import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/transaction.dart';
import '../models/user.dart';
import '../providers/cart_provider.dart';
import '../providers/providers.dart';
import '../utils/money.dart';
import 'payment_success_screen.dart';

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});

  @override
  ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}

class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  final _discountController = TextEditingController();
  final _paidController = TextEditingController();
  String _paymentMethod = 'CASH';
  bool _submitting = false;

  static const _methods = [
    (label: 'Tunai', value: 'CASH', icon: Icons.payments),
    (label: 'QRIS', value: 'QRIS', icon: Icons.qr_code_2),
    (label: 'Transfer', value: 'TRANSFER', icon: Icons.account_balance),
  ];

  @override
  void dispose() {
    _discountController.dispose();
    _paidController.dispose();
    super.dispose();
  }

  num get _discount => num.tryParse(_discountController.text) ?? 0;
  num get _paid => num.tryParse(_paidController.text) ?? 0;

  num _totalFor(CartState cart) {
    final discount = _discount.clamp(0, cart.subtotal);
    return (cart.subtotal - discount).toDouble();
  }

  bool _canSubmit(CartState cart) {
    if (cart.isEmpty || _submitting) return false;
    final total = _totalFor(cart);
    return _paymentMethod == 'CASH' ? _paid >= total : true;
  }

  Future<void> _submit(CartState cart, User user) async {
    if (_submitting) return;
    final syncService = ref.read(transactionSyncServiceProvider);
    final subtotal = cart.subtotal;
    final discount = _discount.clamp(0, subtotal).toDouble();
    final total = _totalFor(cart);
    final items = [
      for (final line in cart.lines)
        CartItemInput(
          productId: line.product.id,
          quantity: line.quantity,
          productName: line.product.name,
          price: line.product.price,
        ),
    ];
    setState(() => _submitting = true);
    try {
      final paid = _paymentMethod == 'CASH' ? _paid : total;
      final result = await syncService.createWithFallback(
        items: items,
        paymentMethod: _paymentMethod,
        paidAmount: paid,
        discount: discount,
      );
      final cartNotifier = ref.read(cartProvider.notifier);
      if (!mounted) return;
      cartNotifier.clear();
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => PaymentSuccessScreen(
            result: result,
            cashierName: user.fullName,
          ),
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Transaksi gagal: $e')),
      );
      setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = ref.watch(cartProvider);
    final auth = ref.watch(authNotifierProvider);
    final user = auth.user;

    final subtotal = cart.subtotal;
    final total = _totalFor(cart);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Checkout'),
        actions: [
          IconButton(
            tooltip: 'Kosongkan keranjang',
            icon: const Icon(Icons.delete_outline),
            onPressed: cart.isEmpty
                ? null
                : () => ref.read(cartProvider.notifier).clear(),
          ),
        ],
      ),
      body: cart.isEmpty
          ? const Center(child: Text('Keranjang kosong.'))
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                ...cart.lines.map((line) => _LineTile(
                      line: line,
                      onIncrement: () => ref
                          .read(cartProvider.notifier)
                          .increment(line.product.id),
                      onDecrement: () => ref
                          .read(cartProvider.notifier)
                          .decrement(line.product.id),
                      onRemove: () => ref
                          .read(cartProvider.notifier)
                          .remove(line.product.id),
                    )),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _discountController,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  inputFormatters: [
                    FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                  ],
                  decoration: const InputDecoration(
                    labelText: 'Diskon (Rp)',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.percent),
                  ),
                  onChanged: (_) => setState(() {}),
                ),
                const SizedBox(height: 16),
                const Text('Metode Pembayaran'),
                const SizedBox(height: 8),
                SegmentedButton<String>(
                  segments: [
                    for (final m in _methods)
                      ButtonSegment(
                        value: m.value,
                        label: Text(m.label),
                        icon: Icon(m.icon),
                      ),
                  ],
                  selected: {_paymentMethod},
                  onSelectionChanged: (selection) =>
                      setState(() => _paymentMethod = selection.first),
                ),
                if (_paymentMethod == 'CASH') ...[
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _paidController,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    inputFormatters: [
                      FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')),
                    ],
                    decoration: const InputDecoration(
                      labelText: 'Uang Diterima (Rp)',
                      border: OutlineInputBorder(),
                      prefixIcon: Icon(Icons.money),
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ],
                const SizedBox(height: 24),
                _SummaryTile(label: 'Subtotal', value: subtotal),
                _SummaryTile(
                  label: 'Diskon',
                  value: -_discount.clamp(0, subtotal),
                  hint: total,
                ),
                _SummaryTile(label: 'Total', value: total, bold: true),
                if (_paymentMethod == 'CASH')
                  _SummaryTile(
                    label: 'Kembalian',
                    value: (_paid - total),
                    hint: _paid,
                    accent: true,
                  ),
                const SizedBox(height: 24),
                if (_paymentMethod != 'CASH')
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text(
                      'Total dibayar: ${formatRupiah(total)} '
                      '($_methodLabel)',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                FilledButton.icon(
                  onPressed: user == null || !_canSubmit(cart)
                      ? null
                      : () => _submit(cart, user),
                  icon: _submitting
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.check_circle),
                  label: Text(_submitting ? 'Memproses...' : 'Bayar'),
                  style: FilledButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    textStyle: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                if (_paymentMethod == 'CASH' && _paid < total)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: Text(
                      'Uang diterima kurang Rp ${formatRupiah(total - _paid)}',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
              ],
            ),
    );
  }

  String get _methodLabel {
    for (final m in _methods) {
      if (m.value == _paymentMethod) return m.label;
    }
    return _paymentMethod;
  }
}

class _LineTile extends StatelessWidget {
  const _LineTile({
    required this.line,
    required this.onIncrement,
    required this.onDecrement,
    required this.onRemove,
  });

  final CartLine line;
  final VoidCallback onIncrement;
  final VoidCallback onDecrement;
  final VoidCallback onRemove;

  @override
  Widget build(BuildContext context) {
    final product = line.product;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.name,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Text(
                    '${formatRupiah(product.price)} x ${line.quantity}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
            ),
            Text(
              formatRupiah(line.subtotal),
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: onRemove,
              icon: const Icon(Icons.close, size: 18),
              visualDensity: VisualDensity.compact,
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryTile extends StatelessWidget {
  const _SummaryTile({
    required this.label,
    required this.value,
    this.hint,
    this.bold = false,
    this.accent = false,
  });

  final String label;
  final num value;
  final num? hint;
  final bool bold;
  final bool accent;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: bold ? theme.textTheme.titleMedium : null,
          ),
          Text(
            formatRupiah(value),
            style: theme.textTheme.bodyLarge?.copyWith(
              fontWeight: bold ? FontWeight.bold : null,
              color: accent ? theme.colorScheme.primary : null,
            ),
          ),
        ],
      ),
    );
  }
}