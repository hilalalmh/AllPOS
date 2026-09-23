import 'dart:io';
import 'dart:math';

import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

import 'package:sistem_pos/models/pending_transaction.dart';
import 'package:sistem_pos/models/transaction.dart';
import 'package:sistem_pos/services/api_client.dart';
import 'package:sistem_pos/services/offline_transaction_store.dart';
import 'package:sistem_pos/services/transaction_sync_service.dart';

Map<String, dynamic> _txJson() => {
      'id': 1,
      'invoice_number': 'POS-20260923-0001',
      'cashier_id': 2,
      'subtotal': 36000,
      'discount': 0,
      'total': 36000,
      'payment_method': 'CASH',
      'paid_amount': 40000,
      'change_amount': 4000,
      'status': 'PAID',
      'created_at': '2026-09-23T10:00:00',
      'items': [
        {
          'id': 1,
          'product_id': 3,
          'product_name': 'Es Kopi',
          'price': 18000,
          'quantity': 2,
          'subtotal': 36000,
          'note': null,
        },
      ],
    };

class _FakeApi extends ApiClient {
  _FakeApi({this.failNetwork = false, this.failStatus}) : super(baseUrl: 'http://x');

  final bool failNetwork;
  final int? failStatus;
  int posts = 0;

  @override
  Future<dynamic> post(String path, [Object? body]) {
    posts++;
    if (failNetwork) throw const SocketException('no route to host');
    if (failStatus != null) {
      throw ApiException(failStatus!, 'rejected: ${failStatus!}');
    }
    return Future.value(_txJson());
  }
}

void main() {
  setUpAll(() {
    sqfliteFfiInit();
    databaseFactory = databaseFactoryFfi;
  });

  late Directory tmp;
  late OfflineTransactionStore store;

  setUp(() async {
    tmp = await Directory.systemTemp.createTemp('pos_test_');
    store = OfflineTransactionStore(
      databasePath: '${tmp.path}/pos_${Random().nextInt(1 << 31)}.db',
    );
  });

  tearDown(() async {
    try {
      await tmp.delete(recursive: true);
    } catch (_) {}
  });

  List<CartItemInput> sampleItems() => const [
        CartItemInput(
          productId: 3,
          quantity: 2,
          productName: 'Es Kopi',
          price: 18000,
        ),
        CartItemInput(
          productId: 5,
          quantity: 1,
          productName: 'Roti Bakar',
          price: 15000,
        ),
      ];

  TransactionSyncService buildService(ApiClient api) =>
      TransactionSyncService(api: api, store: store);

  test('online berhasil tanpa fallback offline', () async {
    final service = buildService(_FakeApi());
    final result = await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'CASH',
      paidAmount: 100000,
      discount: 5000,
    );

    expect(result.isOnline, isTrue);
    expect(result.reference, 'POS-20260923-0001');
    expect(result.total, 36000);
    expect(await store.count(), 0);
  });

  test('gagal koneksi menyimpan antrian offline + PayResult offline', () async {
    final service = buildService(_FakeApi(failNetwork: true));
    final result = await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'CASH',
      paidAmount: 100000,
      discount: 5000,
    );

    expect(result.isOffline, isTrue);
    expect(result.reference, startsWith('LOCAL-'));
    expect(result.items.length, 2);
    expect(result.changeAmount, 54000);

    final pending = await store.all();
    expect(pending.length, 1);
    expect(pending.single.status, 'PENDING');
    expect(pending.single.localRef, result.reference);
    expect(pending.single.items.length, 2);
  });

  test('kesalahan bisnis (4xx) tidak jatuh ke offline', () async {
    final service = buildService(_FakeApi(failStatus: 422));
    await expectLater(
      service.createWithFallback(
        items: sampleItems(),
        paymentMethod: 'CASH',
        paidAmount: 100000,
        discount: 0,
      ),
      throwsA(isA<ApiException>()),
    );
    expect(await store.count(), 0);
  });

  test('syncAll menyinkronkan antrian dan menandai sycned', () async {
    final service = buildService(_FakeApi(failNetwork: true));
    await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'QRIS',
      paidAmount: 45500,
      discount: 0,
    );

    final syncService = buildService(_FakeApi());
    final outcome = await syncService.syncAll();

    expect(outcome.synced, 1);
    final pending = await store.all();
    expect(pending.single.isSynced, isTrue);
    expect(pending.single.invoiceNumber, 'POS-20260923-0001');
  });

  test('syncAll saat offline tetap PENDING (transien tidak dihitung gagal)', () async {
    final service = buildService(_FakeApi(failNetwork: true));
    await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'CASH',
      paidAmount: 50000,
      discount: 0,
    );

    final outcome = await service.syncAll();
    expect(outcome.synced, 0);
    // Gangguan jaringan bersifat transien: tidak dihitung sebagai kegagalan
    // permanen (failed), baris tetap PENDING untuk di-replay berikutnya.
    expect(outcome.failed, 0);
    expect(outcome.error, isNotNull);
    final pending = await store.all();
    expect(pending.single.isPending, isTrue);
  });

  test('syncAll 4xx menandai FAILED yang bisa diulang', () async {
    final service = buildService(_FakeApi(failNetwork: true));
    final result = await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'CASH',
      paidAmount: 50000,
      discount: 0,
    );
    final id = (await store.all()).single.id!;

    final syncService = buildService(_FakeApi(failStatus: 422));
    final outcome = await syncService.syncAll();
    expect(outcome.synced, 0);

    final failed = await store.all();
    expect(failed.single.isFailed, isTrue);
    expect(failed.single.error, isNotNull);

    await store.resetToPending(id);
    expect((await store.all()).single.isPending, isTrue);
    expect(result.reference, isNotEmpty);
  });

  test('401 di checkout jatuh ke antrian offline (sesi habis saat bayar)', () async {
    final service = buildService(_FakeApi(failStatus: 401));
    final result = await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'CASH',
      paidAmount: 100000,
      discount: 0,
    );
    // Pembayaran tunai sudah diterima di kas: 401 (sesi habis di tengah
    // transaksi) tidak boleh menghilangkan penjualan — antrikan offline.
    expect(result.isOffline, isTrue);
    expect((await store.all()).single.status, 'PENDING');
  });

  test('syncAll 401 tidak menandai FAILED permanen (tetap PENDING)', () async {
    final service = buildService(_FakeApi(failNetwork: true));
    await service.createWithFallback(
      items: sampleItems(),
      paymentMethod: 'CASH',
      paidAmount: 50000,
      discount: 0,
    );

    final syncService = buildService(_FakeApi(failStatus: 401));
    final outcome = await syncService.syncAll();
    expect(outcome.synced, 0);
    expect(outcome.failed, 0);
    expect(outcome.error, isNotNull);
    final pending = await store.all();
    // Sesuai desain untuk sesi 401: tetap PENDING, bukan FAILED, agar bisa
    // di-replay setelah login ulang.
    expect(pending.single.isPending, isTrue);
  });

  test('store CRUD dasar', () async {
    final pending = await store.insert(
      PendingTransaction(
        localRef: 'LOCAL-1',
        items: sampleItems(),
        paymentMethod: 'CASH',
        subtotal: 51000,
        discount: 1000,
        total: 50000,
        paidAmount: 60000,
        changeAmount: 10000,
        createdAtLocal: DateTime.now(),
        status: 'PENDING',
      ),
    );
    expect(pending.id, isNotNull);
    expect(await store.count(), 1);
    expect((await store.all()).single.items.length, 2);

    await store.remove(pending.id!);
    expect(await store.count(), 0);
  });
}
