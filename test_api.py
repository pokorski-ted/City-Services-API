import json
from api import app, city_services  # adjust 'app' filename if needed


def setup_function(_):
    # reset in-memory store before each test
    city_services.clear()


def test_create_service():
    client = app.test_client()

    resp = client.post(
        "/api/v1/city_services",
        json={"name": "Water", "type": "Utility"}
    )
    assert resp.status_code == 201

    data = resp.get_json()
    assert data["name"] == "Water"
    assert data["type"] == "Utility"
    assert "id" in data


def test_list_services():
    client = app.test_client()

    # create one service first
    client.post("/api/v1/city_services", json={"name": "Water", "type": "Utility"})

    resp = client.get("/api/v1/city_services")
    assert resp.status_code == 200

    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Water"


def test_get_service_with_etag_and_304():
    client = app.test_client()

    # create service
    client.post("/api/v1/city_services", json={"name": "Water", "type": "Utility"})

    # first GET to obtain ETag
    resp1 = client.get("/api/v1/city_services/Water")
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # second GET with If-None-Match
    resp2 = client.get(
        "/api/v1/city_services/Water",
        headers={"If-None-Match": etag}
    )
    assert resp2.status_code == 304
    # no body expected on 304
    assert not resp2.data


def test_graphql_services_query():
    client = app.test_client()

    # create a service via REST
    client.post("/api/v1/city_services", json={"name": "Water", "type": "Utility"})

    query = """
    {
      services {
        id
        name
        type
      }
    }
    """

    resp = client.post(
        "/api/v1/graphql",
        json={"query": query}
    )
    assert resp.status_code == 200

    data = resp.get_json()
    assert "data" in data
    services = data["data"]["services"]
    assert len(services) == 1
    assert services[0]["name"] == "Water"


def test_graphql_service_by_id():
    client = app.test_client()

    # create a service
    resp_create = client.post(
        "/api/v1/city_services",
        json={"name": "Water", "type": "Utility"}
    )
    created = resp_create.get_json()
    service_id = created["id"]

    query = f"""
    {{
      service(id: {service_id}) {{
        id
        name
        type
      }}
    }}
    """

    resp = client.post(
        "/api/v1/graphql",
        json={"query": query}
    )
    assert resp.status_code == 200

    data = resp.get_json()
    svc = data["data"]["service"]
    assert svc["id"] == service_id
    assert svc["name"] == "Water"
    assert svc["type"] == "Utility"
