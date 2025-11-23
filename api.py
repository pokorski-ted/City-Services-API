from flask import Flask, jsonify, request

app = Flask(__name__)

# simple in-memory store
city_services = []
next_id = 1

@app.route('/city_services', methods=['GET'])
def get_services():
    return jsonify(city_services)

@app.route('/city_services/<string:service_name>', methods=['GET'])
def get_service(service_name):
    for service in city_services:
        if service['name'] == service_name:
            return jsonify(service)
    return jsonify({'error': 'Service not found'}), 404

@app.route('/city_services', methods=['POST'])
def create_service():
    global next_id
    data = request.get_json() or {}
    if not data.get('name'):
        return jsonify({'error': 'Service name required'}), 400
    services = {
        'id': next_id,
        'name': data.get('name'),
        'type': data.get('type')
    }
    city_services.append(services)
    next_id += 1
    return jsonify(services), 201

@app.route('/city_services/<int:service_id>', methods=['PUT'])
def update_service(service_id):
    data = request.get_json() or {}
    for service in city_services:
        if service['id'] == service_id:
            # update only provided fields
            for k in ('name', 'type'):
                if k in data:
                    service[k] = data[k]
            return jsonify(service)
    return jsonify({'error': 'Service not found'}), 404

@app.route('/city_services/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    for service in city_services:
        if service['id'] == service_id:
            city_services.remove(service)
            return '', 204
    return jsonify({'error': 'Service not found'}), 404

if __name__ == '__main__':
    app.run(debug=True)
