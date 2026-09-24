# Memori Proyek — Sistem POS

Catatan kerja lintas sesi: fakta lingkungan, keputusan, gotcha, alat, dan kondisi terkini. Update file ini saat ada perubahan lingkungan/keputusan besar.

## Lingkungan Developer (Windows)

| Item | Nilai |
|------|-------|
| OS | Windows (pwsh 7) |
| Python | 3.14 — `c:\Python314` (venv: `backend\.venv`) |
| Node / npm | 24.11.1 / 10.9.2 |
| PostgreSQL | 17.11 (service `postgresql-x64-17`) |
| Flutter | 3.47.5 stable — `D:\flutter\bin` |
| JDK | Temurin 17 — `C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot` |
| Android SDK | `D:\Android\sdk` (platforms 35 & 36, build-tools 35.0.0, platform-tools/adb) |
| Backend | `http://localhost:8000` |
| Web dev | `http://localhost:5173` |
| DB | `sistem_pos` (owner `pos_user`), test DB `sistem_pos_test` |
| Upload | dilayani di `/uploads/*` (folder `backend/uploads`) |

Env vars user (permanen): `ANDROID_HOME=D:\Android\sdk`, `ANDROID_SDK_ROOT=D:\Android\sdk`, `JAVA_HOME=<JDK 17>`, PATH berisi `D:\flutter\bin`, JDK `bin`, `D:\Android\sdk\platform-tools`.

### Cara menjalankan

```powershell
# Backend (bertahan lintas tool-call saat dijalankan via Start-Process hidden)
scripts\start_backend.cmd
# Web dashboard
scripts\start_web.cmd
# Dev (semua)
scripts\start_dev.cmd
# Restart backend
scripts\restart_backend.cmd
```

Detail di README.

### Verifikasi status terakhir (terakhir dicek: ronde 3 audit, 2026-09-23)

- Backend `http://localhost:8000` hidup (uvicorn --reload); web `http://localhost:5173` hidup (vite, proxy `/api`).
- `curl http://localhost:8000/api/v1/health` → `{"status":"ok","database":"ok"}`.
- `flutter analyze` → No issues (0). `flutter test` → **26 passed** (struk 4 + cart/transaction 7 + offline sync/store 7 + ApiClient 2 + store profile 4 + printer bluetooth 2).
- `pytest` (backend) → **100 passed** — perintah: `cd backend` lalu `.\\.venv\\Scripts\\python.exe -m pytest -q` (bukan `python` polos; gunakan venv project).
- `npm run lint` & `npm run build` (web) → sukses.
- `dart run tool/check_api.dart` (dari `mobile/sistem_pos`) → health 200, login 200, products 200.
- E2E live web: login → transaksi `POS-20260923-0001` → summary dashboard update → kasir 403 dashboard → sukses.
- **PHASE 7 live**: create transaksi via payload app (`items:[{product_id,quantity}], payment_method, paid_amount, discount`) → `POS-20260923-0002` (CASH, 2 item, diskon 5.000, kembalian 55.000) status PAID; `GET /transactions/{id}` konsisten. `flutter build apk --debug` sukses (3x, termasuk `--dart-define=API_BASE_URL=http://192.168.1.50:8000`). Offline fallback diuji unit test (`SocketException`), belum diuji perangkat offline nyata.
- **Ronde 3 (commit `4ac4405`)**: 9 fix mobile + 7 backend + 11 web; migrasi `d4f5c6b7e809` (refresh_tokens) & `b7c8d9e0a1b2` (local_ref). Test penuh lulus (96/24) setelah perubahan — rincian di `docs/arsitektur.md` (Keamanan).
- **Git**: commit pertama `7ee53f8` memuat seluruh source (backend+mobile+web+docs+scripts); `.env`, `uploads/`, `.pytest_cache/`, `build`, `node_modules`, `.venv`, `*.jks`/`key.properties` tidak di-commit. Audit: `efff7cb`/`62474ce`/`b2a7df9` (audit awal) → `b5451e0` (ronde 2) → `4ac4405` (ronde 3).

## Kredensial dev (seed)

- `owner` / `admin123` (OWNER)
- `kasir1` / `kasir123`, `kasir2` / `kasir123` (KASIR)

## Keputusan Teknis Wajib Diingat

1. **Jangan naikkan AGP ke 9 / Gradle 9** pada `mobile/sistem_pos`. Template Flutter 3.47 baru pakai AGP 9.1.0/Gradle 9.3.1 yang **tidak kompatibel** dengan plugin printer lama (jcenter dihapus di Gradle 9). Project sengaja dikunci **AGP 8.11.1 + Gradle 8.14** (Flutter 3.47 butuh Gradle >= 8.14). Lokasi: `android/settings.gradle.kts`, `android/gradle/wrapper/gradle-wrapper.properties`.
2. **`bluetooth_print` dipatch & dikunci** ke `mobile/sistem_pos/third_party/bluetooth_print` via `dependency_overrides` di `pubspec.yaml`. Jangan revert ke versi pub biasa. Patch: tambah `namespace` di build.gradle, hapus v1-`Registrar`, hapus `jcenter()`, buang buildscript AGP 4.1.2, tetap pakai `gprintersdkv2.jar`.
3. **`kotlin.incremental=false`** di `android/gradle.properties` — cache Kotlin incremental pernah korup → `flutter clean` + rebuild. Tambahkan baris ini kalau build error aneh.
4. **Pendekatan simpan-kondisi**: jika build gagal dengan pesan tentang Gradle/Kotlin/missing class, coba `flutter clean` dulu sebelum ubah konfigurasi.
5. **Buat ulang kunci debug/release APK**: `keytool` untuk keystore `.jks` di `android/app/` bila dibutuhkan rilis; saat ini pakai debug keystore default.
6. **Publisher tidak bisa ditulis** di `build.gradle` app saat pakai `flutter build apk` — gunakan `applicationId` + `signingConfigs` (proyek sudah tersusun untuk debug). Kalau error "D8/Unresolved reference", perbaiki `build.gradle` bukan ganti toolchain.
7. **Token** disimpan di `shared_preferences` (Flutter). Ganti target API prod: `flutter build apk --dart-define=API_BASE_URL=http://...` — default `http://10.0.2.2:8000` (emulator). Client Flutter tidak boleh hardcode secret.
8. **UUID untuk file upload** dipakai agar nama file unik; validasi **magic bytes** MIME (bukan sekadar ekstensi) + ukuran 2 MB; URL disimpan `image_url`. Hapus file memakai guard traversal (`..`, `/`, `\`, leading `.`); `create_product` menghapus file bila simpan metadata gagal.
9. **Transaksi** atomic via satu session DB; pending rollback jika gagal; invoice number unik dengan anti-bentrok loop; `payment_method` enum ditulis sebagai `str` di kolom `String`.
10. **Idempotensi offline**: tiap pembayaran kirim `local_ref` unik (8..64); UNIQUE **global** di `transactions.local_ref`; replay isi sama → transaksi yang sama, isi beda → `409`. `created_at_local` opsional menimpa `created_at` (≤ 5 mnt ke depan).
11. **Refresh token rotasi atomik** (`refresh_tokens.jti` unik): sekali pakai; ganti password mencabut semua refresh token user. Login throttled (`LOGIN_MAX_FAILURES`/`LOGIN_LOCKOUT_MINUTES`) — hanya kegagalan yang dihitung.
12. **`ENVIRONMENT`** default `production` (fail-closed): start ditolak bila `JWT_SECRET` lemah/<32 karakter atau seed `admin123`. Set `ENVIRONMENT=development`/`test` saat dev.
13. **Baca `docs/arsitektur.md` (Keamanan) + `docs/roadmap.md` (Audit Keamanan)** sebelum menambah fitur yang menyentuh auth/upload/transaksi — banyak keputusan keamanan ronde 2–3 tersimpan di situ.

## Struktur Repo Terkini

```
AllPOS/
├── backend/        # FastAPI (.venv, app, alembic, tests, requirements.txt)
│   ├── app/        # core/, models/, schemas/, repositories/, services/, routers/
│   └── alembic/
├── mobile/         # aplikasi kasir Flutter
│   └── sistem_pos/ # lib/, third_party/bluetooth_print, test/, tool/check_api.dart
├── scripts/        # *.cmd launcher Windows
├── web/            # dashboard React + Vite
├── docs/           # dokumentasi ini + arsitektur/api/database/roadmap
└── README.md
```

## Gotcha & Pelajaran

- **OS Windows / tool**: command shell bash (dipakai tool) mem-kill process tree — jangan menjalankan backend langsung via `bash tool` kalau mau tetap hidup; gunakan `scripts\start_backend.cmd` (Start-Process hidden) supaya bertahan lintas tool-call.
- **Permission Windows**: saat install JDK/Android SDK via winget perlu akun lokal & bisa `sudo`/admin; sudah berhasil.
- **Flutter**: `flutter build apk --debug` butuh context yang lama (gradle download pertama); jika `Downgrade Android Gradle plugin` muncul, cek agrément versi di `settings.gradle.kts` bukan di `pubspec`.
- **Printer Bluetooth**: plugin `bluetooth_print` tidak meng-Ekspor model `BluetoothDevice`/`LineText`; impor via `package:bluetooth_print/bluetooth_print_model.dart`. Tidak ada `printBytes` — pakai `printReceipt(config, lines)` & `printTest()`.
- **Struk**: `cols` 32 untuk 58mm, 48 untuk 80mm; wajib `LineText(type: LineTextType.WIDTH, size:1)` setelah teks agar wrap; hindari simbol non-ASCII terlalu panjang (terpotong printer).
- **API uang**: Pydantic serializer `Decimal -> float`; mobile menampilkan `Rp 36.000,00` (id_ID).
- **Streaming/push notifikasi**: belum ada (opsi PHASE 8). SQLite offline **sudah** diimplementasikan di PHASE 7 (queue `pending_transactions` + auto-sync, idempoten via `local_ref`).
- **Migrasi DB**: jangan edit migrasi lama yang sudah apply; buat revisi baru (Alembic).
- **pytest**: jalankan **harus** lewat venv project — `cd backend` lalu `.\.venv\Scripts\python.exe -m pytest -q`. `python -m pytest` polos bisa memakai interpreter lain (mismatch deps).
- **dart format**: `flutter format` tidak ada; pakai `D:\flutter\bin\cache\dart-sdk\bin\dart.exe format`. Perhatian: dart format menormalkan **seluruh** file dengan gaya baru — setelah format, revert file yang tidak diedit (hanya lanjutkan file yang benar-benar diubah).
- **JsonBackend/psycopg**: DB pakai psycopg 3 (`postgresql+psycopg://`).

## Status Fase

Lihat `docs/roadmap.md`. Yang sudah selesai: PHASE 1–6, **PHASE 7** (cart+checkout+payment success+cetak struk, offline SQLite queue+sync, base URL via `--dart-define`, idempoten `local_ref`), **PHASE 8 (sebagian)** (store profile backend+web+mobile, audit trail + export laporan CSV/PDF), dan **Audit Keamanan Ronde 1–3** (commit `b5451e0`, `4ac4405`). Tersisa: verifikasi manual perangkat Android + printer fisik, barcode/QR & logo struk, deploy produksi, build APK release.

## Todo Terbuka / Catatan Kecil

- **Audit Keamanan RONDE 3 SELESAI (commit `4ac4405`)**: 9 fix mobile (M1 checkout duplikat — notifier ditangkap sebelum `await`, `cartNotifier.clear()` setelah result, reload pending saat offline, `PopScope`; M2 filter sync per-kasir; M3 `/api/v1/auth/*` bebas logout-401; M5 login rollback saat `/me` gagal; M7 init sesi aman; M8 flag tercetak hanya jika error printer null; M11 logout async; M14 network/5xx tetap PENDING), 7 backend (B1 refresh atomik; B2 throttle adil; B3 lock owner; B4 create_product bersih; B5 dedup local_ref global; B7 revoke saat ganti password; B10 guard traversal), 11 web (W1-W5 refresh tanpa logout paksa + generasi + retry idempoten; W4 pesan login spesifik; W5 guard `/` OWNER; W6 clamp diskon/uang; W7 detail server; W10/store-profile; W11 error kategori). Lega: semua jalur tetap hijau (pytest 96, flutter 24, web lint/build).
- **Audit Keamanan RONDE 2 SELESAI (commit `b5451e0`)**: refresh path mobile, `local_ref` stabil, `ENVIRONMENT` fail-closed, dummy bcrypt (anti-enumeration), magic-byte upload, web logout race & retry single-flight.
- **PHASE 8 audit + export LAPORAN SELESAI**: Backend instrumentasi `AuditLog` (`services/audit_service.py` `record_audit` + `AuditService.list_logs`), router `GET /audit-logs` OWNER (filter action/entity/user/tanggal/q, pagination); report `ReportService` + `GET /reports/transactions.csv` & `.pdf` OWNER (reportlab 5.0.1 → requirements). pytest **100 passed**. Web: `AuditTrailPage` `/audit` + tombol Export CSV/PDF di `TransactionsPage` (hanya OWNER), lint+build sukses; live E2E via proxy web: audit total=12, CSV 200, PDF 200 (file: `backend/app/routers/audit.py`, `reports.py`, `schemas/audit.py`, `tests/test_audit.py`, `tests/test_reports.py`; web `services/audit.ts`, `pages/AuditTrailPage.tsx`).
- **PHASE 8 store profile SELESAI**: Backend `store_profiles` singleton id=1 (`GET` auth / `PUT` OWNER `/api/v1/store-profile`), migrasi alembic `a1b2c3d4e5f6` jalan live. Web: `StoreProfilePage` (OWNER) + zustand `storeProfileStore`; `ReceiptTicket` di `PosPage` kini dinamis, lint+build sukses, live E2E GET→PUT→persist ("Aroma Kopi Nusantara" — DB live berisi nilai ini). Mobile: `models/store_profile.dart`, `repositories/store_profile_repository.dart`, cache `SessionStore` (`store.profile`), `StoreProfileNotifier` (load saat konstruksi & saat login sukses) di `providers.dart` → `receiptServiceProvider` membaca profil (fallback `StoreProfile.defaultProfile` = "SISTEM POS"), `flutter analyze` clean + `flutter test` **26 passed** + `flutter build apk --debug` sukses. Sisa: cetak fisik & offline nyata.
- **PHASE 7 selesai seluruh fitur kodenya**; sisa hanya uji fisik. `ApiClient` punya `timeout` default 20 detik & memangkas `/` akhir `API_BASE_URL` (test `test/api_client_test.dart`). Build produksi: `flutter build apk --release --dart-define=API_BASE_URL=https://...`.
- Offline SQLite: `services/offline_transaction_store.dart` (SQLite `pending_transactions`), `services/transaction_sync_service.dart` (`createWithFallback` fallback hanya saat error jaringan/timeout; 4xx tidak jatuh offline), `models/pending_transaction.dart`, `models/transaction.dart` (`CartItemInput` + `PayResult`), `screens/pending_transactions_screen.dart`, `SyncNotifier` di `providers.dart`; deps `sqflite`+`path`, dev `sqflite_common_ffi`. Catatan: **jangan `dart run` script yang impor paket yang menyeret Flutter** (sqflite → `package:flutter`) — verifikasi pakai `flutter test`.
- Verifikasi manual cetak printer fisik + uji offline nyata di perangkat (butuh HP Android + printer Bluetooth).
- Endpoint dashboard baru (RBAC OWNER): `/api/v1/dashboard/summary`, `/sales`, `/best-sellers` — file: `backend/app/routers/dashboard.py`, `backend/app/services/dashboard_service.py`, `backend/app/schemas/dashboard.py`, test `backend/tests/test_dashboard.py`.