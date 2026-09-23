import re

import pytest


def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture
def owner(client):
    return _login(client, "owner", "admin123")


@pytest.fixture
def kasir1(client):
    return _login(client, "kasir1", "kasir123")


@pytest.fixture
def kasir2(client):
    return _login(client, "kasir2", "kasir123")


def _create(client, headers, payload):
    return client.post(
        "/api/v1/transactions", json=payload, headers=headers
    )


CASH_ESKOPI = {
    "items": [{"product_id": 1, "quantity": 2, "note": None}],
    "payment_method": "CASH",
    "paid_amount": 50000,
    "discount": 0,
}


def test_create_transaction_success(client, kasir1):
    res = _create(client, kasir1, CASH_ESKOPI)
    assert res.status_code == 201
    body = res.json()
    assert re.match(r"^POS-\d{8}-\d{4}$", body["invoice_number"])
    assert body["status"] == "PAID"
    assert body["subtotal"] == 36000.0
    assert body["total"] == 36000.0
    assert body["change_amount"] == 14000.0
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["product_name"] == "Es Kopi"
    assert item["price"] == 18000.0
    assert item["subtotal"] == 36000.0
    assert body["payment"] is not None


def test_invoice_sequential(client, kasir1):
    first = _create(client, kasir1, CASH_ESKOPI).json()
    second = _create(client, kasir1, CASH_ESKOPI).json()
    day = first["invoice_number"].split("-")[1]
    assert first["invoice_number"] == f"POS-{day}-0001"
    assert second["invoice_number"] == f"POS-{day}-0002"


def test_client_cannot_influence_price(client, kasir1):
    payload = {
        **CASH_ESKOPI,
        "items": [
            {"product_id": 1, "quantity": 2, "price": 1, "note": None}
        ],
    }
    res = _create(client, kasir1, payload)
    assert res.status_code == 201
    # Harga tetap dari database (18.000), bukan 1.
    assert res.json()["items"][0]["price"] == 18000.0


def test_payment_insufficient(client, kasir1):
    payload = {
        **CASH_ESKOPI,
        "paid_amount": 1000,
    }
    res = _create(client, kasir1, payload)
    assert res.status_code == 422
    assert "Pembayaran tidak mencukupi" in res.json()["detail"]


def test_discount_exceeds_subtotal(client, kasir1):
    payload = {
        **CASH_ESKOPI,
        "paid_amount": 99999,
        "discount": 40000,
    }
    res = _create(client, kasir1, payload)
    assert res.status_code == 422
    assert "Discount" in res.json()["detail"]


def test_invalid_product(client, kasir1):
    payload = {
        "items": [{"product_id": 99999, "quantity": 1}],
        "payment_method": "CASH",
        "paid_amount": 10000,
    }
    res = _create(client, kasir1, payload)
    assert res.status_code == 422


def test_empty_items(client, kasir1):
    payload = {**CASH_ESKOPI, "items": []}
    res = _create(client, kasir1, payload)
    assert res.status_code == 422


def test_requires_auth(client):
    assert client.get("/api/v1/transactions").status_code == 401


def test_kasir_sees_only_own(client, kasir1, kasir2):
    _create(client, kasir1, CASH_ESKOPI)
    total_k1 = client.get(
        "/api/v1/transactions", headers=kasir1
    ).json()["total"]
    total_k2 = client.get(
        "/api/v1/transactions", headers=kasir2
    ).json()["total"]
    assert total_k1 >= 1
    assert total_k2 == 0


def test_owner_sees_all(client, owner, kasir1):
    _create(client, kasir1, CASH_ESKOPI)
    total = client.get("/api/v1/transactions", headers=owner).json()["total"]
    assert total >= 1


def test_kasir_cannot_access_others_transaction(client, kasir1, kasir2):
    tx = _create(client, kasir1, CASH_ESKOPI).json()
    res = client.get(
        f"/api/v1/transactions/{tx['id']}", headers=kasir2
    )
    assert res.status_code == 403


def test_cancel_transaction(client, owner, kasir1):
    tx = _create(client, kasir1, CASH_ESKOPI).json()
    res = client.post(
        f"/api/v1/transactions/{tx['id']}/cancel", headers=owner
    )
    assert res.status_code == 200
    assert res.json()["status"] == "CANCELLED"
    double = client.post(
        f"/api/v1/transactions/{tx['id']}/cancel", headers=owner
    )
    assert double.status_code == 400


def test_snapshot_preserved_after_price_change(client, owner, kasir1):
    tx = _create(client, kasir1, CASH_ESKOPI).json()
    item_before = tx["items"][0]
    client.put(
        "/api/v1/products/1",
        json={"price": 99999},
        headers=owner,
    )
    detail = client.get(
        f"/api/v1/transactions/{tx['id']}", headers=owner
    ).json()
    item_after = detail["items"][0]
    assert item_before["price"] == item_after["price"] == 18000.0


def test_filter_by_invoice_and_status(client, owner, kasir1):
    _create(client, kasir1, CASH_ESKOPI)
    res = client.get(
        "/api/v1/transactions?q=POS-2026", headers=owner
    )
    assert res.status_code == 200
    assert res.json()["total"] >= 1
    res = client.get(
        "/api/v1/transactions?status=CANCELLED", headers=owner
    )
    assert res.status_code == 200


def test_pagination(client, owner, kasir1):
    for _ in range(3):
        _create(client, kasir1, CASH_ESKOPI)
    res = client.get(
        "/api/v1/transactions?page=1&page_size=2", headers=owner
    )
    body = res.json()
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] >= 3


def test_filter_start_and_end_date(client, owner, kasir1):
    _create(client, kasir1, CASH_ESKOPI)
    res = client.get(
        "/api/v1/transactions",
        headers=owner,
        params={
            "start_date": "2000-01-01",
            "end_date": "9999-12-31",
            "status": "PAID",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert all(item["status"] == "PAID" for item in body["items"])
    assert all(item["created_at"] >= "2000-01-01" for item in body["items"])
    assert all(item["created_at"] <= "9999-12-31" for item in body["items"])


def test_end_date_filter(client, owner, kasir1):
    _create(client, kasir1, CASH_ESKOPI)
    res = client.get(
        "/api/v1/transactions",
        headers=owner,
        params={"end_date": "9999-12-31"},
    )
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_local_ref_idempotent(client, kasir1):
    payload = {**CASH_ESKOPI, "local_ref": "TX-LOCAL-12345"}
    res = _create(client, kasir1, payload)
    assert res.status_code == 201
    first = res.json()

    replay = _create(client, kasir1, payload)
    assert replay.status_code == 201
    second = replay.json()

    assert first["id"] == second["id"]
    assert first["invoice_number"] == second["invoice_number"]
    total_after = client.get(
        "/api/v1/transactions", headers=kasir1
    ).json()["total"]
    assert total_after >= 1


def test_local_ref_conflict_without_ref_creates_separate(client, kasir1):
    _create(client, kasir1, {**CASH_ESKOPI, "local_ref": "TX-LOCAL-67890"})
    other = client.get(
        "/api/v1/transactions", headers=kasir1
    ).json()
    assert other["total"] >= 1


def test_local_ref_replay_denied_for_other_cashier(client, kasir1, kasir2):
    payload = {**CASH_ESKOPI, "local_ref": "TX-LOCAL-OWNED-1"}
    _create(client, kasir1, payload)
    # Kasir lain tidak boleh "menebak" local_ref kasir 1 (enumerasi lintas-kasir).
    res = _create(client, kasir2, payload)
    assert res.status_code == 409


def test_local_ref_replay_conflicts_on_different_items(client, kasir1):
    payload = {**CASH_ESKOPI, "local_ref": "TX-LOCAL-ITEMS-1"}
    _create(client, kasir1, payload)
    # Uang identik (subtotal/discount/total/paid sama) tapi isi keranjang beda
    # (note berbeda) → pemilik yang sama pun harus ditolak (bukan idempoten).
    replay = _create(
        client,
        kasir1,
        {
            **CASH_ESKOPI,
            "local_ref": "TX-LOCAL-ITEMS-1",
            "items": [{"product_id": 1, "quantity": 2, "note": "tambahan"}],
        },
    )
    assert replay.status_code == 409