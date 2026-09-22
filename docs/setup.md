# Setup, Konfigurasi & Operasional — Sistem POS

Panduan mereproduksi environment dari nol, referensi konfigurasi, skrip, dan operasional harian (backup/restore). Asumsi OS Windows + PowerShell.

## 1. Requirement Versi

| Komponen | Versi | Lokasi (bila khusus) |
|----------|-------|-----------|
| Python | 3.14 | `c:\Python314` (venv di `backend\.venv`) |
| Node.js / npm | 24.11.1 / 10.9.2 | - |
| PostgreSQL | 17.11 (service `postgresql-x64-17`) | - |
| Flutter | 3.47.5 stable | `D:\flutter` |
| JDK | Temurin 17 | `C:\Program Files\Eclipse Adoptium\jdk-17.0.20.101-hotspot` |
| Android SDK | platform 35 & 36, build-tools 35.0.0 | `D:\Android\sdk` |

Env vars user permanen: `ANDROID_HOME=D:\Android\sdk`, `ANDROID_SDK_ROOT=D:\Android\sdk`, `JAVA_HOME=<JDK 17>`; PATH berisi `D:\flutter\bin`, `%JAVA_HOME%\bin`, `%ANDROID_SDK_ROOT%\platform-tools`.

Verifikasi: `flutter doctor` (Android toolchain harus hijau).

## 2. Setup Database

```sql
CREATE ROLE pos_user LOGIN PASSWORD 'pos_password';
CREATE DATABASE sistem_pos OWNER pos_user;
CREATE DATABASE sistem_pos_test OWNER pos_user;   -- dipakai pytest
```

Migrasi skema + seed:

```bash
cd backend
.venv\Scripts\activate.bat
pip install -r requirements.txt
python -m alembic upgrade head
python -m app.services.seed
```

## 3. Drive Project

```bash
cd backend && .venv\Scripts\activate.bat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload     # backend :8000

cd web/sistem_pos_dashboard
npm install
npm run dev                                                            # web :5173 (proxy /api → :8000)

cd mobile/sistem_pos
flutter pub get
flutter run                                                            # emulator/HP Android
```

Atau gunakan skrip di `scripts/` (lihat bagian 6).

## 4. Referensi `.env` (backend)

File: `backend/.env` (jangan di-commit). Semua key opsional (punya default di `app/core/config.py`, kecuali `DATABASE_URL`/`JWT_SECRET` yang wajib diubah untuk produksi).

| Key | Default | Keterangan |
|-----|---------|-----------|
| `DATABASE_URL` | `postgresql+psycopg://pos_user:pos_password@localhost:5432/sistem_pos` | Koneksi SQLAlchemy (psycopg 3) |
| `JWT_SECRET` | `change-me-in-production` | **WAJIB ganti untuk produksi** |
| `JWT_ALGORITHM` | `HS256` | Algoritma JWT |
| `JWT_EXPIRES_MINUTES` | `60` | Umur access token |
| `JWT_REFRESH_EXPIRES_DAYS` | `7` | Umur refresh token |
| `SEED_ADMIN_PASSWORD` | `admin123` | Password user `owner` (seed) |
| `CORS_ORIGINS` | `["http://localhost:5173","http://127.0.0.1:5173"]` | Origin web (parsing JSON) |
| `APP_NAME` | `Sistem POS API` | Nama tampilan API |
| `DEBUG` | `false` | Mode debug FastAPI |
| `UPLOAD_DIR` | `uploads` | Folder gambar produk |
| `MAX_UPLOAD_SIZE` | `2097152` | Maks 2 MB |
| `ALLOWED_IMAGE_TYPES` | jpeg/png/webp | Tipe gambar |

Test (pytest) memakai `sistem_pos_test` via `tests/conftest.py` (dependency override), **bukan** dari `.env`.

## 5. Konfigurasi Mobile (Flutter)

- `API_BASE_URL` lewat `--dart-define`, default `http://10.0.2.2:8000` (emulator). Ganti untuk HP fisik pribadi ke IP LAN komputer: `http://192.168.x.x:8000`.
- Build APK debug: `flutter build apk --debug`. Build dengan base URL khusus: tambahkan `--dart-define=API_BASE_URL=...`.
- **Penting:** project mobile dikunci **AGP 8.11.1 + Gradle 8.14** (`android/settings.gradle.kts`, `gradle-wrapper.properties`) dan `kotlin.incremental=false` di `android/gradle.properties`. JANGAN naikkan ke AGP 9/Gradle 9 (plugin printer lama tidak kompatibel). Plugin `bluetooth_print` = salinan ter-patch di `third_party/`, dikunci via `dependency_overrides` di `pubspec.yaml`.

## 6. Skrip Launcher (`scripts/`)

| Skrip | Fungsi |
|-------|--------|
| `start_backend.cmd` | Jalankan backend (`--reload`) di jendela hidden; bertahan di luar tool. |
| `restart_backend.cmd` | Matikan & hidupkan ulang backend. |
| `run_backend.cmd` | Jalankan backend di jendela terlihat (tanpa hidden). |
| `start_web.cmd` | Jalankan Vite dev server (hidden). |
| `start_dev.cmd` | Jalankan backend + web sekaligus (2 jendela minimized). |

Catatan: saat bekerja lewat tool/shell yang membunuh process tree, gunakan `*.cmd` yang memanggil `Start-Process` hidden agar backend/web bertahan.

## 7. Backup & Restore Database (PostgreSQL)

Jalankan saat service PostgreSQL aktif (`Get-Service postgresql-x64-17`).

```powershell
# Backup DB utama ke file dump
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -U pos_user -d sistem_pos -F c -f "D:\backup\sistem_pos_$(Get-Date -Format yyyyMMdd_HHmm).dump"

# Restore ke DB kosong (buat DB dulu: sistem_pos_restore OWNER pos_user)
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -U pos_user -d sistem_pos_restore "D:\backup\sistem_pos_....dump"

# Setelah restore, cek: python -m alembic current di backend, lalu python -m app.services.seed (idempotent)
```

Praktik baik:
- Backup sebelum eksperimen besar / perubahan migrasi.
- Simpan dump di luar folder repo.
- `.env` + `JWT_SECRET` di-backup terpisah (bukan di git), karena tanpanya token tidak bisa diverifikasi.

## 8. Catatan Deployment (Produksi — belum dilakukan)

- Backend: jalankan dengan gunicorn (`gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`) + reverse proxy (nginx) yang menyajikan `/uploads` dan header CORS. Nyalakan `DEBUG=false`, ganti `JWT_SECRET` dan password DB.
- Web: `npm run build` → hasil `dist/` disajikan statis oleh nginx; proxy `/api` ke backend.
- Mobile: build release (`flutter build apk --release`) dengan keystore sendiri + `--dart-define=API_BASE_URL=https://...`.
- Backup `.env` produksi aman; buat dump DB terjadwal.

## 9. Siklus Verifikasi Cepat (cek tidak kehilangan fungsi)

| Cek | Perintah | Harapan |
|-----|----------|---------|
| Backend hidup | `Invoke-RestMethod http://localhost:8000/api/v1/health` | `status=ok`, `database=ok` |
| Backend test | `cd backend && .\.venv\Scripts\python.exe -m pytest tests -q` | semua pass (saat ini 49) |
| Web build | `cd web/sistem_pos_dashboard && npm run lint && npm run build` | sukses |
| Flutter analyze | `cd mobile/sistem_pos && flutter analyze` | No issues |
| Flutter test | `flutter test` | pass |
| Dart → API | `cd mobile/sistem_pos && dart run tool/check_api.dart` | health/login/products 200 |
| E2E proxy web | login → transaksi → summary lewat `:5173/api/v1` | 200 & data update |