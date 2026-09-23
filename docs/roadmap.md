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

## PHASE 7 — Integrasi & Offline Mobile (Flutter) [DONE]

(Core selesai & teruji. Push notifikasi terdaftar sebagai opsi "jika disepakati" — belum diajukan/disepakati.)

- Cart + checkout lengkap di app kasir: ketuk produk → keranjang (qty +/-/hapus/badge), layar `CheckoutScreen` (diskon, metode CASH/QRIS/TRANSFER, uang dibayar, validasi kembalian), simpan via `POST /transactions` (harga & snapshot dari backend). [DONE]
- Alur Bayar → **Payment Success** → **Cetak Struk / Cetak Ulang** via printer Bluetooth; printer gagal tidak menghapus transaksi (sudah aman di backend). [DONE]
- Live verifikasi: `flutter analyze` clean, `flutter test` **10 passed** (cart + model/struk), `flutter build apk --debug` sukses, API live menerima payload app → `POS-20260923-0002` (CASH 2 item, diskon 5.000, kembalian 55.000) status PAID. [DONE]
- Koneksi ke API produktif/bersih: `--dart-define=API_BASE_URL=...` (default `http://10.0.2.2:8000` emulator). [DONE]
  - `ApiClient` normalisasi trailing `/` + **timeout 20 detik**; builtin verifikasi `dart run tool/check_api.dart` memakai `API_BASE_URL` default `http://127.0.0.1:8000`. Bukti: `flutter build apk --debug --dart-define=API_BASE_URL=http://192.168.1.50:8000` sukses; `check_api.dart` → health/login/products 200.
- Sinkronisasi SQLite offline → RS: bayar saat offline masuk antrian `pending_transactions` (snapshot nama+harga lokal), `PaymentSuccess` offline, **auto-sync & tombol sync** saat online (status PENDING/SYNCED/FAILED, ulang/hapus item gagal). [DONE]
  - Deps: `sqflite` + `path` (runtime), `sqflite_common_ffi` (test). File: `services/offline_transaction_store.dart`, `services/transaction_sync_service.dart`, `models/pending_transaction.dart`, `screens/pending_transactions_screen.dart`, `SyncNotifier` di `providers.dart`; checklist badge di POS.
  - Verifikasi: `flutter analyze` clean, `flutter test` **19 passed** (7 sync/offline + 2 ApiClient), `flutter build apk --debug` (3x, termasuk --dart-define) sukses.
  - Catatan jujur: fallback offline diuji via unit test dengan `SocketException` (sitah gagal koneksi) + `POST /transactions` live ke backend (POS-20260923-0002) karena alur offline replays body yang sama; belum diuji di perangkat Android offline nyata.
- Push notifikasi / pending order (jika disepakati).

## PHASE 8 — Fitur Lanjutan [IN PROGRESS]

- Profil toko (nama & alamat di struk dikonfigurasi dari dashboard) **DONE**:
  - Backend: model `store_profile` singleton id=1, `GET` (auth) / `PUT` (OWNER) `/api/v1/store-profile`; migrasi alembic `a1b2c3d4e5f6`; test **56 passed** (7 store profile).
  - Web: `StoreProfilePage.tsx` + zustand store; struk POS dinamis; `npm run lint`/`build` sukses.
  - Mobile: model + repo + cache `SessionStore` + `StoreProfileNotifier` (load saat login) → `ReceiptService` dinamis; `flutter analyze` clean, `flutter test` **24 passed** (4 store profile), `flutter build apk --debug` sukses.
  - Live E2E web: GET → PUT ("Aroma Kopi Nusantara") → GET ulang persist. Cetak fisik tetap perlu verifikasi manual.
- Skenario printer: Wi-Fi/network, logo, QR/barcode di struk.
- Audit trail lengkap + export laporan (CSV/PDF) **DONE**:
  - Backend: `AuditLog` (tabel sudah ada sejak migrasi `3ed605c47695`) kini diinstrumentasi — `auth.login`, `transaction.create/cancel` (sudah), `product.create/update/delete`, `category.create/update/delete`, `store_profile.update`, `report.csv/pdf`. `AuditService` (filter action/entity/user/tanggal/q + pagination), `GET /audit-logs` OWNER-only.
  - Backend: `ReportService` + `GET /reports/transactions.csv` & `transactions.pdf` (filter tanggal/metode/status, OWNER-only) memakai reportlab 5.0.1 (ditambah ke requirements).
  - Test: pytest **66 passed** (+4 audit, +6 reports). Web: halaman Audit Trail `/audit` (filter aksi/entitas/tanggal) + tombol Export CSV/PDF di Transaksi (hanya OWNER); lint & build sukses. Live E2E via proxy web: audit total=12 (login ter-klaim), CSV 200, PDF 200.
- Deploy backend (gunicorn/uvicorn + nginx) & build produksi Web APK.

## Audit Keamanan (Ronde 1–3) [DONE]

Pengerasan keamanan di luar roadmap fitur, dikerjakan bertahap (semua teruji):

- **Audit awal**: `efff7cb` / `62474ce` / `b2a7df9` — rate limit login, guard JWT produksi, clamp `created_at`, `local_ref` replay 409, export cap, header CSP, `allowBackup=false` Android, refresh *network-aware*, idempotensi web, user management (web+API), tagging kasir antrian offline.
- **Ronde 2** (`b5451e0`): refresh path mobile, `local_ref` stabil pada reset line offline, `ENVIRONMENT` fail-closed, anti username-enumeration (dummy bcrypt), validasi upload **magic bytes**, web logout race & retry (single-flight refresh).
- **Ronde 3** (`4ac4405`): perbaikan duplikasi checkout offline (notifier & `PopScope`), filter sinkronisasi per-kasir, endpoint `/api/v1/auth/*` bebas dari logout-401, throttle login adil (hanya kegagalan + eviction), **rotasi refresh atomik** + pencabutan semua saat ganti password, kunci baris owner sebelum mutasi role/is_active, `create_product` membersihkan file bila gagal, dedup `local_ref` global, guard path traversal hapus gambar, refresh web tanpa logout paksa + guard `/` per role + clamp diskon/uang dibayar + pesan error login spesifik.
- Migrasi baru pada ronde audit: `b7c8d9e0a1b2` (transactions.local_ref), `d4f5c6b7e809` (refresh_tokens).
- Test terkini: pytest **96 passed**; mobile `flutter test` **24 passed**; web lint + build sukses. Detail kontrol di `docs/arsitektur.md` → Keamanan.

## Catatan Roadmap

- Setiap features wajib diuji (pytest backend, widget test Flutter, uji manual via live check) sebelum dinyatakan selesai.
- Jangan meng-claim sukses tanpa verifikasi aktual.
- Kondisi test **terkini** (pembaruan dari angka historis per fase): backend **96 passed** di `backend/` via `.\.venv\Scripts\python.exe -m pytest -q`, mobile **24 passed** via `flutter test`. Angka per-fase di atas adalah kondisi saat fase itu ditutup.