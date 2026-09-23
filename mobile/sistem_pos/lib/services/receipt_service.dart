import 'package:bluetooth_print/bluetooth_print_model.dart' as bt_model;

import '../models/receipt.dart';
import 'printer_service.dart' show PaperSize;

class StoreInfo {
  const StoreInfo({
    required this.name,
    this.address = '',
    this.phone = '',
    this.footer = 'TERIMA KASIH ~ SILAHKAN DATANG KEMBALI',
  });

  final String name;
  final String address;
  final String phone;
  final String footer;
}

class ReceiptService {
  ReceiptService({
    StoreInfo? store,
    StoreInfo Function()? storeBuilder,
  }) : _storeBuilder = storeBuilder ??
            (() => store ?? const StoreInfo(name: 'SISTEM POS'));

  final StoreInfo Function() _storeBuilder;

  StoreInfo get store => _storeBuilder();

  Map<String, dynamic> printerConfig(PaperSize paper) => {
        'width': paper == PaperSize.mm58 ? 580 : 800,
        'fontsize': 1,
        'charset': 'UTF-8',
      };

  int get _rowWidth => 32;

  List<bt_model.LineText> buildLines(ReceiptData receipt, PaperSize paper) {
    final lines = <bt_model.LineText>[];

    void text(
      String content, {
      int align = bt_model.LineText.ALIGN_LEFT,
      int fontZoom = 1,
      int weight = 0,
      int linefeed = 0,
    }) {
      lines.add(
        bt_model.LineText(
          type: bt_model.LineText.TYPE_TEXT,
          content: content,
          align: align,
          fontZoom: fontZoom,
          weight: weight,
          linefeed: linefeed,
        ),
      );
    }

    void hr() => text('-' * _rowWidth);

    String pair(String left, String right) {
      final l = left.length;
      final r = right.length;
      final spaces = _rowWidth - l - r;
      return spaces > 0 ? '$left${' ' * spaces}$right' : '$left $right';
    }

    text(store.name, align: bt_model.LineText.ALIGN_CENTER, fontZoom: 2, weight: 1, linefeed: 1);
    if (store.address.isNotEmpty) {
      text(store.address, align: bt_model.LineText.ALIGN_CENTER);
    }
    if (store.phone.isNotEmpty) {
      text(store.phone, align: bt_model.LineText.ALIGN_CENTER, linefeed: 1);
    }
    hr();
    text(pair('Invoice', receipt.invoiceNumber));
    text(pair('Kasir', receipt.cashierName));
    text(pair('Tgl', receipt.createdAt));
    hr();
    for (final item in receipt.items) {
      text(item.productName);
      text(pair('${item.quantity} x ${_money(item.price)}', _money(item.subtotal)));
      if (item.note != null && item.note!.isNotEmpty) {
        text('  - ${item.note}');
      }
    }
    hr();
    text(pair('Subtotal', _money(receipt.subtotal)));
    text(pair('Discount', _money(receipt.discount)));
    text(pair('TOTAL', _money(receipt.total)), weight: 1);
    hr();
    text(pair(_paymentLabel(receipt.paymentMethod), _money(receipt.paidAmount)));
    text(pair('Kembalian', _money(receipt.changeAmount)));
    hr();
    text(store.footer, align: bt_model.LineText.ALIGN_CENTER, linefeed: 3);

    return lines;
  }

  String _paymentLabel(String method) {
    switch (method) {
      case 'CASH':
        return 'Tunai';
      case 'QRIS':
        return 'QRIS';
      case 'TRANSFER':
        return 'Transfer';
      default:
        return method;
    }
  }

String _money(num value) {
  final totalCents = (value * 100).round();
  final whole = totalCents ~/ 100;
  final cents = totalCents % 100;
  final digits = whole.toString();
  final buffer = StringBuffer();
  final reversed = digits.split('').reversed.toList();
  for (var i = 0; i < reversed.length; i++) {
    buffer.write(reversed[i]);
    if ((i + 1) % 3 == 0 && i != reversed.length - 1) {
      buffer.write('.');
    }
  }
  final formattedWhole = buffer.toString().split('').reversed.join();
  final fixed = cents < 10 ? '0$cents' : '$cents';
  return '$formattedWhole,$fixed';
}
}