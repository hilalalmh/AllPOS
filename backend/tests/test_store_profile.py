import pytest

OWNER_PASSWORD = "admin123"
KASIR_PASSWORD = "kasir123"


def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _headers(client, username, password):
    return _login(client, username, password)


def test_get_store_profile_default(client):
    resp = client.get(
        "/api/v1/store-profile", headers=_headers(client, "owner", OWNER_PASSWORD)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["store_name"] == "SISTEM POS"
    assert data["footer"] == "TERIMA KASIH ~ SILAHKAN DATANG KEMBALI"
    assert data["id"] == 1


def test_get_store_profile_requires_auth(client):
    resp = client.get("/api/v1/store-profile")
    assert resp.status_code == 401


def test_update_store_profile_owner(client):
    resp = client.put(
        "/api/v1/store-profile",
        json={
            "store_name": "Kedai Kopi Tetangga",
            "address": "Jl. Melati No. 12, Bandung",
            "phone": "081234567890",
            "footer": "TERIMA KASIH ~ MAMPIR LAGI YA!",
        },
        headers=_headers(client, "owner", OWNER_PASSWORD),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["store_name"] == "Kedai Kopi Tetangga"


def test_update_store_profile_persists(client):
    client.put(
        "/api/v1/store-profile",
        json={"store_name": "Aroma Kopi"},
        headers=_headers(client, "owner", OWNER_PASSWORD),
    )
    resp = client.get(
        "/api/v1/store-profile", headers=_headers(client, "owner", OWNER_PASSWORD)
    )
    assert resp.status_code == 200
    assert resp.json()["store_name"] == "Aroma Kopi"


def test_update_store_profile_forbidden_for_kasir(client):
    resp = client.put(
        "/api/v1/store-profile",
        json={"store_name": "HACK"},
        headers=_headers(client, "kasir1", KASIR_PASSWORD),
    )
    assert resp.status_code == 403


def test_update_store_profile_partial(client):
    resp = client.put(
        "/api/v1/store-profile",
        json={"phone": "0812-3456-7890"},
        headers=_headers(client, "owner", OWNER_PASSWORD),
    )
    assert resp.status_code == 200
    assert resp.json()["phone"] == "0812-3456-7890"


def test_update_store_profile_validation(client):
    resp = client.put(
        "/api/v1/store-profile",
        json={"store_name": ""},
        headers=_headers(client, "owner", OWNER_PASSWORD),
    )
    assert resp.status_code == 422


def test_update_store_profile_null_rejected(client):
    """Kiriman null tidak boleh memicu 500 — harus 422 di validasi."""
    for payload in ({"store_name": None}, {"footer": None}):
        resp = client.put(
            "/api/v1/store-profile",
            json=payload,
            headers=_headers(client, "owner", OWNER_PASSWORD),
        )
        assert resp.status_code == 422
