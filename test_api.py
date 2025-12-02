import json
import pytest
from api import app
from db import db, ServiceModel


@pytest.fixture(autouse=True)
def setup_database():
    """Reset database before each test using in-memory SQLite."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


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


def test_update_service():
    client = app.test_client()

    # create a service first
    resp_create = client.post(
        "/api/v1/city_services",
        json={"name": "Water", "type": "Utility"}
    )
    created = resp_create.get_json()
    service_id = created["id"]

    # update the service
    resp = client.put(
        f"/api/v1/city_services/{service_id}",
        json={"type": "Essential Utility"}
    )
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["id"] == service_id
    assert data["name"] == "Water"
    assert data["type"] == "Essential Utility"


def test_update_service_not_found():
    client = app.test_client()

    resp = client.put(
        "/api/v1/city_services/999",
        json={"type": "Updated"}
    )
    assert resp.status_code == 404


def test_delete_service():
    client = app.test_client()

    # create a service first
    resp_create = client.post(
        "/api/v1/city_services",
        json={"name": "Water", "type": "Utility"}
    )
    created = resp_create.get_json()
    service_id = created["id"]

    # delete the service
    resp = client.delete(f"/api/v1/city_services/{service_id}")
    assert resp.status_code == 204

    # verify it's deleted
    resp_list = client.get("/api/v1/city_services")
    data = resp_list.get_json()
    assert len(data) == 0


def test_delete_service_not_found():
    client = app.test_client()

    resp = client.delete("/api/v1/city_services/999")
    assert resp.status_code == 404
