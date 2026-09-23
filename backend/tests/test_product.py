import pytest


def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_headers(client):
    return _login(client, "owner", "admin123")


@pytest.fixture
def kasir_headers(client):
    return _login(client, "kasir1", "kasir123")


# ---------- Categories ----------


def test_create_category(client, owner_headers):
    res = client.post(
        "/api/v1/categories", json={"name": "Snack"}, headers=owner_headers
    )
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Snack"
    assert body["is_active"] is True


def test_create_category_duplicate(client, owner_headers):
    client.post("/api/v1/categories", json={"name": "Dup"}, headers=owner_headers)
    res = client.post(
        "/api/v1/categories", json={"name": "Dup"}, headers=owner_headers
    )
    assert res.status_code == 409


def test_update_category(client, owner_headers):
    created = client.post(
        "/api/v1/categories", json={"name": "Rename me"}, headers=owner_headers
    ).json()
    res = client.put(
        f"/api/v1/categories/{created['id']}",
        json={"name": "Renamed"},
        headers=owner_headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Renamed"


def test_update_category_null_not_nullable_rejected(client, owner_headers):
    created = client.post(
        "/api/v1/categories", json={"name": "Null me"}, headers=owner_headers
    ).json()
    res = client.put(
        f"/api/v1/categories/{created['id']}",
        json={"name": None},
        headers=owner_headers,
    )
    assert res.status_code == 422


def test_delete_category_empty(client, owner_headers):
    created = client.post(
        "/api/v1/categories", json={"name": "ToDelete"}, headers=owner_headers
    ).json()
    res = client.delete(
        f"/api/v1/categories/{created['id']}", headers=owner_headers
    )
    assert res.status_code == 204


def test_category_requires_owner(client, kasir_headers):
    res = client.post(
        "/api/v1/categories", json={"name": "Nope"}, headers=kasir_headers
    )
    assert res.status_code == 403


# ---------- Products ----------


def _make_product(
    client,
    headers,
    *,
    category_id=1,
    name="Es Kopi",
    sku="ESKOPI",
    price="18000",
    **extra,
):
    data = {
        "category_id": str(category_id),
        "name": name,
        "sku": sku,
        "price": price,
    }
    data.update({k: str(v) for k, v in extra.items()})
    return client.post("/api/v1/products", data=data, headers=headers)


def test_create_product(client, owner_headers):
    res = _make_product(client, owner_headers, name="Cappuccino", sku="CAP")
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Cappuccino"
    assert body["price"] == 18000.0
    assert body["category_id"] == 1


def test_create_product_duplicate_sku(client, owner_headers):
    _make_product(client, owner_headers, name="A", sku="DUP")
    res = _make_product(client, owner_headers, name="B", sku="DUP")
    assert res.status_code == 409
    assert "SKU" in res.json()["detail"]


def test_create_product_invalid_category(client, owner_headers):
    res = _make_product(client, owner_headers, category_id=99999)
    assert res.status_code == 404


def test_create_product_zero_price(client, owner_headers):
    res = _make_product(client, owner_headers, price="0")
    assert res.status_code == 422


def test_create_product_requires_owner(client, kasir_headers):
    res = _make_product(client, kasir_headers, sku="KASIRPROD")
    assert res.status_code == 403


def test_list_products_pagination(client, owner_headers):
    _make_product(client, owner_headers, name="Latte", sku="LATTE")
    _make_product(client, owner_headers, name="Macchiato", sku="MACH")
    res = client.get("/api/v1/products?page=1&page_size=2", headers=owner_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["items"]) <= 2
    assert body["total"] >= 2
    assert body["page"] == 1
    assert body["page_size"] == 2


def test_search_products(client, owner_headers):
    _make_product(client, owner_headers, name="Matcha Latte", sku="MTCHL")
    res = client.get("/api/v1/products?q=matcha", headers=owner_headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1
    assert all("matcha" in p["name"].lower() for p in res.json()["items"])


def test_get_product(client, owner_headers):
    created = _make_product(client, owner_headers, name="Cold Brew", sku="CB")
    pid = created.json()["id"]
    res = client.get(f"/api/v1/products/{pid}", headers=owner_headers)
    assert res.status_code == 200
    assert res.json()["name"] == "Cold Brew"


def test_update_product(client, owner_headers):
    created = _make_product(client, owner_headers, name="X", sku="XX")
    pid = created.json()["id"]
    res = client.put(
        f"/api/v1/products/{pid}",
        json={"price": 25000, "description": "desc"},
        headers=owner_headers,
    )
    assert res.status_code == 200
    body = res.json()
    assert body["price"] == 25000.0
    assert body["description"] == "desc"


def test_update_product_null_not_nullable_rejected(client, owner_headers):
    created = _make_product(client, owner_headers, name="Y", sku="YY")
    pid = created.json()["id"]
    # Pydantic mengizinkan None karena field optional; kolom NOT NULL tidak
    # boleh di-null → 422, bukan 500 IntegrityError.
    res = client.put(
        f"/api/v1/products/{pid}",
        json={"name": None},
        headers=owner_headers,
    )
    assert res.status_code == 422
    res = client.put(
        f"/api/v1/products/{pid}",
        json={"price": None},
        headers=owner_headers,
    )
    assert res.status_code == 422


def test_delete_product_soft(client, owner_headers):
    created = _make_product(client, owner_headers, name="Temporary", sku="TMP")
    pid = created.json()["id"]
    res = client.delete(f"/api/v1/products/{pid}", headers=owner_headers)
    assert res.status_code == 204
    listed = client.get(
        "/api/v1/products?q=TMP", headers=owner_headers
    ).json()
    assert listed["total"] == 0


def test_products_require_auth(client):
    res = client.get("/api/v1/products")
    assert res.status_code == 401


def test_upload_non_image_rejected(client, owner_headers):
    res = client.post(
        "/api/v1/products",
        data={
            "category_id": "1",
            "name": "Bad Image",
            "sku": "BADIMG",
            "price": "1000",
        },
        files={"image": ("fake.txt", b"hello", "text/plain")},
        headers=owner_headers,
    )
    assert res.status_code == 400
    assert "Format gambar" in res.json()["detail"]


def test_upload_spoofed_mime_rejected(client, owner_headers):
    """content_type dipalsukan PNG tapi isi bukan gambar → tolak magic-byte."""
    res = client.post(
        "/api/v1/products",
        data={
            "category_id": "1",
            "name": "Spoof",
            "sku": "SPOOF",
            "price": "1000",
        },
        files={"image": ("spoof.png", b"<html>not-an-image</html>", "image/png")},
        headers=owner_headers,
    )
    assert res.status_code == 400
    assert "tidak cocok" in res.json()["detail"]


def test_upload_real_png_accepted(client, owner_headers):
    """PNG 1x1 asli dengan magic byte valid tetap diterima."""
    png = (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDAT"
        b"\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x05\x02\x00\x11\xb6\x11"
        b"\x1c\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    res = client.post(
        "/api/v1/products",
        data={
            "category_id": "1",
            "name": "PNG Ok",
            "sku": "PNGOK",
            "price": "1000",
        },
        files={"image": ("ok.png", png, "image/png")},
        headers=owner_headers,
    )
    assert res.status_code == 201
    assert res.json()["image_url"].startswith("/uploads/")