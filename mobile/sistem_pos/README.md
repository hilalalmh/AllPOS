# sistem_pos

Aplikasi kasir Flutter untuk Sistem POS (backend berada di akar repo). Fitur:

- Login JWT (FastAPI) + sesi aman (shared_preferences; init gagal → kembali ke login).
- POS: keranjang, diskon, metode `CASH/QRIS/TRANSFER`, uang dibayar & kembalian.
- Cetak struk thermal via Bluetooth (`bluetooth_print`, kertas 58 / 80 mm), tes cetak, cetak ulang.
- Transaksi offline: SQLite queue (`pending_transactions`) + auto-sync; idempoten via `local_ref` (UNIQUE global di backend).

## Struktur Utama

```
lib/
├── core/          # AppConfig (API_BASE_URL via --dart-define, default http://10.0.2.2:8000)
├── models/        # user, product, receipt, store_profile, pending_transaction, transaction
├── services/      # api_client, receipt_service, printer_service, offline_transaction_store, transaction_sync_service
├── repositories/  # session_store, auth_repository, product_repository, store_profile_repository
├── providers/     # Riverpod (auth, printer, produk, sync, store profile)
├── screens/       # splash, login, pos, checkout, payment_success, printer_settings, pending_transactions
└── widgets/
test/              # widget/unit test (24)
tool/check_api.dart  # verifikasi koneksi Dart → backend
third_party/bluetooth_print  # plugin printer di-patch & dikunci via dependency_overrides
```

## Menjalankan

Dari folder ini:

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000   # emulator Android
flutter test
```

Ganti `API_BASE_URL` ke IP LAN/domain produksi untuk HP fisik. Project dikunci **AGP 8.11.1 + Gradle 8.14** (plugin printer lama tidak kompatibel dengan AGP 9/Gradle 9) dan `kotlin.incremental=false`.

Dokumentasi lengkap (arsitektur, API, database, roadmap, setup, memori) ada di folder `docs/` akar repo.