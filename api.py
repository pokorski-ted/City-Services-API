from flask import Flask, jsonify, request
from flask_sock import Sock

import json
import hashlib
import os
import strawberry
from typing import List, Optional
from strawberry.flask.views import GraphQLView

from db import db, ServiceModel, init_db

app = Flask(__name__)
sock = Sock(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///city_services.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)


def make_etag(obj) -> str:
    """Generate a simple ETag from a Python object and hash it please."""
    raw = json.dumps(obj, sort_keys=True).encode("utf-8")
    return '"' + hashlib.md5(raw).hexdigest() + '"'

# track connected WebSocket clients
ws_clients = []


# WebSocket endpoint
@sock.route('/ws/services')
def services_ws(ws):
    ws_clients.append(ws)
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)


# ---------------- REST ENDPOINTS ----------------

@app.route('/api/v1/city_services', methods=['GET'])
def get_services():
    services = ServiceModel.query.all()
    return jsonify([s.to_dict() for s in services]), 200


@app.route('/api/v1/city_services/<string:service_name>', methods=['GET'])
def get_service(service_name):
    try:
        # Validate input
        if not service_name or not isinstance(service_name, str):
            return jsonify({"error": "Invalid service name"}), 400

        service = ServiceModel.query.filter_by(name=service_name).first()

        # Not found
        if not service:
            return jsonify({'error': 'Service not found'}), 404

        service_dict = service.to_dict()

        # Generate ETag from the service object
        etag = make_etag(service_dict)

        # Read client's conditional header, if any
        client_etag = request.headers.get("If-None-Match")

        # Common caching headers
        headers = {
            "ETag": etag,
            "Cache-Control": "max-age=60"  # cache for 60 seconds
        }

        # If the client's ETag matches, return 304 Not Modified
        if client_etag == etag:
            return ("", 304, headers)

        # Otherwise return full resource
        response = jsonify(service_dict)
        for k, v in headers.items():
            response.headers[k] = v
        return response, 200

    except KeyError as e:
        return jsonify({"error": f"missing field: {str(e)}"}), 400

    except Exception:
        return jsonify({"error": "Internal error"}), 500


@app.route('/api/v1/city_services', methods=['POST'])
def create_service():
    try:
        data = request.get_json(force=False, silent=True) or {}
        if not data.get('name'):
            return jsonify({'error': 'Service name required'}), 400

        service = ServiceModel(
            name=data.get('name'),
            type=data.get('type')
        )
        db.session.add(service)
        db.session.commit()

        service_dict = service.to_dict()

        # WEBSOCKET BROADCAST HERE ---
        try:
            message = json.dumps({
                "event": "service.created",
                "data": service_dict
            })
            for ws in list(ws_clients):
                try:
                    ws.send(message)
                except Exception:
                    if ws in ws_clients:
                        ws_clients.remove(ws)
        except Exception as e:
            # optional: print or log, but don't fail the request because of WS
            print("WebSocket broadcast error:", repr(e))
        # END WEBSOCKET PART ---

        return jsonify(service_dict), 201

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

    except Exception as e:
        db.session.rollback()
        print("create_service error:", repr(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/city_services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    try:
        data = request.get_json(force=False, silent=True) or {}

        service = db.session.get(ServiceModel, service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404

        # update only provided fields
        if 'name' in data:
            service.name = data['name']
        if 'type' in data:
            service.type = data['type']

        db.session.commit()
        return jsonify(service.to_dict()), 200

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

    except Exception as e:
        db.session.rollback()
        print("update_service error:", repr(e))
        return jsonify({"error": "Internal Error"}), 500


@app.route('/api/v1/city_services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    try:
        service = db.session.get(ServiceModel, service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404

        db.session.delete(service)
        db.session.commit()
        return '', 204

    except Exception as e:
        db.session.rollback()
        print("delete_service error:", repr(e))
        return jsonify({"error": "Internal Error"}), 500


# ---------------- GRAPHQL ----------------

@strawberry.type
class Service:
    id: int
    name: str
    type: Optional[str]


def dict_to_service(d: dict) -> Service:
    return Service(
        id=d["id"],
        name=d["name"],
        type=d.get("type")
    )


@strawberry.type
class Query:
    @strawberry.field
    def services(self) -> List[Service]:
        all_services = ServiceModel.query.all()
        return [dict_to_service(s.to_dict()) for s in all_services]

    @strawberry.field
    def service(self, id: int) -> Optional[Service]:
        s = db.session.get(ServiceModel, id)
        if s:
            return dict_to_service(s.to_dict())
        return None


schema = strawberry.Schema(query=Query)

app.add_url_rule(
    "/api/v1/graphql",
    view_func=GraphQLView.as_view(
        "graphql_view",
        schema=schema,
        graphiql=True  # enables the nice web UI
    )
)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
