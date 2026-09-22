from datetime import date


def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create(client, headers, payload):
    return client.post(
        "/api/v1/transactions", json=payload, headers=headers
    )


def _summary(client, headers, **params):
    res = client.get(
        "/api/v1/dashboard/summary",
        headers=headers,
        params=params or None,
    )
    assert res.status_code == 200
    return res.json()


def _best(client, headers, **params):
    res = client.get(
        "/api/v1/dashboard/best-sellers",
        headers=headers,
        params=params or None,
    )
    assert res.status_code == 200
    return res.json()["items"]


def _qty_best(client, headers, product_name):
    for item in _best(client, headers, limit=50):
        if item["product_name"] == product_name:
            return item["quantity"]
    return 0


CASH_ESKOPI = {
    "items": [{"product_id": 1, "quantity": 2, "note": None}],
    "payment_method": "CASH",
    "paid_amount": 50000,
    "discount": 0,
}


def test_dashboard_requires_owner(client):
    headers = _login(client, "kasir1", "kasir123")
    res = client.get("/api/v1/dashboard/summary", headers=headers)
    assert res.status_code == 403


def test_dashboard_requires_auth(client):
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 401


def test_dashboard_summary_reflects_transactions(client):
    owner = _login(client, "owner", "admin123")
    before = _summary(client, owner, start_date=str(date.today()), end_date=str(date.today()))
    before_best = _qty_best(client, owner, "Es Kopi")

    _create(client, owner, CASH_ESKOPI)

    after = _summary(client, owner, start_date=str(date.today()), end_date=str(date.today()))
    after_best = _qty_best(client, owner, "Es Kopi")

    assert after["transaction_count"] == before["transaction_count"] + 1
    assert after["sales_total"] == before["sales_total"] + 36000.0
    assert after["item_count"] == before["item_count"] + 2
    assert after["active_products"] > 0
    assert after["best_seller"]["product_name"] == "Es Kopi"
    assert after_best == before_best + 2


def test_dashboard_summary_excludes_cancelled(client):
    owner = _login(client, "owner", "admin123")
    before = _summary(client, owner, start_date=str(date.today()), end_date=str(date.today()))
    created = _create(client, owner, CASH_ESKOPI).json()
    client.post(
        f"/api/v1/transactions/{created['id']}/cancel", headers=owner
    )
    after = _summary(client, owner, start_date=str(date.today()), end_date=str(date.today()))
    assert after["transaction_count"] == before["transaction_count"]
    assert after["sales_total"] == before["sales_total"]


def test_sales_series_group_day(client):
    owner = _login(client, "owner", "admin123")
    today = str(date.today())

    def _row():
        res = client.get(
            "/api/v1/dashboard/sales",
            headers=owner,
            params={"start_date": today, "end_date": today, "group_by": "day"},
        )
        assert res.status_code == 200
        rows = res.json()
        assert len(rows) <= 1
        if len(rows) == 0:
            return {"period": today, "transaction_count": 0, "sales_total": 0.0}
        return rows[0]

    before = _row()
    _create(client, owner, CASH_ESKOPI)
    after = _row()

    assert after["period"] == today
    assert after["transaction_count"] == before["transaction_count"] + 1
    assert after["sales_total"] == before["sales_total"] + 36000.0


def test_sales_series_invalid_group_by(client):
    owner = _login(client, "owner", "admin123")
    res = client.get(
        "/api/v1/dashboard/sales",
        headers=owner,
        params={"group_by": "hour"},
    )
    assert res.status_code == 422


def test_best_sellers_ranking(client):
    owner = _login(client, "owner", "admin123")
    before_qty = _qty_best(client, owner, "Es Kopi")

    _create(client, owner, CASH_ESKOPI)

    items = _best(client, owner, limit=50)
    es_kopi = next(
        (i for i in items if i["product_name"] == "Es Kopi"), None
    )
    assert es_kopi is not None
    assert es_kopi["quantity"] == before_qty + 2
    assert es_kopi["revenue"] >= 36000.0


def test_best_sellers_empty_range(client):
    owner = _login(client, "owner", "admin123")
    res = client.get(
        "/api/v1/dashboard/best-sellers",
        headers=owner,
        params={"start_date": "2000-01-01", "end_date": "2000-01-02"},
    )
    assert res.status_code == 200
    assert res.json()["items"] == []