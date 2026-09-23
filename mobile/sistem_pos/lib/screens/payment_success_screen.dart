import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/transaction.dart';
import '../providers/providers.dart';
import '../utils/money.dart';

class PaymentSuccessScreen extends ConsumerStatefulWidget {
  const PaymentSuccessScreen({
    super.key,
    required this.result,
    required this.cashierName,
  });

  final PayResult result;
  final String cashierName;

  @override
  ConsumerState<PaymentSuccessScreen> createState() =>
      _PaymentSuccessScreenState();
}

class _PaymentSuccessScreenState extends ConsumerState<PaymentSuccessScreen> {
  bool _printed = false;

  String get _paymentLabel {
    switch (widget.result.paymentMethod) {
      case 'QRIS':
        return 'QRIS';
      case 'TRANSFER':
        return 'Transfer';
      default:
        return 'Tunai';
    }
  }

  Future<void> _print() async {
    final receipt = widget.result.toReceipt(cashierName: widget.cashierName);
    await ref.read(printerNotifierProvider.notifier).printReceipt(receipt);
  }

  @override
  Widget build(BuildContext context) {
    final printer = ref.watch(printerNotifierProvider);
    final result = widget.result;
    final theme = Theme.of(context);

    return Scaffold(
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Spacer(),
              Icon(
                result.isOffline ? Icons.cloud_off : Icons.check_circle,
                color: result.isOffline ? Colors.orange : Colors.green,
                size: 88,
              ),
              const SizedBox(height: 16),
              Text(
                result.isOffline ? 'Disimpan Offline' : 'Pembayaran Berhasil',
                textAlign: TextAlign.center,
                style: theme.textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                result.reference,
                textAlign: TextAlign.center,
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 4),
              Text(
                result.createdAtText,
                textAlign: TextAlign.center,
                style: theme.textTheme.bodySmall,
              ),
              if (result.isOffline) ...[
                const SizedBox(height: 8),
                Text(
                  'Belum ada koneksi. Transaksi masuk antrian '
                  'dan akan tersinkron otomatis.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: Colors.orange.shade800,
                  ),
                ),
              ],
              const SizedBox(height: 24),
              Container(
                decoration: BoxDecoration(
                  color: theme.colorScheme.surfaceContainerHighest,
                  borderRadius: BorderRadius.circular(12),
                ),
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    _row('Total Bayar', formatRupiah(result.total), bold: true),
                    _row('Metode', _paymentLabel),
                    if (result.discount > 0)
                      _row('Diskon', '- ${formatRupiah(result.discount)}'),
                    _row('Dibayar', formatRupiah(result.paidAmount)),
                    _row('Kembalian', formatRupiah(result.changeAmount)),
                  ],
                ),
              ),
              const Spacer(),
              if (printer.lastError != null)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    'Cetak gagal: ${printer.lastError}',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: theme.colorScheme.error),
                  ),
                ),
              FilledButton.icon(
                onPressed: printer.busy
                    ? null
                    : () async {
                        await _print();
                        final err = ref.read(printerNotifierProvider).lastError;
                        // Tandai tercetak hanya bila tidak ada error printer.
                        if (mounted && err == null) {
                          setState(() => _printed = true);
                        }
                      },
                icon: printer.busy
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.print),
                label: Text(_printed ? 'Cetak Ulang Struk' : 'Cetak Struk'),
                style: FilledButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
              ),
              const SizedBox(height: 8),
              OutlinedButton(
                onPressed: () {
                  while (Navigator.of(context).canPop()) {
                    Navigator.of(context).pop();
                  }
                },
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: const Text('Selesai'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _row(String label, String value, {bool bold = false}) {
    final theme = Theme.of(context);
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: theme.textTheme.bodyMedium),
          Text(
            value,
            style: theme.textTheme.bodyMedium?.copyWith(
              fontWeight: bold ? FontWeight.bold : null,
            ),
          ),
        ],
      ),
    );
  }
}
