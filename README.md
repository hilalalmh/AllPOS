# Sistem POS

Sistem Point of Sale untuk coffee shop/kedai: Flutter (kasir), React + Vite (dashboard), FastAPI (backend), PostgreSQL (database utama), SQLite (offline Flutter), thermal printer (Bluetooth/Wi-Fi).

## Struktur Proyek

```
SISTEM-POS/
├── backend/                 # FastAPI + SQLAlchemy + Alembic
├── mobile/
│   └── sistem_pos/          # Flutter (kasir) — Android (+ web fallback)
├── web/
│   └── sistem_pos_dashboard/# React + Vite + TypeScript + Tailwind
├── scripts/                 # launcher dev (Windows)
├── docs/                    # dokumentasi proyek (arsitektur, API, DB, roadmap, memori)
├── docker-compose.yml       # optional: PostgreSQL via Docker
└── README.md
```

## Dokumentasi

| Dokumen | Isi |
|---------|-----|
| `docs/tujuan.md` | Tujuan project, prinsip master (backend otoritas harga, invoice unik, dsb.), fase & cara menjaga progress |
| `docs/arsitektur.md` | Arsitektur sistem: komponen, RBAC, alur transaksi, keamanan, keputusan teknis |
| `docs/api.md` | Referensi lengkap endpoint REST (path, auth, body, response, error) |
| `docs/database.md` | Skema PostgreSQL: tabel, kolom, relasi, enum, migrasi Alembic |
| `docs/roadmap.md` | Status fase roadmap & rencana ke depan |
| `docs/setup.md` | Setup dari nol, referensi `.env`, skrip launcher, backup/restore DB, verifikasi |
| `docs/memory.md` | Memori kerja proyek: lingkungan, keputusan, gotcha, kondisi terkini |

## Stack

- Backend: Python 3.14, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, psycopg 3
- Mobile: Flutter 3.47 (Dart 3.13), Riverpod 2, `bluetooth_print` (ESC/POS via Bluetooth), `shared_preferences`, `sqflite` (offline queue)
- Web: React 18, Vite 6, TypeScript 5.6, Tailwind 3, Axios, React Router, Zustand, Recharts
- Database: PostgreSQL 17 (default user `pos_user` / DB `sistem_pos`); SQLite lokal di Flutter untuk antrian offline

## Requirement Environment

| Komponen | Versi | Status |
|----------|-------|--------|
| Python   | 3.14.0 | OK |
| Node.js  | 24.11.1 | OK |
| npm      | 10.9.2 | OK |
| PostgreSQL | 17.11 (service `postgresql-x64-17`) | OK |
| Flutter  | 3.47.5 stable | OK (D:\flutter) |
| Android SDK | platform 35 & 36, build-tools 35.0.0 | OK (D:\Android\sdk) |
| JDK      | Temurin 17.0.20 | OK |

> Android SDK & JDK di-install agar `flutter doctor` Android toolchain hijau. Flutter/Android/JDK PATH sudah ditambahkan ke environment user.
> `flutter build apk --debug` berhasil memproduksi `mobile/sistem_pos/build/app/outputs/flutter-apk/app-debug.apk`.

## Setup Database (dilakukan di PHASE 1)

```sql
CREATE ROLE pos_user LOGIN PASSWORD 'pos_password';
CREATE DATABASE sistem_pos OWNER pos_user;
```

Kredensial aplikasi ada di `backend/.env` (jangan di-commit).

## Menjalankan Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate.bat   # Windows
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check: `http://localhost:8000/api/v1/health` → `{"status":"ok","database":"ok"}`

Migrasi database (Alembic):

```bash
cd backend
python -m alembic upgrade head
```

## Menjalankan Web Dashboard

```bash
cd web/sistem_pos_dashboard
npm install
npm run dev
```

Dev server: `http://localhost:5173` — proxy `/api` → `http://localhost:8000`.
Halaman Health Check: `http://localhost:5173/health`.

## Menjalankan Aplikasi Flutter (Kasir)

```bash
cd mobile/sistem_pos
flutter pub get
flutter run                          # butuh emulator/HP Android (Bluetooth untuk printer)
dart run tool/check_api.dart         # cek koneksi Dart → backend (harus backend hidup)
```

Base URL API default `http://10.0.2.2:8000` (emulator Android), bisa diubah:

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
flutter build apk --debug --dart-define=API_BASE_URL=http://192.168.1.10:8000
```

> Catatan build Android: template memakai AGP 8.11.1 + Gradle 8.14 (bukan default AGP 9/Gradle 9) karena plugin printer lama. Paket `bluetooth_print` dipatch namespace + v1-embedding lalu dikunci via `dependency_overrides` ke `mobile/sistem_pos/third_party/bluetooth_print` (persisten di repo).

## Menjalankan Keduanya Sekaligus

```cmd
scripts\start_dev.cmd
```

Membuka 2 jendela terminal (minimized) untuk backend dan web.

## PHASE 1 — Foundation (DONE)

Hasil verifikasi (teruji, bukan asumsi):

1. Environment: Python, Node, npm tersedia. PostgreSQL 17 diinstal via winget & dijalankan sebagai service.
2. Struktur folder dibuat sesuai spek.
3. Backend FastAPI + koneksi PostgreSQL berjalan.
4. React (Vite) app dibuat & build sukses (`npm run lint`, `npm run build`).
5. Alembic inisialisasi + baseline migration tereksekusi ke PostgreSQL.
6. Endpoint health check `GET /api/v1/health` → **status ok, database ok**.
7. Test React → API melalui proxy Vite (`http://localhost:5173/api/v1/health`) → **ok**.
8. Test Flutter → API: **DONE di PHASE 5** (Dart script `tool/check_api.dart` → health/login/products OK).

Flag PHASE 1 selesai. Siap lanjut PHASE 2 (Authentication) setelah Flutter disiapkan.

## PHASE 2 — Authentication (DONE)

- Model `roles` & `users` + migration Alembic (`8e22230fef65`).
- JWT (access + refresh), password di-hash dengan bcrypt.
- Endpoint:
  - `POST /api/v1/auth/login` — login, return access + refresh token.
  - `POST /api/v1/auth/refresh` — tukar refresh token jadi token baru.
  - `GET  /api/v1/auth/me` — profil user terautentikasi (wajib token).
- Role seed: `OWNER`, `KASIR`.
- Seed default admin (dev only):

```bash
cd backend
.venv\Scripts\activate.bat
python -m app.services.seed
# login: owner / admin123   (ubah SEED_ADMIN_PASSWORD di .env untuk production)
```

Test:

```bash
cd backend
python -m pytest tests -v   # 9 passed (login, token, me, refresh, invalid cases)
```

## PHASE 3 — PRODUCT (DONE)

- Model `categories` & `products` + migration (`c201f1d8a910`), harga pakai `NUMERIC(12,2)`.
- Endpoint:
  - `GET/POST /api/v1/categories`, `PUT/DELETE /api/v1/categories/{id}`
  - `GET/POST /api/v1/products`, `GET/PUT/DELETE /api/v1/products/{id}`
  - Search `?q=`, filter `?category_id=`, pagination `?page=&page_size=`
  - Upload gambar: `POST /api/v1/products` multipart `image` → disimpan di `backend/uploads/`, disajikan di `/uploads/...`
- RBAC: GET diakses semua user terautentikasi; POST/PUT/DELETE hanya `OWNER`.
- Validasi: SKU unik (409), kategori wajib ada & aktif, format & ukuran gambar (max 2MB, jpg/png/webp).
- Harga final selalu dihitung backend (harga dari database, bukan client).
- Seed contoh data (Coffee/Non Coffee + 6 produk) via `python -m app.services.seed`.
- Test: `backend/tests/test_product.py` — total **26 passed** (CRUD, RBAC, search, pagination, validasi).

## PHASE 4 — POS (DONE)

- Model `transactions`, `transaction_items`, `payments`, `audit_logs` + migration (`3ed605c47695`).
- Alur transaksi mengikuti prinsip atomic (sec. 41): validasi request → validasi produk → harga dari **database** (bukan client) → subtotal → discount → total → validasi pembayaran → buat transaction + items + payment → COMMIT, error = ROLLBACK.
- Invoice number: `POS-YYYYMMDD-XXXX` (unique, urut harian, retry saat race).
- Snapshot `product_name` + `price` disimpan di `transaction_items` — riwayat tidak berubah walau harga produk diubah.
- Status: `PENDING`/`PAID`/`CANCELLED`. Transaksi di-cancel, tidak dihapus fisik.
- Payment: `CASH`, `QRIS`, `TRANSFER`; validasi `paid_amount >= total` → *"Pembayaran tidak mencukupi."*
- Endpoint:
  - `POST /api/v1/transactions`, `GET /api/v1/transactions` (filter q/invoice, cashier, payment_method, status, tanggal, pagination)
  - `GET /api/v1/transactions/{id}`, `POST /api/v1/transactions/{id}/cancel`
- RBAC transaksi: kasir → miliknya sendiri; owner → semua; kasir tidak bisa akses transaksi kasir lain (403).
- Audit log minimal: `transaction.create`, `transaction.cancel`.
- Test: `backend/tests/test_transaction.py` — total **41 passed** (alur lengkap, snapshot, harga anti-manipulasi, RBAC, filter, pagination, cancel).

## Catatan

- Jangan commit secret. Semua kredensial lewat `.env`.
- Ganti `JWT_SECRET` di `.env` sebelum production.

## PHASE 5 — PRINTER & APLIKASI FLUTTER (DONE)

### Flutter SDK + toolchain
- Flutter 3.47.5 stable diklone ke `D:\flutter`; JDK Temurin 17 & Android SDK (platforms 35/36, build-tools 35.0.0) diinstall; `flutter doctor` → Android toolchain hijau.

### Aplikasi `mobile/sistem_pos`
Struktur sesuai spek:
```
lib/
├── core/          # app_config (API_BASE_URL via --dart-define)
├── models/        # user, product, receipt (struk)
├── services/      # api_client, printer_service, receipt_service
├── repositories/  # session_store (prefs), auth_repository, product_repository
├── providers/     # Riverpod (auth, printer, produk)
├── screens/       # splash, login, pos, printer_settings
└── widgets/
```
- Login ke backend FastAPI (JWT), sesi disimpan di `shared_preferences`.
- **Printer service** berbasis `bluetooth_print` (Bluetooth classic ESC/POS): scan, connect, disconnect, **Tes Cetak**, **Cetak Struk**, **Cetak Ulang**, kertas **58 mm / 80 mm**, auto-reconnect printer terakhir.
- **Receipt service**: membangun baris struk (header toko, invoice, kasir, tanggal, item `qty x harga`, subtotal, diskon, total, dibayar, kembalian, sambutan) — 58 mm lebar 32 kolom.
- Layar Pengaturan Printer: status bluetooth/koneksi, pindai & hubungkan, pilih ukuran kertas, tes cetak, cetak ulang struk terakhir, tampilan error.
- Receipt & printer terakhir dipersist (reprint setelah app restart).
- Android: permission Bluetooth (+legacy location), `INTERNET`, `usesCleartextTraffic` untuk API lokal.
- Printer tidak tersedia/putus tidak menghapus transaksi — error hanya menunjukkan pesan (struk tetap tersimpan untuk cetak ulang).

### Patch plugin bluetooth_print (AGP 8+)
Salinan plugin dikunci di `mobile/sistem_pos/third_party/bluetooth_print` via `dependency_overrides`:
- `namespace 'com.example.bluetooth_print'` + `compileSdk 34` + buang `jcenter()`;
- hapus v1-embedding `Registrar` (API sudah dihapus Flutter modern);
- buildscript AGP 4.1.2 dibuang (pakai AGP dari root).

### Verifikasi
- `flutter analyze` → No issues found.
- `flutter test` → 3 passed (struk: invoice/kasir/item/money format, config kertas 58/80).
- `flutter build apk --debug` → **apk jadi** (146 MB debug).
- `dart run tool/check_api.dart` → health 200, login 200, products 200 (backend live) — **Flutter ↔ FastAPI terhubung**.
- Cetak fisik memakai printer Bluetooth: perlu perangkat Android + printer termal yang terpasang (langkah verifikasi manual).

## PHASE 6 — DASHBOARD WEB (DONE)

### Backend: endpoint statistik (RBAC OWNER)
- `GET /api/v1/dashboard/summary` — total penjualan, jumlah transaksi, item, produk aktif, best-seller (periode default hari ini; `start_date`/`end_date`).
- `GET /api/v1/dashboard/sales?group_by=day|month` — deret penjualan.
- `GET /api/v1/dashboard/best-sellers?limit=5` — ranking menu terlaris.
- Transaksi `CANCELLED` tidak dihitung. Kasir → `403`. Test dashboard: **49 passed total**.

### Web dashboard (`/`)
- **Login** (JWT) + guard `RequireAuth`; menu adaptif role (OWNER: Dashboard/Kasir/Transaksi/Produk/Kategori/Health; KASIR: Kasir/Transaksi).
- **Axios interceptor**: sisipkan Bearer token + auto-refresh saat 401 (retry 1x) → event `auth-expired` → logout.
- **Kasir & Bayar** (`/pos`): cari & pilih produk, keranjang, diskon, metode `CASH/QRIS/TRANSFER`, kembalian, **Cetak Struk 58mm** (CSS print).
- **Transaksi** (`/transactions`): filter invoice/status/metode/tanggal, pagination, detail, batalkan.
- **Produk** (`/products`) & **Kategori** (`/categories`): CRUD + upload gambar, khusus OWNER.
- **Dashboard** (`/`): kartu ringkasan + grafik penjualan (AreaChart) + menu terlaris (BarChart), filter Hari Ini/7 Hari/30 Hari.

Verifikasi: `npm run lint` OK, `npm run build` OK, end-to-end live lewat proxy Vite (login → transaksi `POS-20260923-0001` → summary ikut update → kasir 403) sukses.

## PHASE 7 — POS MOBILE & OFFLINE (DONE)

### Transaksi kasir mobile (Flutter)
- Keranjang: tambah produk (cari sederhana), ubah qty, diskon global, metode `CASH/QRIS/TRANSFER`, uang dibayar & kembalian, ringkasan.
- Checkout → `POST /api/v1/transactions` (harga tetap dari backend) → halaman sukses menampilkan struk → **cetak struk / cetak ulang** via bluetooth_print.
- Kartu ulang transaksi tadi dipersist (`printer.last_receipt`).

### Offline SQLite (queue + sync)
- Saat jaringan bermasalah (timeout/`SocketException`), transaksi **tidak gagal** — masuk antrian `pending_transactions` (SQLite, snapshot nama+harga lokal) dan disinkronkan otomatis saat online; ada tombol sinkron manual + halaman daftar status `PENDING/SYNCED/FAILED` (retry / hapus).
- **Idempoten**: setiap checkout mengirim `local_ref` unik (dibuat per transaksi offline); backend menjadikannya **UNIQUE global** sehingga transaksi yang tersinkron ulang tidak menimbulkan penjualan ganda.
- Error 4xx (validasi/RBAC) **tidak** jatuh offline — tetap tampil error; error jaringan/5xx tidak dihitung sebagai kegagalan (tetap `PENDING`).
- Deps: `sqflite` + `path` (runtime), `sqflite_common_ffi` (test).

### Base URL fleksibel
- `--dart-define=API_BASE_URL=...`; default `http://10.0.2.2:8000` (emulator). `ApiClient` memangkas trailing `/` + timeout 20 detik.

Verifikasi: `flutter analyze` clean, `flutter test` (offline sync + ApiClient + cart), `flutter build apk --debug` sukses, `POST /transactions` live → `POS-20260923-0002`. **Belum** diuji di perangkat offline nyata (fallback diuji via unit test `SocketException`).

## PHASE 8 — FITUR LANJUTAN (SEBAGIAN DONE)

### Profil Toko (DONE)
- Backend: tabel `store_profiles` (singleton id=1), `GET /api/v1/store-profile` (semua auth) & `PUT` (OWNER); migrasi `a1b2c3d4e5f6`; seed idempotent.
- Web: halaman **Profil Toko** (`/store-profile`, OWNER) — nama toko, alamat, telepon, footer struk; tersimpan via zustand store; struk POS (`/pos`) header/footer dinamis.
- Mobile: model + repository + cache `SessionStore` + `StoreProfileNotifier` (ambil saat login) → struk `ReceiptService` dinamis (fallback `SISTEM POS`).
- Live E2E: GET → PUT ("Aroma Kopi Nusantara") → GET ulang persist. Cetak fisik tetap perlu verifikasi manual.

### Audit Trail + Export Laporan (DONE)
- Backend: `AuditLog` diinstrumentasi penuh — `auth.login`, `transaction.create/cancel`, `product/category.create/update/delete`, `store_profile.update`, `report.csv/pdf`. `GET /api/v1/audit-logs` (OWNER), filter action/entitas/user/tanggal/q + pagination.
- Export: `GET /api/v1/reports/transactions.csv` & `transactions.pdf` (reportlab), filter tanggal/metode/status, OWNER-only.
- Web: halaman **Audit Trail** (`/audit`, OWNER) + tombol **Export CSV / Export PDF** di Transaksi (hanya tampil untuk OWNER).

### Sisa (belum dikerjakan)
- Printer Wi-Fi/network, logo, QR/barcode di struk.
- Deploy backend (gunicorn/uvicorn + nginx) & build produksi Web/APK.

## Audit Keamanan (Ronde 1–3 — DONE)

Pengerasan keamanan dilakukan bertahap dalam 3 ronde audit (semua teruji — lihat Status Test):

- **Otentikasi**: password di-hash bcrypt; verifikasi waktu-sama + *dummy bcrypt* saat username tak ditemukan (anti username-enumeration); JWT access (60 mnt) + refresh (7 hari) tersimpan di DB (`refresh_tokens`, jti unik) dengan **rotasi atomik** (dipakai sekali; ulang pakai ditolak).
- **Throttle login**: gagal login ≥ `LOGIN_MAX_FAILURES` dalam jendela `LOGIN_LOCKOUT_MINUTES` → `429` + `Retry-After`. Hanya percobaan gagal yang dihitung (bot tidak bisa mengunci akun orang lain via login sukses).
- **Sesi dicabut**: ganti password (oleh diri sendiri maupun admin) **mencabut semua refresh token** user.
- **Backend = otoritas harga**: harga dari database, bukan client. Replay offline aman: `local_ref` unik **global** → kirim ulang isi sama = transaksi yang sama; isi berlainan → `409`.
- **Upload aman**: validasi tipe via **magic bytes** (bukan sekadar ekstensi), ukuran ≤ 2 MB, nama UUID; penghapusan file dengan guard traversal (`..`, `/`, `\`).
- **Fail-closed**: `ENVIRONMENT=production` menolak start bila `JWT_SECRET` lemah/<32 karakter atau seed `admin123`.
- **Mobile**: endpoint `/api/v1/auth/*` tak memicu logout saat token habis; transaksi offline (jaringan/5xx) tidak dianggap gagal; session init gagal → bersihkan & balik ke login; logout revolasi async (UI tidak terblokir).
- **Web**: auto-refresh **single-flight** + penjaga generasi token; logout paksa hanya saat refresh benar-benar `401`; retry idempoten (GET/HEAD/PUT/PATCH/DELETE); pesan error login spesifik (429/403/network).

## Status Test

| Komponen | Perintah | Hasil |
|----------|----------|-------|
| Backend | `.\\.venv\\Scripts\\python.exe -m pytest -q` (dari `backend/`) | **100 passed** |
| Web | `npm run lint` + `npm run build` | bersih & sukses |
| Mobile | `flutter analyze` + `flutter test` | clean & **26 passed** |
| Mobile | `flutter build apk --debug` | sukses |