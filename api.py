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
    try:
        # Validate input
        if not service_name or not isinstance(service_name, str):
            return jsonify({"error": "Invalid service name"}), 400
        
            for service in city_services:
                if service['name'] == service_name:
                    return jsonify(service), 200 
                
            #not found
            return jsonify({'error': 'Service not found'}), 404
        
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
    

if __name__ == '__main__':
    app.run(debug=True)
