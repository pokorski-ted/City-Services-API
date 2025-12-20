# tests/test_products_api.py
# Purpose:
# High-level API tests (HTTP in/out) similar to "controller smoke tests" in C#.
# These test your FastAPI routes + DI + DB integration.

def test_get_products_returns_list(client):
    # GET should return an empty list on a fresh test DB
    res = client.get("/products")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_post_product_creates_product(client):
    # POST creates a new product record in SQLite
    res = client.post("/products", json={"name": "Mango"})
    assert res.status_code in (200, 201)

    body = res.json()
    assert "id" in body
    assert body["name"] == "Mango"


def test_put_product_updates_product(client):
    # Arrange: create a product first
    created = client.post("/products", json={"name": "Apple"}).json()
    pid = created["id"]

    # Act: update via PUT
    res = client.put(f"/products/{pid}", json={"name": "Apple Updated"})
    assert res.status_code == 200
    assert res.json()["name"] == "Apple Updated"


def test_delete_product_deletes_product(client):
    # Arrange: create a product
    created = client.post("/products", json={"name": "ToDelete"}).json()
    pid = created["id"]

    # Act: delete it
    res = client.delete(f"/products/{pid}")
    assert res.status_code == 200
    assert "message" in res.json()

    # Assert: product should no longer be available
    res2 = client.get(f"/products/{pid}")
    assert res2.status_code == 404


def test_put_nonexistent_returns_404(client):
    # Updating something that doesn't exist should return 404
    res = client.put("/products/9999", json={"name": "DoesNotExist"})
    assert res.status_code == 404


def test_post_invalid_name_returns_422(client):
    # Name too short (min_length=2) should return validation error (422)
    res = client.post("/products", json={"name": "A"})
    assert res.status_code == 422
