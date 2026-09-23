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
  TransactionSyncService({
    required this.api,
    required this.store,
  });

  final ApiClient api;
  final OfflineTransactionStore store;

  bool _isNetworkError(Object e) =>
      e is SocketException ||
      e is http.ClientException ||
      e is TimeoutException;

  Future<PayResult> createWithFallback({
    required List<CartItemInput> items,
    required String paymentMethod,
    required num paidAmount,
    required num discount,
  }) async {
    final now = DateTime.now();
    final localRef = 'LOCAL-${now.microsecondsSinceEpoch}';
    final subtotal = items.fold<num>(0, (sum, i) => sum + i.subtotal);
    final total = (subtotal - discount).clamp(0, double.infinity);
    final paid = paymentMethod == 'CASH' ? paidAmount : total;
    final change = paymentMethod == 'CASH'
        ? (paid - total).clamp(0, double.infinity)
        : 0;
    try {
      final transaction = await _onlineCreate(
        items,
        paymentMethod,
        paid,
        discount,
        localRef: localRef,
      );
      return PayResult.fromTransaction(transaction);
    } catch (e) {
      if (!_isNetworkError(e)) rethrow;
      final pending = await store.insert(
        PendingTransaction(
          localRef: localRef,
          items: items,
          paymentMethod: paymentMethod,
          subtotal: subtotal,
          discount: discount,
          total: total,
          paidAmount: paid,
          changeAmount: change,
          createdAtLocal: now,
          status: 'PENDING',
        ),
      );
      return PayResult.offline(
        localRef: pending.localRef,
        now: now,
        items: items,
        paymentMethod: paymentMethod,
        subtotal: subtotal,
        discount: discount,
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
  }) async {
    final response = await api.post(
      '/api/v1/transactions',
      {
        'items': [for (final i in items) i.toRequestJson()],
        'payment_method': paymentMethod,
        'paid_amount': paidAmount,
        'discount': discount,
        'local_ref': ?localRef,
      },
    );
    return Transaction.fromJson(response as Map<String, dynamic>);
  }

  Future<SyncOutcome> syncAll() async {
    final pending = await store.all();
    var synced = 0;
    var failed = 0;
    String? firstError;
    for (final item in pending) {
      if (!item.isPending) continue;
      try {
        final transaction = await _onlineCreate(
          item.items,
          item.paymentMethod,
          item.paidAmount,
          item.discount,
          localRef: item.localRef,
        );
        await store.markSynced(item.id!, transaction.invoiceNumber);
        synced++;
      } catch (e) {
        if (e is ApiException && e.statusCode >= 400 && e.statusCode < 500) {
          failed++;
          firstError ??= e.message;
          await store.markFailed(item.id!, e.message);
        } else {
          failed++;
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