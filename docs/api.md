# Referensi API — Sistem POS

Base URL backend: `http://localhost:8000`.

Prefix: `/api/v1`. Kecuali disebutkan, body/kirim/terima format **JSON**. Endpoint bermuatan auth mengharap header `Authorization: Bearer <access_token>`.

CORS origin dev: `http://localhost:5173` dan `http://127.0.0.1:5173`.

## Ringkasan Endpoint

| Method | Path | Auth | RBAC | Deskripsi |
|--------|------|------|------|-----------|
| GET | `/api/v1/health` | - | - | Status sehat backend & DB |
| POST | `/api/v1/auth/login` | - | - | Login, dapat token |
| POST | `/api/v1/auth/refresh` | - | - | Tukar refresh → token baru |
| POST | `/api/v1/auth/logout` | - | - | Cabut refresh token (best effort, 204) |
| GET | `/api/v1/auth/me` | Bearer | - | Profil user aktif |
| GET | `/api/v1/users` | Bearer | OWNER | Daftar pengguna (pager + search) |
| POST | `/api/v1/users` | Bearer | OWNER | Buat pengguna |
| PUT | `/api/v1/users/{id}` | Bearer | OWNER | Ubah pengguna (nama/role/status/password) |
| GET | `/api/v1/categories` | Bearer | - | Daftar kategori aktif |
| POST | `/api/v1/categories` | Bearer | OWNER | Buat kategori |
| PUT | `/api/v1/categories/{id}` | Bearer | OWNER | Ubah kategori |
| DELETE | `/api/v1/categories/{id}` | Bearer | OWNER | Hapus kategori |
| GET | `/api/v1/products` | Bearer | - | Daftar produk (search/filter/pager) |
| GET | `/api/v1/products/{id}` | Bearer | - | Detail produk |
| POST | `/api/v1/products` | Bearer | OWNER | Buat produk (multipart) |
| PUT | `/api/v1/products/{id}` | Bearer | OWNER | Ubah produk |
| DELETE | `/api/v1/products/{id}` | Bearer | OWNER | Hapus produk |
| POST | `/api/v1/transactions` | Bearer | - | Buat transaksi |
| GET | `/api/v1/transactions` | Bearer | kasir=sendiri, owner=semua | Daftar transaksi |
| GET | `/api/v1/transactions/{id}` | Bearer | kasir=sendiri | Detail transaksi |
| POST | `/api/v1/transactions/{id}/cancel` | Bearer | kasir=sendiri | Batalkan transaksi |
| GET | `/api/v1/dashboard/summary` | Bearer | OWNER | Ringkasan penjualan periode |
| GET | `/api/v1/dashboard/sales` | Bearer | OWNER | Deret penjualan per hari/bulan |
| GET | `/api/v1/dashboard/best-sellers` | Bearer | OWNER | Ranking menu terlaris |
: | GET | `/api/v1/store-profile` | Bearer | - | Profil toko (singleton id=1) |
| PUT | `/api/v1/store-profile` | Bearer | OWNER | Perbarui profil toko |
| GET | `/api/v1/audit-logs` | Bearer | OWNER | Audit trail (filter + pager) |
| GET | `/api/v1/reports/transactions.csv` | Bearer | OWNER | Export transaksi CSV |
| GET | `/api/v1/reports/transactions.pdf` | Bearer | OWNER | Export transaksi PDF |
| GET | `/uploads/{nama_file}` | - | - | File gambar produk |

## Kode Error Umum

- `401` — login gagal / token tidak valid / kedaluwarsa.
- `403` — user nonaktif, atau role tidak diizinkan (RBAC).
- `404` — resource tidak ditemukan.
- `409` — duplikat (SKU, nama kategori bersifat unik; replay `local_ref` dengan isi berbeda; gagal membuat invoice unik).
- `422` — validasi gagal (skema, atau aturan bisnis transaksi seperti pembayaran kurang / produk nonaktif).
- `429` — terlalu banyak percobaan login dalam jendela `LOGIN_LOCKOUT_MINUTES` (throttle); sertakan header `Retry-After` (detik).

## Health Check

`GET /api/v1/health`

Response:

```json
{ "status": "ok", "database": "ok" }
```

`database` bernilai `unavailable` jika SELECT 1 ke DB gagal (status menjadi `degraded`).

## Autentikasi

### POST `/api/v1/auth/login`

Body:

```json
{ "username": "owner", "password": "admin123" }
```

Response `200`:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600
}
```

Error: `401` kredensial salah (pesan seragam, terlepas akun ada atau tidak — anti username-enumeration); `403` user nonaktif; `429` terlalu banyak percobaan gagal dari (username, IP) dalam jendela `LOGIN_LOCKOUT_MINUTES` — sertakan header `Retry-After`. Hanya kredensial salah yang menambah counter (login sukses tidak bisa dipakai bot untuk mengunci akun orang lain).

### POST `/api/v1/auth/refresh`

Body:

```json
{ "refresh_token": "<jwt>" }
```

Response `200` sama seperti login. Refresh token **rotasi atomik**: disimpan di tabel `refresh_tokens` (jti unik, `revoked`), setiap refresh memakai token yang sama sekaligus mencabut yang lama (dipakai sekali). Error `401` refresh token tidak valid / sudah dipakai / revoked / kedaluwarsa. **Ganti password (oleh diri sendiri atau admin) mencabut seluruh refresh token user** — sesi lama langsung tidak sah.

### GET `/api/v1/auth/me`

Header Bearer. Response `200`:

```json
{
  "id": 1,
  "role_id": 1,
  "username": "owner",
  "full_name": "Administrator",
  "is_active": true,
  "created_at": "2026-09-22T09:00:00Z",
  "role": "OWNER"
}
```

## Kategori

Skema kategori: `{ id, name, is_active, created_at, updated_at }`.

- `GET /api/v1/categories` → `[{ CategoryOut }]` (hanya `is_active=true`).
- `POST /api/v1/categories` body `{ name }` → 201.
- `PUT /api/v1/categories/{id}` body parsial `{ name?, is_active? }`.
- `DELETE /api/v1/categories/{id}` → 204. Error `409` nama duplikat, `404` tidak ditemukan. Kategori yang dipakai produk tidak bisa dihapus (`ondelete=RESTRICT`, error 409/422 bergantung DB).

## Produk

Skema produk: `{ id, category_id, name, description, sku, price, image_url, is_active, created_at, updated_at }`. `price` dikirim/diterima sebagai angka float.

### GET `/api/v1/products`

Query params:

| Param | Tipe | Keterangan |
|-------|------|-----------|
| `q` | string | Cari nama/SKU (ilike) |
| `category_id` | int | Filter kategori |
| `include_inactive` | bool | Default `false`. Bila `true` → hanya akses OWNER, sertakan produk `is_active=false` |
| `page` | int (>=1) | Halaman, default 1 |
| `page_size` | int (1..100) | Default 20 |

Response `200`:

```json
{
  "items": [ { "id": 1, "category_id": 1, "name": "Es Kopi", "description": null, "sku": "ESKOPI", "price": 18000.0, "image_url": null, "is_active": true, "created_at": "...", "updated_at": "..." } ],
  "total": 6,
  "page": 1,
  "page_size": 20
}
```

(`GET /products` hanya menampilkan produk aktif.)

### GET `/api/v1/products/{id}`

Response `200` ProdukOut; `404` tidak ditemukan.

### POST `/api/v1/products` (multipart/form-data)

| Field | Tipe | Keterangan |
|-------|------|-----------|
| `category_id` | int | Wajib, kategori aktif |
| `name` | string (1..100) | Wajib |
| `price` | float (>0) | Wajib |
| `description` | string | Opsional |
| `sku` | string (<=50) | Opsional, unik (409 jika duplikat) |
| `is_active` | bool | Default `true` |
| `image` | file | Opsional; `image/jpeg|png|webp`, maks 2 MB |

Response `201` ProdukOut. Jika kategori tidak ada → `404`. Jika upload gagal, file tidak tersisa (dibersihkan). Tipe file divalidasi via **magic bytes** (bukan hanya ekstensi/MIME): file yang bukan `jpeg/png/webp` asli ditolak `422`.

### PUT `/api/v1/products/{id}` (JSON)

Body parsial semua field; `price` float > 0. Response `200`; `409` SKU duplikat; `404`.

### DELETE `/api/v1/products/{id}`

Response `204`. Produk yang sudah dipakai di transaksi tidak bisa dihapus fisik (`RESTRICT`).

## Transaksi

Skema response transaksi:

```json
{
  "id": 1,
  "invoice_number": "POS-20260922-0001",
  "cashier_id": 1,
  "subtotal": 56000.0,
  "discount": 0.0,
  "total": 56000.0,
  "payment_method": "CASH",
  "paid_amount": 60000.0,
  "change_amount": 4000.0,
  "status": "PAID",
  "created_at": "2026-09-22T10:30:00Z",
  "items": [
    { "id": 1, "product_id": 1, "product_name": "Es Kopi", "price": 18000.0, "quantity": 2, "subtotal": 36000.0, "note": null }
  ],
  "payment": { "id": 1, "method": "CASH", "amount": 60000.0, "change_amount": 4000.0 }
}
```

Enums: `payment_method` = `CASH | QRIS | TRANSFER`; `status` = `PENDING | PAID | CANCELLED`.

### POST `/api/v1/transactions`

Body:

```json
{
  "items": [
    { "product_id": 1, "quantity": 2, "note": "tanpa gula" }
  ],
  "payment_method": "CASH",
  "paid_amount": 60000,
  "discount": 0,
  "local_ref": "TX-9f3a1c2e...",       // opsional, idempoten offline (8..64 karakter)
  "created_at_local": "2026-09-23T09:00:00+07:00"  // opsional, fase sinkron offline
}
```

Aturan (`TransactionService`):

- `items` 1..50; `quantity` 1..999; `note` <= 255.
- Harga diambil dari database, **bukan** dari client (abaikan `price` di request).
- Semua produk harus ada & aktif.
- `subtotal = sum(qty * harga)`; `total = subtotal - discount`.
- `discount` >= 0; `paid_amount` >= total → jika kurang `422 "Pembayaran tidak mencukupi."`.
- `change = paid - total`.
- Status produk baru = `PAID` (langsung lunas), invoice `POS-YYYYMMDD-XXXX`.
- Membuat audit log `transaction.create`.

Field idempoten (sinkronisasi offline):

- `local_ref` unik per pembayaran (opsional, 8..64). Backend menjadikannya **UNIQUE global** — kirim ulang dengan isi sama → mengembalikan transaksi yang sama **tanpa transaksi baru** (aman untuk ulang-pakai/replay jaringan); isi berbeda terhadap `local_ref` yang sama → `409 "local_ref sudah dipakai untuk transaksi dengan isi berbeda."`.
- `created_at_local` (opsional, timezone-aware) menimpa `created_at` transaksi (fase sinkronisasi luring); ditolak bila > 5 menit ke masa depan.

Response `201`.

### GET `/api/v1/transactions`

Query params (semua opsional): `q` (cari invoice), `cashier_id`, `payment_method`, `status`, `start_date`, `end_date` (format `YYYY-MM-DD`), `page`, `page_size`.

RBAC: KASIR → hanya transaksi miliknya; OWNER → semua (param `cashier_id` diabaikan jika bukan owner).

Response `200`:

```json
{ "items": [ TransactionOut ], "total": 1, "page": 1, "page_size": 20 }
```

### GET `/api/v1/transactions/{id}`

Response `200`; `404` tidak ada; `403` kasir mengakses transaksi kasir lain.

### POST `/api/v1/transactions/{id}/cancel`

Mengubah status `PAID`/`PENDING` → `CANCELLED` + audit log `transaction.cancel`. Error `404` transaksi tidak ada; `400` jika sudah `CANCELLED` (tidak bisa dibatalkan dua kali). Response `200` dengan transaksi terbaru.

## Dashboard (Statistik)

Semua endpoint dashboard **wajib role OWNER** (kasir mendapat 403). Data transaksi yang dihitung **tidak termasuk status CANCELLED**.

### GET `/api/v1/dashboard/summary`

Query params opsional: `start_date`, `end_date` (format `YYYY-MM-DD`). Default: hari ini.

Response `200`:

```json
{
  "start_date": "2026-09-23",
  "end_date": "2026-09-23",
  "sales_total": 18000.0,
  "transaction_count": 1,
  "item_count": 1,
  "active_products": 7,
  "best_seller": { "product_name": "Es Kopi", "quantity": 1, "revenue": 18000.0 }
}
```

Jika belum ada transaksi, `best_seller` bernilai `null`.

### GET `/api/v1/dashboard/sales`

Query params: `start_date`, `end_date`, `group_by` (`day` default | `month`). Response `200`:

```json
[
  { "period": "2026-09-23", "sales_total": 18000.0, "transaction_count": 1 }
]
```

`period` bernilai `YYYY-MM-DD` (day) atau `YYYY-MM` (month).

### GET `/api/v1/dashboard/best-sellers`

Query params: `start_date`, `end_date`, `limit` (1..50, default 5). Response `200`:

```json
{ "items": [ { "product_name": "Es Kopi", "quantity": 1, "revenue": 18000.0 } ] }
```

Diurutkan berdasarkan jumlah terjual, lalu pendapatan.

## Profil Toko

### GET `/api/v1/store-profile`

Akses: semua user terautentikasi. Mengembalikan profil toko singleton (`id=1`); jika belum ada, dibuat otomatis dengan default. Response `200`:

```json
{
  "id": 1,
  "store_name": "SISTEM POS",
  "address": null,
  "phone": null,
  "footer": "TERIMA KASIH ~ SILAHKAN DATANG KEMBALI",
  "created_at": "...",
  "updated_at": "..."
}
```

### PUT `/api/v1/store-profile`

Akses: **OWNER**. Body parsial (field optional): `store_name`, `address`, `phone`, `footer`. Menulis audit log `store_profile.update`. Response `200` dengan profil terbaru.

## Audit Trail

### GET `/api/v1/audit-logs`

Akses: **OWNER**. Query params opsional: `action`, `entity_type`, `user_id`, `start_date`, `end_date` (format `YYYY-MM-DD`), `q` (cari aksi), `page`, `page_size`.

Response `200`:

```json
{
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "username": "owner",
      "action": "auth.login",
      "entity_type": "user",
      "entity_id": 1,
      "details": { "username": "owner" },
      "created_at": "..."
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

Aksi yang direkam: `auth.login`, `transaction.create`, `transaction.cancel`, `product.create/update/delete`, `category.create/update/delete`, `store_profile.update`, `report.csv`, `report.pdf`.

## Laporan (Export)

Semua endpoint laporan **wajib role OWNER**. Query params opsional sama untuk keduanya: `start_date`, `end_date`, `payment_method`, `status`.

### GET `/api/v1/reports/transactions.csv`

Response `200` `text/csv` dengan header `Content-Disposition: attachment; filename=transactions.csv`. Kolom: `invoice_number, cashier, created_at, payment_method, status, subtotal, discount, total, paid_amount, change_amount`.

### GET `/api/v1/reports/transactions.pdf`

Response `200` `application/pdf` (reportlab) — tabel laporan transaksi + ringkasan total.

## Upload File

`GET /uploads/{nama}` → file statis (mount `StaticFiles`). URL lengkap contoh: `http://localhost:8000/uploads/3f5a...jpg`.

## Catatan Integrasi

- Mobile (Flutter): `POST /auth/login` → simpan access token → `GET /auth/me` → panggil API lain dgn Bearer. Detail di `docs/arsitektur.md` dan `docs/memory.md`.
- Saat menguji via browser/halaman web, cookie tidak dipakai; gunakan header Bearer.