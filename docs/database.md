# Skema Database — Sistem POS

Database utama: **PostgreSQL 17**, nama `sistem_pos` (owner `pos_user`).
Database test (pytest): `sistem_pos_test`.

Uang disimpan sebagai `NUMERIC(12,2)`. Waktu memakai `timestamptz`. Migrasi dikelola Alembic (folder `backend/alembic/versions`).

## Garis Besar Relasi

```
roles 1───* users 1───* transactions 1───* transaction_items
                              │                  │
                              │                  └──* products (RESTRICT)
                              └──1 payments
users 1───* audit_logs
categories 1───* products 1───* transaction_items (RESTRICT)
store_profiles        (singleton id=1, mandiri)
```

- Transaksi di-**cancel**, tidak dihapus fisik.
- Item & payment ikut terhapus (CASCADE) jika transaksi dihapus (hanya satuan dev).
- Produk/kategori yang sudah dipakai transaksi tidak bisa dihapus (RESTRICT).

## Tabel `roles`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| name | varchar(50) | UNIQUE + INDEX |
| is_active | bool | default true |

Role seed: `OWNER`, `KASIR`. Referensi aplikasi: enum `RoleEnum` (`backend/app/models/role.py`).

## Tabel `users`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| role_id | int FK → roles.id | RESTRICT, INDEX |
| username | varchar(50) | UNIQUE + INDEX |
| password_hash | varchar(255) | bcrypt |
| full_name | varchar(100) | |
| is_active | bool | default true |
| created_at | timestamptz | server_default now() |
| updated_at | timestamptz | onupdate now() |

## Tabel `categories`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| name | varchar(50) | UNIQUE + INDEX |
| is_active | bool | default true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## Tabel `products`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| category_id | int FK → categories.id | RESTRICT, INDEX |
| name | varchar(100) | INDEX (untuk search) |
| description | text | nullable |
| sku | varchar(50) | UNIQUE + INDEX, nullable |
| price | numeric(12,2) | wajib |
| image_url | varchar(255) | nullable |
| is_active | bool | default true |
| created_at | timestamptz | |
| updated_at | timestamptz | |

## Tabel `transactions`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| invoice_number | varchar(30) | UNIQUE + INDEX, `POS-YYYYMMDD-XXXX` |
| cashier_id | int FK → users.id | RESTRICT, INDEX |
| subtotal | numeric(12,2) | |
| discount | numeric(12,2) | default 0 |
| total | numeric(12,2) | |
| payment_method | varchar(20) | `CASH|QRIS|TRANSFER` |
| paid_amount | numeric(12,2) | |
| change_amount | numeric(12,2) | default 0 |
| status | varchar(20) | `PENDING|PAID|CANCELLED`, INDEX |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Enum di aplikasi: `PaymentMethod`, `TransactionStatus` (`backend/app/models/transaction.py`).

## Tabel `transaction_items` (snapshot)

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| transaction_id | int FK → transactions.id | CASCADE, INDEX |
| product_id | int FK → products.id | RESTRICT, INDEX |
| product_name | varchar(100) | snapshot nama |
| price | numeric(12,2) | snapshot harga |
| quantity | int | |
| subtotal | numeric(12,2) | |
| note | text | nullable |

Snapshot `product_name` + `price` membuat riwayat transaksi tidak berubah walau produk diedit nanti.

## Tabel `payments`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| transaction_id | int FK → transactions.id | CASCADE, UNIQUE, INDEX (satu pembayaran per transaksi) |
| method | varchar(20) | |
| amount | numeric(12,2) | |
| change_amount | numeric(12,2) | default 0 |
| created_at | timestamptz | |

## Tabel `audit_logs`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | serial PK | |
| user_id | int FK → users.id | SET NULL, nullable, INDEX |
| action | varchar(50) | INDEX, contoh `auth.login`, `transaction.create`, `transaction.cancel`, `product.create`, `category.update`, `store_profile.update`, `report.csv` |
| entity_type | varchar(50) | INDEX; contoh `user`, `transaction`, `product`, `category`, `store_profile`, `report` |
| entity_id | int | nullable |
| details | jsonb | nullable (detail bebas) |
| created_at | timestamptz | |

## Tabel `store_profiles`

| Kolom | Tipe | Keterangan |
|-------|------|-----------|
| id | int PK (singleton) | selalu `1` |
| store_name | varchar(100) | default `SISTEM POS` |
| address | varchar(255) | nullable |
| phone | varchar(30) | nullable |
| footer | varchar(255) | default `TERIMA KASIH ~ SILAHKAN DATANG KEMBALI`, dipakai di footer struk |
| created_at | timestamptz | |
| updated_at | timestamptz | |

Satu baris (id=1) di-seed; dipakai web & mobile sebagai header/footer struk.

## Migrasi (Alembic)

| Revisi | Deskripsi |
|--------|-----------|
| `ae49cdc7617a` | Baseline (kerangka) |
| `8e22230fef65` | add roles & users |
| `c201f1d8a910` | add categories & products |
| `3ed605c47695` | add transactions, payments, audit_logs |
| `a1b2c3d4e5f6` | add store_profiles |

Perintah:

```bash
cd backend
python -m alembic upgrade head      # aplikasikan semua
python -m alembic revision --autogenerate -m "deskripsi"
```

## Konfigurasi Koneksi

`.env` (backend): `DATABASE_URL=postgresql+psycopg://pos_user:pos_password@localhost:5432/sistem_pos`. Untuk test, conftest memakai DB `sistem_pos_test` via dependency override (bukan dari `.env`).

## Data Seed

`python -m app.services.seed` (idempotent):

- Role `OWNER`, `KASIR`.
- User `owner` (password dari `SEED_ADMIN_PASSWORD`, default dev `admin123`).
- Kategori `Coffee`, `Non Coffee` + produk demo (Es Kopi, Americano, Latte, Matcha, Chocolate, Tea).
- Profil toko `id=1` (SISTEM POS) — idempotent, tidak menimpa nilai yang sudah diubah.

Jika tabel `store_profiles` belum ada di DB, jalankan `python -m alembic upgrade head` (revisi `a1b2c3d4e5f6`).