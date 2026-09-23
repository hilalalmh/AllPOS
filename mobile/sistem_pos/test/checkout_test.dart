import 'package:flutter_test/flutter_test.dart';

import 'package:sistem_pos/models/product.dart';
import 'package:sistem_pos/models/transaction.dart';
import 'package:sistem_pos/providers/cart_provider.dart';
import 'package:sistem_pos/utils/money.dart';

Product _product(int id, String name, num price) => Product(
      id: id,
      categoryId: 1,
      name: name,
      price: price,
    );

void main() {
  group('CartNotifier', () {
    test('menambah produk baru jadi satu baris', () {
      final cart = CartNotifier();
      cart.add(_product(1, 'Es Kopi', 18000));
      cart.add(_product(1, 'Es Kopi', 18000));
      cart.add(_product(2, 'Roti Bakar', 15000));

      expect(cart.state.lines.length, 2);
      expect(cart.state.totalQuantity, 3);
      expect(cart.state.subtotal, 51000);
    });

    test('increment dan decrement mengubah kuantitas', () {
      final cart = CartNotifier();
      cart.add(_product(1, 'Es Kopi', 18000));
      cart.increment(1);
      expect(cart.state.totalQuantity, 2);
      cart.decrement(1);
      expect(cart.state.totalQuantity, 1);
      cart.decrement(1);
      expect(cart.state.isEmpty, isTrue);
    });

    test('remove menghapus baris tertentu', () {
      final cart = CartNotifier();
      cart.add(_product(1, 'Es Kopi', 18000));
      cart.add(_product(2, 'Roti Bakar', 15000));
      cart.remove(1);
      expect(cart.state.lines.length, 1);
      expect(cart.state.lines.single.product.id, 2);
    });

    test('clear mengosongkan keranjang', () {
      final cart = CartNotifier();
      cart.add(_product(1, 'Es Kopi', 18000));
      cart.clear();
      expect(cart.state.isEmpty, isTrue);
      expect(cart.state.subtotal, 0);
    });
  });

  group('Transaction', () {
    final json = {
      'id': 42,
      'invoice_number': 'POS-20260923-0002',
      'cashier_id': 2,
      'subtotal': 33000,
      'discount': 3000,
      'total': 30000,
      'payment_method': 'CASH',
      'paid_amount': 50000,
      'change_amount': 20000,
      'status': 'COMPLETED',
      'created_at': '2026-09-23T10:00:00',
      'items': [
        {
          'id': 1,
          'product_id': 3,
          'product_name': 'Es Kopi',
          'price': 18000,
          'quantity': 1,
          'subtotal': 18000,
          'note': null,
        },
        {
          'id': 2,
          'product_id': 5,
          'product_name': 'Roti Bakar',
          'price': 15000,
          'quantity': 1,
          'subtotal': 15000,
          'note': null,
        },
      ],
    };

    test('fromJson membongkar semua field', () {
      final t = Transaction.fromJson(json);
      expect(t.id, 42);
      expect(t.invoiceNumber, 'POS-20260923-0002');
      expect(t.paymentMethod, 'CASH');
      expect(t.paidAmount, 50000);
      expect(t.changeAmount, 20000);
      expect(t.status, 'COMPLETED');
      expect(t.items.length, 2);
      expect(t.items.first.productName, 'Es Kopi');
      expect(t.items.first.price, 18000);
    });

    test('toReceipt memetakan ke data struk', () {
      final t = Transaction.fromJson(json);
      final receipt = t.toReceipt(cashierName: 'kasir1');
      expect(receipt.invoiceNumber, 'POS-20260923-0002');
      expect(receipt.cashierName, 'kasir1');
      expect(receipt.subtotal, 33000);
      expect(receipt.discount, 3000);
      expect(receipt.total, 30000);
      expect(receipt.paidAmount, 50000);
      expect(receipt.changeAmount, 20000);
      expect(receipt.items.first.productName, 'Es Kopi');
      expect(receipt.createdAt, isNotEmpty);
    });
  });

  group('formatRupiah', () {
    test('memformat angka dengan pemisah ribuan', () {
      expect(formatRupiah(30000), 'Rp30.000');
      expect(formatRupiah(1234567), 'Rp1.234.567');
      expect(formatRupiah(0), 'Rp0');
      expect(formatRupiah(18000.5), 'Rp18.000,50');
    });
  });
}