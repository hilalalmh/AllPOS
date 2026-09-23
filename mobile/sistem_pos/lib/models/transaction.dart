import '../models/receipt.dart';
import '../utils/date_time.dart';

class CartItemInput {
  const CartItemInput({
    required this.productId,
    required this.quantity,
    required this.productName,
    required this.price,
    this.note,
  });

  final int productId;
  final int quantity;
  final String productName;
  final num price;
  final String? note;

  num get subtotal => price * quantity;

  Map<String, dynamic> toRequestJson() => {
        'product_id': productId,
        'quantity': quantity,
      };

  Map<String, dynamic> toSnapshotJson() => {
        'product_id': productId,
        'quantity': quantity,
        'product_name': productName,
        'price': price,
        'note': note,
      };

  factory CartItemInput.fromSnapshotJson(Map<String, dynamic> json) =>
      CartItemInput(
        productId: json['product_id'] as int,
        quantity: json['quantity'] as int,
        productName: json['product_name'] as String,
        price: json['price'] as num,
        note: json['note'] as String?,
      );
}

class TransactionItem {
  const TransactionItem({
    required this.id,
    required this.productId,
    required this.productName,
    required this.price,
    required this.quantity,
    required this.subtotal,
    this.note,
  });

  final int id;
  final int productId;
  final String productName;
  final num price;
  final int quantity;
  final num subtotal;
  final String? note;

  factory TransactionItem.fromJson(Map<String, dynamic> json) =>
      TransactionItem(
        id: json['id'] as int,
        productId: json['product_id'] as int,
        productName: json['product_name'] as String,
        price: json['price'] as num,
        quantity: json['quantity'] as int,
        subtotal: json['subtotal'] as num,
        note: json['note'] as String?,
      );
}

class Transaction {
  const Transaction({
    required this.id,
    required this.invoiceNumber,
    required this.cashierId,
    required this.subtotal,
    required this.discount,
    required this.total,
    required this.paymentMethod,
    required this.paidAmount,
    required this.changeAmount,
    required this.status,
    required this.createdAt,
    required this.items,
  });

  final int id;
  final String invoiceNumber;
  final int cashierId;
  final num subtotal;
  final num discount;
  final num total;
  final String paymentMethod;
  final num paidAmount;
  final num changeAmount;
  final String status;
  final DateTime createdAt;
  final List<TransactionItem> items;

  factory Transaction.fromJson(Map<String, dynamic> json) => Transaction(
        id: json['id'] as int,
        invoiceNumber: json['invoice_number'] as String,
        cashierId: json['cashier_id'] as int,
        subtotal: json['subtotal'] as num,
        discount: json['discount'] as num,
        total: json['total'] as num,
        paymentMethod: json['payment_method'] as String,
        paidAmount: json['paid_amount'] as num,
        changeAmount: json['change_amount'] as num,
        status: json['status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        items: (json['items'] as List<dynamic>)
            .map((e) => TransactionItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  String get createdAtDisplay {
    final local = createdAt.toLocal();
    return formatDateIndo(local);
  }

  ReceiptData toReceipt({required String cashierName}) => ReceiptData(
        invoiceNumber: invoiceNumber,
        cashierName: cashierName,
        items: [
          for (final item in items)
            ReceiptItem(
              productName: item.productName,
              quantity: item.quantity,
              price: item.price,
              subtotal: item.subtotal,
              note: item.note,
            ),
        ],
        subtotal: subtotal,
        discount: discount,
        total: total,
        paidAmount: paidAmount,
        changeAmount: changeAmount,
        paymentMethod: paymentMethod,
        createdAt: createdAtDisplay,
      );
}

class PayResult {
  const PayResult({
    required this.reference,
    required this.createdAtText,
    required this.paymentMethod,
    required this.subtotal,
    required this.discount,
    required this.total,
    required this.paidAmount,
    required this.changeAmount,
    required this.items,
    this.isOffline = false,
  });

  final String reference;
  final String createdAtText;
  final String paymentMethod;
  final num subtotal;
  final num discount;
  final num total;
  final num paidAmount;
  final num changeAmount;
  final List<ReceiptItem> items;
  final bool isOffline;

  bool get isOnline => !isOffline;

  factory PayResult.fromTransaction(Transaction t) => PayResult(
        reference: t.invoiceNumber,
        createdAtText: t.createdAtDisplay,
        paymentMethod: t.paymentMethod,
        subtotal: t.subtotal,
        discount: t.discount,
        total: t.total,
        paidAmount: t.paidAmount,
        changeAmount: t.changeAmount,
        items: [
          for (final item in t.items)
            ReceiptItem(
              productName: item.productName,
              quantity: item.quantity,
              price: item.price,
              subtotal: item.subtotal,
              note: item.note,
            ),
        ],
        isOffline: false,
      );

  factory PayResult.offline({
    required String localRef,
    required DateTime now,
    required List<CartItemInput> items,
    required String paymentMethod,
    required num subtotal,
    required num discount,
    required num total,
    required num paidAmount,
  }) =>
      PayResult(
        reference: localRef,
        createdAtText: formatDateIndo(now),
        paymentMethod: paymentMethod,
        subtotal: subtotal,
        discount: discount,
        total: total,
        paidAmount: paidAmount,
        changeAmount: paymentMethod == 'CASH'
            ? (paidAmount - total).clamp(0, double.infinity)
            : 0,
        items: [
          for (final item in items)
            ReceiptItem(
              productName: item.productName,
              quantity: item.quantity,
              price: item.price,
              subtotal: item.subtotal,
              note: item.note,
            ),
        ],
        isOffline: true,
      );

  ReceiptData toReceipt({required String cashierName}) => ReceiptData(
        invoiceNumber: reference,
        cashierName: cashierName,
        items: items,
        subtotal: subtotal,
        discount: discount,
        total: total,
        paidAmount: paidAmount,
        changeAmount: changeAmount,
        paymentMethod: paymentMethod,
        createdAt: createdAtText,
      );
}