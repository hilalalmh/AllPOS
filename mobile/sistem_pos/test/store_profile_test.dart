import 'package:flutter_test/flutter_test.dart';
import 'package:sistem_pos/models/store_profile.dart';

void main() {
  group('StoreProfile model', () {
    test('fromJson memakai field backend (store_name/address/phone/footer)', () {
      final p = StoreProfile.fromJson({
        'store_name': 'Aroma Kopi Nusantara',
        'address': 'Jl. Rajawali No. 21, Jakarta',
        'phone': '0812-9000-1234',
        'footer': 'TERIMA KASIH ~ SAMPAI JUMPA!',
      });

      expect(p.storeName, 'Aroma Kopi Nusantara');
      expect(p.address, 'Jl. Rajawali No. 21, Jakarta');
      expect(p.phone, '0812-9000-1234');
      expect(p.footer, 'TERIMA KASIH ~ SAMPAI JUMPA!');
    });

    test('fromJson memberi default aman saat field kosong', () {
      final p = StoreProfile.fromJson({});
      expect(p.storeName, StoreProfile.defaultProfile.storeName);
      expect(p.address, '');
      expect(p.phone, '');
      expect(p.footer, StoreProfile.defaultProfile.footer);
    });

    test('toJson round-trip', () {
      final src = StoreProfile(
        storeName: 'Kedai Kopi Tetangga',
        address: 'Jl. Melati No. 12',
        phone: '021-1234',
        footer: 'TERIMA KASIH',
      );
      final restored = StoreProfile.fromJson(src.toJson());
      expect(restored.storeName, src.storeName);
      expect(restored.address, src.address);
      expect(restored.phone, src.phone);
      expect(restored.footer, src.footer);
    });

    test('defaultProfile menyediakan nilai yang dipakai fallback', () {
      expect(StoreProfile.defaultProfile.storeName, 'SISTEM POS');
      expect(
        StoreProfile.defaultProfile.footer,
        'TERIMA KASIH ~ SILAHKAN DATANG KEMBALI',
      );
    });
  });
}