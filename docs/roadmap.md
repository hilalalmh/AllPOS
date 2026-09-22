# Roadmap Sistem POS

Status fase mengikuti roadmap master (urut, tidak melompat; tiap fase selesai = ditest & diverifikasi).

## Legenda

- DONE — fitur selesai, teruji (test otomatis dan/atau verifikasi manual live).
- IN PROGRESS — sedang dikerjakan.
- TODO — belum dikerjakan.

## PHASE 1 — Foundation [DONE]

- Environment: Python, Node, npm OK; PostgreSQL 17 di-install via winget (service `postgresql-x64-17`).
- Struktur folder sesuai spek.
- Backend FastAPI + koneksi PostgreSQL (`GET /api/v1/health` → status & database ok).
- React (Vite) app dibuat; `npm run lint` & `npm run build` sukses; proxy Vite → API ok.
- Alembic inisialisasi + baseline migration.
- Launcher Windows (`scripts/*.cmd`), README, docker-compose (opsional), .gitignore.

## PHASE 2 — Authentication [DONE]

- Model `roles`/`users` + migrasi; bcrypt; JWT access + refresh.
- Endpoint: `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`.
- RBAC role `OWNER`/`KASIR`; seed user `owner`.
- Test: 9 passed.

## PHASE 3 — Product [DONE]

- Model `categories`/`products` + migrasi; harga `NUMERIC(12,2)`.
- CRUD kategori & produk, search `q`, filter `category_id`, pagination.
- Upload gambar produk (jpg/png/webp ≤ 2MB, random filename, serve `/uploads`).
- RBAC: GET = semua login; tulis = OWNER.
- Seed demo produk (Coffee/Non Coffee).
- Test: 26 passed.

## PHASE 4 — POS / Transaction [DONE]

- Model `transactions`/`transaction_items`/`payments`/`audit_logs` + migrasi.
- Buat transaksi atomarik; harga dari database (bukan client); snapshot nama+harga.
- Invoice `POS-YYYYMMDD-XXXX`; status `PENDING|PAID|CANCELLED`; cancel = status, tidak hapus.
- Payment `CASH|QRIS|TRANSFER`; validasi `paid_amount >= total`.
- RBAC transaksi (kasir = miliknya, owner = semua), filter & pagination.
- Test: 41 passed.

## PHASE 5 — Aplikasi Mobile + Printer [DONE]

- Instalasi Flutter SDK 3.47.5, JDK 17, Android SDK (35/36); `flutter doctor` hijau.
- Aplikasi `mobile/sistem_pos`: struktur spek, login JWT, POS (list produk), state Riverpod, sesi tersimpan.
- Printer Bluetooth: scan/connect/disconnect, **Tes Cetak**, cetak struk, **cetak ulang**; kertas 58/80 mm; auto-reconnect; struk terakhir dipersist.
- Patch plugin `bluetooth_print` (AGP 8+) → `third_party`, di-lock via `dependency_overrides`.
- Build APK debug sukses; `flutter analyze` clean; `flutter test` 3 passed; Dart → API ok (health/login/products 200).
- Keterbatasan: hidup printer perlu perangkat Android + printer fisik (verifikasi manual).

## PHASE 6 — Dashboard Web (React) [DONE]

- Login dashboard (JWT) + layout admin: guard `RequireAuth`, menu dinamis per role (OWNER melihat semua, KASIR hanya Kasir & Transaksi), logout.
- Axios interceptor: sisipkan `Authorization: Bearer` otomatis + auto-refresh saat 401 (retry 1x) + event `auth-expired` → logout.
- Alur "Bayar" di web (`/pos`): grid produk (search + filter kategori) → keranjang (qty +/-) → diskon, metode CASH/QRIS/TRANSFER, uang dibayar & kembalian → simpan transaksi → popup sukses + **Cetak Struk** (CSS print 58mm).
- Melihat transaksi (`/transactions`): filter invoice/status/metode/tanggal, pagination, detail, cancel.
- Manajemen produk & kategori (`/products`, `/categories`): CRUD + upload gambar (produk), gating OWNER.
- Dashboard statistik (`/`): kartu ringkasan, grafik penjualan (AreaChart), menu terlaris (BarChart), filter Hari Ini / 7 Hari / 30 Hari.
- Backend: endpoint agregasi baru `dashboard.py` (summary, sales, best-sellers) RBAC OWNER — test **49 passed** (dashboard 8 test).
- Verifikasi live: lint sukses, `npm run build` sukses, end-to-end lewat proxy Vite (login → transaksi → summary update → kasir 403) OK.

## PHASE 7 — Integrasi & Offline Mobile (Flutter) [IN PROGRESS / berikutnya]

- Cart + checkout lengkap di app kasir (bayar CASH/QRIS/TRANSFER, validasi kembalian) — layar POS Flutter saat ini masih placeholder.
- Alur Bayar → Payment Success → Cetak Struk (printer); printer gagal tidak menghapus transaksi (sudah aman di backend).
- Koneksi ke API produktif/bersih (base URL configurable via `--dart-define`).
- Sinkronisasi SQLite offline → RS: bisa antri transaksi saat offline dan sinkron saat online.
- Push notifikasi / pending order (jika disepakati).

## PHASE 8 — Fitur Lanjutan [TODO]

- SQLite sebagai cadangan & sinkronisasi.
- Skenario printer: Wi-Fi/network, logo, QR/barcode di struk.
- Multi-tenant / profil toko (nama & alamat di struk dikonfigurasi dari dashboard).
- Audit trail lengkap + export laporan (CSV/PDF).
- Deploy backend (gunicorn/uvicorn + nginx) & build produksi Web APK.

## Catatan Roadmap

- Setiap features wajib diuji (pytest backend, widget test Flutter, uji manual via live check) sebelum dinyatakan selesai.
- Jangan meng-claim sukses tanpa verifikasi aktual.