import 'dart:convert';

import '../models/transaction.dart';

class PendingTransaction {
  const PendingTransaction({
    required this.localRef,
    required this.items,
    required this.paymentMethod,
    required this.subtotal,
    required this.discount,
    required this.total,
    required this.paidAmount,
    required this.changeAmount,
    required this.createdAtLocal,
    required this.status,
    this.cashierId,
    this.id,
    this.invoiceNumber,
    this.error,
    this.syncedAt,
  });

  final int? id;
  final String localRef;
  final List<CartItemInput> items;
  final String paymentMethod;
  final num subtotal;
  final num discount;
  final num total;
  final num paidAmount;
  final num changeAmount;
  final DateTime createdAtLocal;
  final int? cashierId;
  final String status;
  final String? invoiceNumber;
  final String? error;
  final DateTime? syncedAt;

  bool get isSynced => status == 'SYNCED';
  bool get isFailed => status == 'FAILED';
  bool get isPending => status == 'PENDING';

  factory PendingTransaction.fromRow(Map<String, dynamic> row) =>
      PendingTransaction(
        id: row['id'] as int,
        localRef: row['local_ref'] as String,
        items: _decodeItems(row['items_json'] as String),
        paymentMethod: row['payment_method'] as String,
        subtotal: row['subtotal'] as num,
        discount: row['discount'] as num,
        total: row['total'] as num,
        paidAmount: row['paid_amount'] as num,
        changeAmount: row['change_amount'] as num,
        createdAtLocal: DateTime.parse(row['created_at_local'] as String),
        cashierId: row['cashier_id'] as int?,
        status: row['status'] as String,
        invoiceNumber: row['invoice_number'] as String?,
        error: row['error'] as String?,
        syncedAt: row['synced_at'] == null
            ? null
            : DateTime.parse(row['synced_at'] as String),
      );

  Map<String, dynamic> toRow() => {
        if (id != null) 'id': id,
        'local_ref': localRef,
        'items_json': jsonEncode([for (final i in items) i.toSnapshotJson()]),
        'payment_method': paymentMethod,
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'paid_amount': paidAmount,
        'change_amount': changeAmount,
        'created_at_local': createdAtLocal.toIso8601String(),
        'cashier_id': cashierId,
        'status': status,
        'invoice_number': invoiceNumber,
        'error': error,
        'synced_at': syncedAt?.toIso8601String(),
      };
}

List<CartItemInput> _decodeItems(String raw) {
  final decoded = jsonDecode(raw) as List<dynamic>;
  return decoded
      .map((e) => CartItemInput.fromSnapshotJson(e as Map<String, dynamic>))
      .toList();
}