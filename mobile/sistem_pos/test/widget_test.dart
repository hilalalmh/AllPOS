import 'package:flutter_test/flutter_test.dart';

import 'package:sistem_pos/models/receipt.dart';
import 'package:sistem_pos/services/printer_service.dart';
import 'package:sistem_pos/services/receipt_service.dart';

void main() {
  test('buildLines menghasilkan baris struk yang cocok dengan transaksi', () {
    final service = ReceiptService(
      store: const StoreInfo(name: 'Aroma Kopi Nusantara'),
    );
    final receipt = ReceiptData(
      invoiceNumber: 'POS-20260922-0001',
      cashierName: 'kasir1',
      items: const [
        ReceiptItem(
          productName: 'Es Kopi',
          quantity: 2,
          price: 18000,
          subtotal: 36000,
        ),
      ],
      subtotal: 36000,
      discount: 0,
      total: 36000,
      paidAmount: 40000,
      changeAmount: 4000,
      paymentMethod: 'CASH',
      createdAt: '2026-09-22 10:30:00',
    );

    final lines = service.buildLines(receipt, PaperSize.mm58);

    expect(lines, isNotEmpty);
    final contents = lines.map((l) => l.content ?? '').join('\n');
    expect(contents, contains('Aroma Kopi Nusantara'));
    expect(contents, contains('POS-20260922-0001'));
    expect(contents, contains('kasir1'));
    expect(contents, contains('Es Kopi'));
    expect(contents, contains('2 x 18.000'));
    expect(contents, contains('Tunai'));
    expect(contents, contains('4.000'));
  });

  test('header dan footer struk memakai profil toko', () {
    final service = ReceiptService(
      store: const StoreInfo(
        name: 'Kedai Kopi Tetangga',
        address: 'Jl. Melati No. 12',
        phone: '0812-0000-1111',
        footer: 'TERIMA KASIH ~ SAMPAI JUMPA',
      ),
    );
    final lines = service.buildLines(
      ReceiptData(
        invoiceNumber: 'YPOS-001',
        cashierName: 'kasir2',
        items: const [],
        subtotal: 0,
        discount: 0,
        total: 0,
        paidAmount: 0,
        changeAmount: 0,
        paymentMethod: 'CASH',
        createdAt: '',
      ),
      PaperSize.mm58,
    );
    final contents = lines.map((l) => l.content ?? '').join('\n');
    expect(contents, contains('Kedai Kopi Tetangga'));
    expect(contents, contains('Jl. Melati No. 12'));
    expect(contents, contains('0812-0000-1111'));
    expect(contents, contains('TERIMA KASIH ~ SAMPAI JUMPA'));
  });

  test('printerConfig menyesuaikan lebar kertas', () {
    final service = ReceiptService();
    expect(service.printerConfig(PaperSize.mm58)['width'], 580);
    expect(service.printerConfig(PaperSize.mm80)['width'], 800);
  });

  test('money formatting memakai titik dan koma ala Indonesia', () {
    final service = ReceiptService();
    final lines = service.buildLines(
      ReceiptData(
        invoiceNumber: 'X',
        cashierName: 'c',
        items: const [],
        subtotal: 36000,
        discount: 1000,
        total: 35000,
        paidAmount: 50000,
        changeAmount: 15000,
        paymentMethod: 'QRIS',
        createdAt: '',
      ),
      PaperSize.mm58,
    );
    final contents = lines.map((l) => l.content ?? '').join('\n');
    expect(contents, contains('36.000,00'));
    expect(contents, contains('1.000,00'));
    expect(contents, contains('50.000,00'));
    expect(contents, contains('QRIS'));
    expect(contents, contains('Kembalian'));
  });

  test('struk memuat QR dan barcode nomor invoice', () {
    final service = ReceiptService(
      store: const StoreInfo(name: 'Aroma Kopi Nusantara'),
    );
    final lines = service.buildLines(
      ReceiptData(
        invoiceNumber: 'POS-20260922-0001',
        cashierName: 'kasir1',
        items: const [],
        subtotal: 0,
        discount: 0,
        total: 0,
        paidAmount: 0,
        changeAmount: 0,
        paymentMethod: 'CASH',
        createdAt: '',
      ),
      PaperSize.mm58,
    );
    final qr = lines.where(
      (l) => l.type == 'qrcode' && (l.content ?? '').contains('POS-20260922-0001'),
    );
    final barcode = lines.where(
      (l) => l.type == 'barcode' && (l.content ?? '').contains('POS-20260922-0001'),
    );
    expect(qr, isNotEmpty);
    expect(barcode, isNotEmpty);
  });
}