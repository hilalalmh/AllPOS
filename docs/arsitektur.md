# Arsitektur Sistem POS

Dokumen ini menjelaskan arsitektur keseluruhan Sistem POS untuk coffee shop/kedai.

## Gambaran Umum

Sistem terdiri dari 3 aplikasi utama + database:

```
        +-----------------+          +------------------+
        |  Mobile (Kasir) |          |  Web (Dashboard) |
        |  Flutter 3.47   |          |  React + Vite    |
        +--------+--------+          +--------+---------+
                 |  HTTPS / HTTP (REST, JSON, Bearer JWT)
                 +------------------+------------------+
                                    |
                          +---------+---------+
                          |  Backend (API)   |
                          |  FastAPI         |
                          |  /api/v1/*       |
                          +---------+---------+
                                    |
                    +---------------+---------------+
                    |               |               |
            +-------+-------+  +---+----+   +------+--------+
            |  PostgreSQL   |  | Uploads |  | Thermal       |
            |   (primary)   |  | image   |  | Printer       |
            |  sistem_pos   |  | files   |  | (ESC/POS BT)  |
            +---------------+  +--------+   +---------------+
```

Komponen tambahan pada perangkat kasir:
- **SQLite lokal (Flutter)** — cadangan offline / cache perangkat (belum diimplementasikan).
- **Printer termal** — koneksi Bluetooth (ESC/POS), kertas 58 mm / 80 mm.

## Komponen

### 1. Backend (FastAPI)

- Python 3.14, FastAPI, Uvicorn di port `8000`.
- SQLAlchemy 2.x (ORM, tipe `Mapped`/`mapped_column`) + Alembic (migrasi).
- Driver: psycopg 3 (`postgresql+psycopg://`).
- Pydantic v2 + pydantic-settings untuk konfigurasi (`.env`).
- Struktur berlapis:

```
backend/app/
├── core/          # config, database (get_db), security (bcrypt+JWT), deps (RBAC), storage (upload gambar)
├── models/        # ORM: role, user, product, transaction, audit
├── schemas/       # Pydantic: request/response (serializer uang Decimal -> float)
├── repositories/  # akses data (base, role, user, product, transaction)
├── services/      # logika bisnis (auth, product, transaction, seed)
└── routers/       # endpoint API (/health, /auth, /categories, /products, /transactions)
```

Alur request per endpoint: `Router -> Service (biz) -> Repository (ORM/SQL)`. Transaction dibuat **atomarik** dalam satu session; sukses → `commit`, error → `rollback` (lihat `core/database.py` `get_db`).

### 2. Mobile Kasir (Flutter)

- Flutter 3.47.5 stable, Riverpod 2 (state), `http` (REST), `shared_preferences` (persistensi sesi & preferensi printer), `bluetooth_print` (Bluetooth classic ESC/POS).
- Struktur (sesuai spek):

```
mobile/sistem_pos/lib/
├── core/          # AppConfig (API_BASE_URL via --dart-define, default http://10.0.2.2:8000)
├── models/        # user, product, receipt (struk)
├── services/      # api_client, receipt_service, printer_service
├── repositories/  # session_store (prefs), auth_repository, product_repository
├── providers/     # Riverpod: auth, printer, produk
├── screens/       # splash, login, pos, printer_settings
└── widgets/
```

- Token JWT disimpan di `shared_preferences`; `ApiClient` menyisipkan `Authorization: Bearer` otomatis.
- **Printer**: scan Bluetooth, connect, disconnect, tes cetak, cetak struk, cetak ulang; kertas 58/80 mm; auto-reconnect; struk & printer terakhir dipersist.
- Build Android: toolkit menggunakan **AGP 8.11.1 + Gradle 8.14** (bukan AGP 9/Gradle 9 bawaan template) karena kompatibilitas plugin printer. Plugin `bluetooth_print` dipatch dan dikunci via `dependency_overrides` → `mobile/sistem_pos/third_party/bluetooth_print`.

### 3. Web Dashboard (React + Vite)

- React 18, Vite 6, TypeScript 5.6, Tailwind 3; Axios, React Router, Zustand, Recharts.
- Dev server `localhost:5173`, proxy `/api` → `localhost:8000`.
- Status saat ini: kerangka app, layout dashboard, halaman Home & Health Check.

### 4. Database (PostgreSQL 17)

- DB utama: `sistem_pos`, owner `pos_user`. Test: `sistem_pos_test` (pytest, dependency override).
- Skema lengkap: lihat `docs/database.md`.

## Autentikasi & Otorisasi (RBAC)

- Login `POST /api/v1/auth/login` → `access_token` (JWT HS256, default 60 menit) + `refresh_token` (7 hari).
- Role: `OWNER`, `KASIR` (seed). Dideklarasikan sebagai `RoleEnum`; disimpan di tabel `roles`.
- Endpoint membaca token via `HTTPBearer`; `core/deps.py`:
  - `get_current_user` → wajib login.
  - `require_roles(...)` → wajib punya salah satu role (mis. semua operasi tulis produk = `OWNER`).
- Otorisasi data: kasir hanya melihat/membatalkan transaksi miliknya; OWNER melihat semua (diterapkan di `TransactionService`).

## Alur Transaksi (prinsip atomic)

1. Kasir memilih produk di app kasir → `POST /api/v1/transactions`.
2. Backend memvalidasi: produk ada & aktif, harga diambil **dari database** (bukan dari client), kalkulasi subtotal → diskon → total.
3. Validasi pembayaran: `paid_amount >= total`, metode `CASH|QRIS|TRANSFER`.
4. Simpan `transactions` + `transaction_items` (snapshot nama dan harga) + `payments` + `audit_logs` dalam satu transaksi DB; `commit`.
5. Invoice number `POS-YYYYMMDD-XXXX` (unik, urut harian, retry 5x jika bentrok).
6. Status: `PENDING`/`PAID`/`CANCELLED`. Transaksi di-cancel (tidak dihapus), via `POST /transactions/{id}/cancel`.

Printer gagal / putus **tidak** membatalkan transaksi — transaksi sudah tersimpan; struk bisa dicetak ulang dari layar Pengaturan Printer.

## Keamanan

- Password: bcrypt (hash), tidak pernah disimpan plaintext.
- JWT: secret di `.env`, algoritma HS256; access + refresh.
- Upload gambar: hanya `jpg/png/webp`, maks 2 MB, nama file acak (UUID), disajikan dari `/uploads/`.
- Uang: `NUMERIC(12,2)` di DB; diserialkan ke `float` di API.
- Sensitif (`.env`, venv, build) di `.gitignore`; jangan commit secret.

## Konvensi Teknis

- Migrasi DB: Alembic; setiap perubahan skema = revisi baru, lalu `python -m alembic upgrade head`.
- Test backend: `pytest` (berjalan terhadap `sistem_pos_test`, seed owner/kasir/produk demo). 41 test lulus.
- Test Flutter: `flutter test` (mis. format struk). 3 test lulus.
- Verifikasi tangan: `curl http://localhost:8000/api/v1/health` → `{"status":"ok","database":"ok"}`.
- Skrip launcher Windows di `scripts/`: `start_dev.cmd`, `start_backend.cmd`, `start_web.cmd`, `restart_backend.cmd`, `run_backend.cmd`.

## Keputusan Teknis Penting

- Pindah ke **JDK 17 + Android SDK (platform 35/36)** agar toolchain Android hijau.
- Downgrade template Android **AGP 9/Gradle 9 → AGP 8.11.1/Gradle 8.14** (plugin printer bluetooth_print 2021 tidak kompatibel dengan AGP 9).
- `bluetooth_print` dipatch: tambah `namespace`, hapus v1-embedding `Registrar`, buang `jcenter()`, buang buildscript AGP 4.1.2; dikunci via `dependency_overrides` ke folder `third_party` (persisten di repo).
- Format uang layar: titik ribuan + koma desimal (`Rp 36.000,00`).