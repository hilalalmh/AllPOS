import 'dart:async';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../models/pending_transaction.dart';
import '../models/transaction.dart';
import '../services/api_client.dart';
import '../services/offline_transaction_store.dart';

class SyncOutcome {
  const SyncOutcome({this.synced = 0, this.failed = 0, this.error});

  final int synced;
  final int failed;
  final String? error;
}

class TransactionSyncService {
  TransactionSyncService({required this.api, required this.store});

  final ApiClient api;
  final OfflineTransactionStore store;

  bool _isNetworkError(Object e) =>
      e is SocketException ||
      e is http.ClientException ||
      e is TimeoutException;

  /// Error 5xx bersifat ambigu: server kemungkinan besar sudah mencatat
  /// transaksi tapi respons tidak sampai. Dengan local_ref yang stabil,
  /// antrian offline bisa di-replay dan server men-dedup tanpa duplikasi.
  bool _isAmbiguousError(Object e) {
    if (e is! ApiException) return false;
    return e.statusCode >= 500;
  }

  static num _round2(num value) => (value * 100).round() / 100;

  Future<PayResult> createWithFallback({
    required List<CartItemInput> items,
    required String paymentMethod,
    required num paidAmount,
    required num discount,
    int? cashierId,
    String? localRef,
  }) async {
    final now = DateTime.now();
    // localRef dihasilkan pemanggil (stabil per keranjang checkout) agar
    // retry jaringan/5xx tidak menciptakan transaksi ganda di server.
    final ref = localRef ?? 'LOCAL-${now.microsecondsSinceEpoch}';
    final subtotal = _round2(items.fold<num>(0, (sum, i) => sum + i.subtotal));
    final discountVal = _round2(discount.clamp(0, subtotal));
    final total = _round2((subtotal - discountVal).clamp(0, double.infinity));
    final paid = _round2(paymentMethod == 'CASH' ? paidAmount : total);
    final change = _round2(
      paymentMethod == 'CASH' ? (paid - total).clamp(0, double.infinity) : 0,
    );
    try {
      final transaction = await _onlineCreate(
        items,
        paymentMethod,
        paid,
        discountVal,
        localRef: ref,
        createdAtLocal: now,
      );
      return PayResult.fromTransaction(transaction);
    } catch (e) {
      if (!_isNetworkError(e) && !_isAmbiguousError(e)) rethrow;
      final pending = await store.insert(
        PendingTransaction(
          localRef: ref,
          items: items,
          paymentMethod: paymentMethod,
          subtotal: subtotal,
          discount: discountVal,
          total: total,
          paidAmount: paid,
          changeAmount: change,
          createdAtLocal: now,
          cashierId: cashierId,
          status: 'PENDING',
        ),
      );
      return PayResult.offline(
        localRef: pending.localRef,
        now: now,
        items: items,
        paymentMethod: paymentMethod,
        subtotal: subtotal,
        discount: discountVal,
        total: total,
        paidAmount: paid,
      );
    }
  }

  Future<Transaction> _onlineCreate(
    List<CartItemInput> items,
    String paymentMethod,
    num paidAmount,
    num discount, {
    String? localRef,
    DateTime? createdAtLocal,
  }) async {
    final response = await api.post('/api/v1/transactions', {
      'items': [for (final i in items) i.toRequestJson()],
      'payment_method': paymentMethod,
      'paid_amount': _round2(paidAmount),
      'discount': _round2(discount),
      'local_ref': ?localRef,
      'created_at_local': ?createdAtLocal?.toIso8601String(),
    });
    return Transaction.fromJson(response as Map<String, dynamic>);
  }

  Future<SyncOutcome> syncAll({int? cashierId}) async {
    final pending = await store.all();
    var synced = 0;
    var failed = 0;
    String? firstError;
    for (final item in pending) {
      if (!item.isPending) continue;
      // Antrian offline dimiliki kasir tertentu; jangan sinkronkan punya
      // kasir lain saat berpindah akun di perangkat yang sama.
      if (cashierId != null &&
          item.cashierId != null &&
          item.cashierId != cashierId) {
        continue;
      }
      try {
        final transaction = await _onlineCreate(
          item.items,
          item.paymentMethod,
          item.paidAmount,
          item.discount,
          localRef: item.localRef,
          createdAtLocal: item.createdAtLocal,
        );
        await store.markSynced(item.id!, transaction.invoiceNumber);
        synced++;
      } catch (e) {
        if (e is ApiException && e.statusCode >= 400 && e.statusCode < 500) {
          failed++;
          firstError ??= e.message;
          await store.markFailed(item.id!, e.message);
        } else {
          // Network/5xx bersifat transien: baris tetap PENDING (aman di-replay
          // berkat local_ref), jangan dihitung sebagai kegagalan permanen.
          firstError ??= _message(e);
        }
      }
    }
    return SyncOutcome(synced: synced, failed: failed, error: firstError);
  }

  String _message(Object e) {
    if (e is ApiException) return e.message;
    return e.toString();
  }
}
