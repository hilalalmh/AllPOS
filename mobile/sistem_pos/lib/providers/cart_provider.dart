import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/product.dart';

class CartLine {
  CartLine({required this.product, this.quantity = 1});

  final Product product;
  final int quantity;

  num get subtotal => product.price * quantity;

  CartLine copyWith({int? quantity}) => CartLine(
        product: product,
        quantity: quantity ?? this.quantity,
      );
}

class CartState {
  const CartState({this.lines = const []});

  final List<CartLine> lines;

  bool get isEmpty => lines.isEmpty;

  int get totalQuantity =>
      lines.fold(0, (sum, line) => sum + line.quantity);

  num get subtotal =>
      lines.fold<num>(0, (sum, line) => sum + line.subtotal);

  CartLine? lineFor(int productId) {
    for (final line in lines) {
      if (line.product.id == productId) return line;
    }
    return null;
  }
}

class CartNotifier extends StateNotifier<CartState> {
  CartNotifier() : super(const CartState());

  void add(Product product) {
    final index = state.lines.indexWhere((l) => l.product.id == product.id);
    if (index == -1) {
      state = CartState(lines: [...state.lines, CartLine(product: product)]);
    } else {
      final updated = [...state.lines];
      updated[index] = updated[index].copyWith(
        quantity: updated[index].quantity + 1,
      );
      state = CartState(lines: updated);
    }
  }

  void increment(int productId) {
    final index = state.lines.indexWhere((l) => l.product.id == productId);
    if (index == -1) return;
    final updated = [...state.lines];
    updated[index] = updated[index].copyWith(
      quantity: updated[index].quantity + 1,
    );
    state = CartState(lines: updated);
  }

  void decrement(int productId) {
    final index = state.lines.indexWhere((l) => l.product.id == productId);
    if (index == -1) return;
    final updated = [...state.lines];
    final quantity = updated[index].quantity - 1;
    if (quantity <= 0) {
      updated.removeAt(index);
    } else {
      updated[index] = updated[index].copyWith(quantity: quantity);
    }
    state = CartState(lines: updated);
  }

  void remove(int productId) {
    state = CartState(
      lines: state.lines
          .where((l) => l.product.id != productId)
          .toList(),
    );
  }

  void clear() => state = const CartState();
}

final cartProvider = StateNotifierProvider<CartNotifier, CartState>(
  (ref) => CartNotifier(),
);