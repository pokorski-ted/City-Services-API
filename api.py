from flask import Flask, jsonify, request
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

import json
import hashlib

# move this to a seperate py file ---
import strawberry
from typing import List, Optional

# city_services comes from your main file
# but Strawberry needs to reference it directly

@strawberry.type
class Service:
    id: int
    name: str
    type: Optional[str]

def dict_to_service(d):
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
#----

def make_etag(obj) -> str:
    """Generate a simple ETag from a Python object and HASH it."""
    raw = json.dumps(obj, sort_keys=True).encode("utf-8")
    return '"' + hashlib.md5(raw).hexdigest() + '"'


# simple in-memory store
city_services = []
next_id = 1

# track connected WebSocket clients
ws_clients = []

# keep track of connected clients; broadcast a JSON message whenever a new service is created
@sock.route('/ws/services')
def services_ws(ws):
    # Add client to list
    ws_clients.append(ws)
    try:
        # Keep the connection open
        while True:
            # We don't really care what client sends; just block waiting
            msg = ws.receive()
            if msg is None:
                break
    finally:
        # Ensure client is removed on disconnect
        if ws in ws_clients:
            ws_clients.remove(ws)


@app.route('/city_services', methods=['GET'])
def get_services():
    return jsonify(city_services)

@app.route('/city_services/<string:service_name>', methods=['GET'])
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

            #not found
            if not service:
                return jsonify({'error': 'Service not found'}), 404
        
            # Generate ETag from the service object
            etag = make_etag(service)

            # Read client's conditional header, if any
            client_etag = request.headers.get("If-None-Match")

            # Common caching headers
            headers = {
                "ETag": etag,
                "Cache-Control": "max-age=60"  # cache for 60 seconds (demo)
            }

            # If the client's ETag matches, return 304 Not Modified
            if client_etag == etag:
                return ("", 304, headers)
            
            #otherwise return service        
            response = jsonify(service)

            # jsonify already sets Content-Type; we just add headers
            for k, v in headers.items():
                response.headers[k] = v
            return response, 200

    except KeyError as e:
            return jsonify({"error: ": f"missing field: {str(e)}"}), 400
    
    except Exception as e:
            return jsonify({"error: ": "Internal error"}), 500


@app.route('/city_services', methods=['POST'])
def create_service():
    try:
        
        data = request.get_json() or {}
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
        # Prepare JSON message
        message = json.dumps({
            "event": "service.created",
            "data": services
        })

        # Send to all connected WS clients
        # (make a copy of list to avoid modification during iteration)
        for ws in list(ws_clients):
            try:
                ws.send(message)
            except Exception:
                # If a client is dead, drop it
                if ws in ws_clients:
                    ws_clients.remove(ws)
        # END WEBSOCKET PART ---
        # Every time you POST /city_services, all connected WS clients will get a "service.created" event with the new service

        return jsonify(services), 201
    
    except KeyError as e:
        # Missing expected field in the payload
        return jsonify({"error": f"Missing field: {str(e)}"}), 400

    except Exception:
        # Any other unexpected server error
        return jsonify({"error": "Internal server error"}), 500

@app.route('/city_services/<int:service_id>', methods=['PUT'])
def update_service(service_id):

    try:

        data = request.get_json() or {}
        for service in city_services:
            if service['id'] == service_id:
                # update only provided fields
                for k in ('name', 'type'):
                    if k in data:
                        service[k] = data[k]
                return jsonify(service), 200
            
            return jsonify({'error': 'Service not found'}), 404
        
    except KeyError as e:
        return jsonify({"error: ": f"Missing field: {str(e)}"}), 400
    
    except Exception as e:
        return jsonify({"error: ": "Internal Error"}), 500


@app.route('/city_services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):

    try:

        for service in city_services:
            if service['id'] == service_id:
                city_services.remove(service)
                return '', 204
            
        return jsonify({'error': 'Service not found'}), 404

    except Exception as e:
        return jsonify({"error: ": "Internal Error"}, 500)
    
# more GraphQL stuff---
from strawberry.flask.views import GraphQLView

app.add_url_rule(
    "/graphql",
    view_func=GraphQLView.as_view(
        "graphql_view",
        schema=schema,
        graphiql=True  # enables the nice web UI
    )
)
#---


if __name__ == '__main__':
    app.run(debug=True)
