def _login(client, username, password):
    res = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _create_transaction(client, headers):
    return client.post(
        "/api/v1/transactions",
        json={
            "items": [{"product_id": 1, "quantity": 1, "note": None}],
            "payment_method": "CASH",
            "paid_amount": 20000,
            "discount": 0,
        },
        headers=headers,
    )


def test_report_requires_auth(client):
    res = client.get("/api/v1/reports/transactions.csv")
    assert res.status_code == 401


def test_report_requires_owner(client):
    headers = _login(client, "kasir1", "kasir123")
    res = client.get("/api/v1/reports/transactions.csv", headers=headers)
    assert res.status_code == 403


def test_transactions_csv(client):
    owner = _login(client, "owner", "admin123")
    created = _create_transaction(client, owner)
    assert created.status_code == 201

    res = client.get("/api/v1/reports/transactions.csv", headers=owner)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("text/csv")
    assert "attachment" in res.headers["content-disposition"]
    body = res.text
    assert body.startswith("invoice_number")
    assert created.json()["invoice_number"] in body


def test_transactions_csv_filtered_end_date(client):
    owner = _login(client, "owner", "admin123")
    created = _create_transaction(client, owner)
    assert created.status_code == 201
    res = client.get(
        "/api/v1/reports/transactions.csv",
        headers=owner,
        params={"end_date": "9999-12-31"},
    )
    assert res.status_code == 200
    body = res.text
    assert body.startswith("invoice_number")
    assert created.json()["invoice_number"] in body


def test_transactions_csv_filtered(client):
    owner = _login(client, "owner", "admin123")
    _create_transaction(client, owner)
    res = client.get(
        "/api/v1/reports/transactions.csv",
        headers=owner,
        params={"status": "PAID", "payment_method": "CASH", "start_date": "2000-01-01"},
    )
    assert res.status_code == 200
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("invoice_number")
    assert len(lines) >= 2
    assert "PAID" in lines[1]


def test_transactions_pdf(client):
    owner = _login(client, "owner", "admin123")
    created = _create_transaction(client, owner)
    assert created.status_code == 201

    res = client.get("/api/v1/reports/transactions.pdf", headers=owner)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")

    text = _pdf_decompressed_text(res.content)
    assert "Laporan Transaksi" in text
    assert created.json()["invoice_number"] in text


def test_transactions_pdf_with_end_date(client):
    owner = _login(client, "owner", "admin123")
    created = _create_transaction(client, owner)
    assert created.status_code == 201

    res = client.get(
        "/api/v1/reports/transactions.pdf",
        headers=owner,
        params={"end_date": "9999-12-31"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")
    assert created.json()["invoice_number"] in _pdf_decompressed_text(res.content)


def _pdf_decompressed_text(content: bytes) -> str:
    import base64
    import re
    import zlib

    text = ""
    markers = list(re.finditer(rb"stream\r?\n", content))
    for idx, m in enumerate(markers):
        end = content.find(b"endstream", m.end())
        if end == -1:
            end = len(content)
        raw = content[m.end() : end]
        try:
            decoded = base64.a85decode(raw.strip(), adobe=True)
            decoded = zlib.decompress(decoded)
        except Exception:
            try:
                decoded = zlib.decompress(raw.strip())
            except Exception:
                continue
        text += decoded.decode("latin-1", errors="ignore")
    return text