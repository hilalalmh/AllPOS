def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_users_requires_auth(client):
    res = client.get("/api/v1/users")
    assert res.status_code == 401


def test_users_requires_owner(client):
    res = client.get(
        "/api/v1/users", headers=_login(client, "kasir1", "kasir123")
    )
    assert res.status_code == 403


def test_create_user_and_list(client):
    headers = _login(client, "owner", "admin123")
    res = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "kasir_baru",
            "password": "rahasia123",
            "full_name": "Kasir Baru",
            "role": "KASIR",
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["username"] == "kasir_baru"
    assert body["role"] == "KASIR"
    assert body["is_active"] is True

    res = client.get("/api/v1/users?q=kasir_baru", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1
    assert res.json()["items"][0]["username"] == "kasir_baru"


def test_create_user_duplicate_username(client):
    headers = _login(client, "owner", "admin123")
    res = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "kasir1",
            "password": "rahasia123",
            "full_name": "Duplikat",
            "role": "KASIR",
        },
    )
    assert res.status_code == 409


def test_create_user_invalid_username(client):
    headers = _login(client, "owner", "admin123")
    res = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "bad username!",
            "password": "rahasia123",
            "full_name": "Bad",
            "role": "KASIR",
        },
    )
    assert res.status_code == 422


def test_create_user_password_over_72_bytes_rejected(client):
    headers = _login(client, "owner", "admin123")
    # 73 karakter ASCII = 73 byte > batas bcrypt 72 byte.
    long_password = "a" * 73
    res = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "username": "kasir_panjang",
            "password": long_password,
            "full_name": "Panjang",
            "role": "KASIR",
        },
    )
    assert res.status_code == 422
    assert "72 byte" in res.text


def test_update_user_password_over_72_bytes_rejected(client):
    headers = _login(client, "owner", "admin123")
    users = client.get("/api/v1/users?q=kasir2", headers=headers).json()
    user_id = users["items"][0]["id"]

    res = client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"password": "b" * 73},
    )
    assert res.status_code == 422


def test_change_own_password_over_72_bytes_rejected(client):
    headers = _login(client, "kasir1", "kasir123")
    res = client.put(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "kasir123", "new_password": "c" * 73},
    )
    assert res.status_code == 422


def test_update_user_deactivate_and_role(client):
    headers = _login(client, "owner", "admin123")
    users = client.get("/api/v1/users?q=kasir2", headers=headers).json()
    user_id = users["items"][0]["id"]

    res = client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"is_active": False},
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    res = client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"role": "OWNER", "is_active": True},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "OWNER"


def test_cannot_deactivate_self(client):
    headers = _login(client, "owner", "admin123")
    me = client.get("/api/v1/auth/me", headers=headers).json()

    res = client.put(
        f"/api/v1/users/{me['id']}",
        headers=headers,
        json={"is_active": False},
    )
    assert res.status_code == 400


def test_cannot_demote_self(client):
    headers = _login(client, "owner", "admin123")
    me = client.get("/api/v1/auth/me", headers=headers).json()

    res = client.put(
        f"/api/v1/users/{me['id']}",
        headers=headers,
        json={"role": "KASIR"},
    )
    assert res.status_code == 400


def test_update_nonexistent_user(client):
    headers = _login(client, "owner", "admin123")
    res = client.put(
        "/api/v1/users/99999", headers=headers, json={"full_name": "X"}
    )
    assert res.status_code == 404


def test_reset_password_allows_login(client):
    headers = _login(client, "owner", "admin123")
    users = client.get("/api/v1/users?q=kasir2", headers=headers).json()
    user_id = users["items"][0]["id"]

    res = client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"password": "baru1234"},
    )
    assert res.status_code == 200

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "kasir2", "password": "baru1234"},
    )
    assert res.status_code == 200

    # Pulihkan password agar test lain tidak terganggu.
    client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json={"password": "kasir123"},
    )


def test_change_own_password(client):
    headers = _login(client, "kasir1", "kasir123")
    res = client.put(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "kasir123", "new_password": "ganti123"},
    )
    assert res.status_code == 200

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "kasir1", "password": "ganti123"},
    )
    assert res.status_code == 200

    # Pulihkan password kasir1 agar test lain tidak terganggu.
    client.put(
        "/api/v1/users/me/password",
        headers=_login(client, "kasir1", "ganti123"),
        json={"current_password": "ganti123", "new_password": "kasir123"},
    )


def test_change_own_password_wrong_current(client):
    headers = _login(client, "kasir1", "kasir123")
    res = client.put(
        "/api/v1/users/me/password",
        headers=headers,
        json={"current_password": "salah", "new_password": "ganti123"},
    )
    assert res.status_code == 400