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

### Verifikasi status terakhir (terakhir dicek: PHASE 6 2026-09-23)

- Backend `http://localhost:8000` hidup (uvicorn --reload); web `http://localhost:5173` hidup (vite, proxy `/api`).
- `curl http://localhost:8000/api/v1/health` → `{"status":"ok","database":"ok"}`.
- `flutter analyze` → No issues (0). `flutter test` → 3 passed (struk).
- `pytest` (backend) → **49 passed** (termasuk dashboard: summary/sales/best-seller).
- `npm run lint` & `npm run build` (web) → sukses.
- `dart run tool/check_api.dart` (dari `mobile/sistem_pos`) → health 200, login 200, products 200.
- E2E live web: login → transaksi `POS-20260923-0001` → summary dashboard update → kasir 403 dashboard → sukses.
- **Git**: commit pertama dibuat memuat seluruh source (backend+mobile+web+docs+scripts); `.env`, `uploads/`, `.pytest_cache/`, `build`, `node_modules`, `.venv` di-ignore.

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
8. **UUID untuk file upload** dipakai agar nama file unik; validasi ekstensi MIME + ukuran 2 MB; URL disimpan `image_url`.
9. **Transaksi** atomic via satu session DB; pending rollback jika gagal; invoice number unik dengan anti-bentrok loop; `payment_method` enum ditulis sebagai `str` di kolom `String`.

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
- **Streaming/sinkronisasi**: belum ada; SQLite offline adalah PHASE 8.
- **Migrasi DB**: jangan edit migrasi lama yang sudah apply; buat revisi baru (Alembic).

## Status Fase

Lihat `docs/roadmap.md`. Yang sudah selesai: PHASE 1–6. **PHASE 7 (integrasi & offline mobile) berikutnya.**

## Todo Terbuka / Catatan Kecil

- Ganti `APP_NAME`/branding di backend (mis. nama toko) bila perlu.
- Verifikasi manual cetak printer fisik (butuh HP + printer Bluetooth); cetak struk web (58mm) via CSS print sudah jalan.
- Endpoint dashboard baru (RBAC OWNER): `/api/v1/dashboard/summary`, `/sales`, `/best-sellers` — file: `backend/app/routers/dashboard.py`, `backend/app/services/dashboard_service.py`, `backend/app/schemas/dashboard.py`, test `backend/tests/test_dashboard.py`.