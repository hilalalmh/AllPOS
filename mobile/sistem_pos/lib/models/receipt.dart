class ReceiptItem {
  const ReceiptItem({
    required this.productName,
    required this.quantity,
    required this.price,
    required this.subtotal,
    this.note,
  });

  final String productName;
  final int quantity;
  final num price;
  final num subtotal;
  final String? note;

  factory ReceiptItem.fromJson(Map<String, dynamic> json) => ReceiptItem(
        productName: json['product_name'] as String,
        quantity: json['quantity'] as int,
        price: json['price'] as num,
        subtotal: json['subtotal'] as num,
        note: json['note'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'product_name': productName,
        'quantity': quantity,
        'price': price,
        'subtotal': subtotal,
        'note': note,
      };
}

class ReceiptData {
  const ReceiptData({
    required this.invoiceNumber,
    required this.cashierName,
    required this.items,
    required this.subtotal,
    required this.discount,
    required this.total,
    required this.paidAmount,
    required this.changeAmount,
    required this.paymentMethod,
    required this.createdAt,
  });

  final String invoiceNumber;
  final String cashierName;
  final List<ReceiptItem> items;
  final num subtotal;
  final num discount;
  final num total;
  final num paidAmount;
  final num changeAmount;
  final String paymentMethod;
  final String createdAt;

  factory ReceiptData.fromJson(Map<String, dynamic> json) => ReceiptData(
        invoiceNumber: json['invoice_number'] as String,
        cashierName: json['cashier_name'] as String,
        items: (json['items'] as List<dynamic>)
            .map((e) => ReceiptItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        subtotal: json['subtotal'] as num,
        discount: json['discount'] as num,
        total: json['total'] as num,
        paidAmount: json['paid_amount'] as num,
        changeAmount: json['change_amount'] as num,
        paymentMethod: json['payment_method'] as String,
        createdAt: json['created_at'] as String,
      );

  Map<String, dynamic> toJson() => {
        'invoice_number': invoiceNumber,
        'cashier_name': cashierName,
        'items': items.map((e) => e.toJson()).toList(),
        'subtotal': subtotal,
        'discount': discount,
        'total': total,
        'paid_amount': paidAmount,
        'change_amount': changeAmount,
        'payment_method': paymentMethod,
        'created_at': createdAt,
      };
}