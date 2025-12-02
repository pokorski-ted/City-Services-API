from flask import Flask, jsonify, request
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

import json
import hashlib
import strawberry
from typing import List, Optional
from strawberry.flask.views import GraphQLView


def make_etag(obj) -> str:
    """Generate a simple ETag from a Python object and hash it please."""
    raw = json.dumps(obj, sort_keys=True).encode("utf-8")
    return '"' + hashlib.md5(raw).hexdigest() + '"'


# simple in-memory store
city_services = []
next_id = 1

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
    return jsonify(city_services), 200


@app.route('/api/v1/city_services/<string:service_name>', methods=['GET'])
def get_service(service_name):
    try:
        # Validate input
        if not service_name or not isinstance(service_name, str):
            return jsonify({"error": "Invalid service name"}), 400

        
        service = None
        for s in city_services:
            if s.get("name") == service_name:
                service = s
                break

        # Not found
        if not service:
            return jsonify({'error': 'Service not found'}), 404

        # Generate ETag from the service object
        etag = make_etag(service)

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
        response = jsonify(service)
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

        global next_id
        services = {
            'id': next_id,
            'name': data.get('name'),
            'type': data.get('type')
        }

        city_services.append(services)
        next_id += 1

        # WEBSOCKET BROADCAST HERE ---
        try:
            message = json.dumps({
                "event": "service.created",
                "data": services
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

        return jsonify(services), 201

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

    except Exception as e:
        print("create_service error:", repr(e))
        return jsonify({"error": "Internal server error"}), 500


@app.route('/api/v1/city_services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    try:
        data = request.get_json(force=False, silent=True) or {}

        for service in city_services:
            if service['id'] == service_id:
                # update only provided fields
                for k in ('name', 'type'):
                    if k in data:
                        service[k] = data[k]
                return jsonify(service), 200

        
        return jsonify({'error': 'Service not found'}), 404

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

    except Exception as e:
        print("update_service error:", repr(e))
        return jsonify({"error": "Internal Error"}), 500


@app.route('/api/v1/city_services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    try:
        for service in city_services:
            if service['id'] == service_id:
                city_services.remove(service)
                return '', 204

        return jsonify({'error': 'Service not found'}), 404

    except Exception as e:
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
        return [dict_to_service(s) for s in city_services]

    @strawberry.field
    def service(self, id: int) -> Optional[Service]:
        for s in city_services:
            if s["id"] == id:
                return dict_to_service(s)
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
