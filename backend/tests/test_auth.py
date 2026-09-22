import pytest


@pytest.fixture
def login_payload():
    return {"username": "owner", "password": "admin123"}


def test_login_success(client, login_payload):
    res = client.post("/api/v1/auth/login", json=login_payload)
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["expires_in"] > 0


def test_login_wrong_password(client):
    res = client.post(
        "/api/v1/auth/login", json={"username": "owner", "password": "wrong"}
    )
    assert res.status_code == 401
    assert "salah" in res.json()["detail"]


def test_login_unknown_user(client):
    res = client.post(
        "/api/v1/auth/login", json={"username": "ghost", "password": "x"}
    )
    assert res.status_code == 401


def test_login_missing_fields(client):
    res = client.post("/api/v1/auth/login", json={})
    assert res.status_code == 422


def test_me_with_token(client, login_payload):
    login = client.post("/api/v1/auth/login", json=login_payload).json()
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["username"] == "owner"
    assert body["role"] == "OWNER"
    assert body["is_active"] is True


def test_me_without_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_invalid_token(client):
    res = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert res.status_code == 401


def test_refresh_flow(client, login_payload):
    login = client.post("/api/v1/auth/login", json=login_payload).json()
    res = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_invalid_token(client):
    res = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "garbage"}
    )
    assert res.status_code == 401