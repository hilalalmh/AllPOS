def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_audit_requires_auth(client):
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 401


def test_audit_requires_owner(client):
    headers = _login(client, "kasir1", "kasir123")
    res = client.get("/api/v1/audit-logs", headers=headers)
    assert res.status_code == 403


def test_login_is_audited(client):
    headers = _login(client, "owner", "admin123")
    res = client.get("/api/v1/audit-logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    actions = {item["action"] for item in data["items"]}
    assert "auth.login" in actions
    login_log = next(
        item for item in data["items"] if item["action"] == "auth.login"
    )
    assert login_log["username"] == "owner"
    assert login_log["entity_type"] == "user"


def test_product_create_is_audited(client):
    owner = _login(client, "owner", "admin123")
    res = client.post(
        "/api/v1/categories",
        json={"name": "Audit Test Cat", "is_active": True},
        headers=owner,
    )
    assert res.status_code == 201
    category_id = res.json()["id"]

    res = client.post(
        "/api/v1/products",
        data={
            "category_id": str(category_id),
            "name": "Audit Kopi",
            "sku": "AUDIT-001",
            "price": "15000",
        },
        headers=owner,
    )
    assert res.status_code == 201
    product_id = res.json()["id"]

    logs = client.get(
        "/api/v1/audit-logs",
        headers=owner,
        params={"entity_type": "product", "action": "product.create"},
    ).json()
    assert logs["total"] >= 1
    assert any(item["entity_id"] == product_id for item in logs["items"])


def test_filter_and_pagination(client):
    owner = _login(client, "owner", "admin123")
    logs = client.get(
        "/api/v1/audit-logs",
        headers=owner,
        params={"page": 1, "page_size": 5, "q": "auth"},
    ).json()
    assert logs["page"] == 1
    assert logs["page_size"] == 5
    assert logs["total"] >= 1
    assert all("auth" in item["action"] for item in logs["items"])