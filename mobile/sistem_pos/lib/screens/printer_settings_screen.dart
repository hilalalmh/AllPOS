import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../providers/providers.dart';
import '../services/printer_service.dart';

class PrinterSettingsScreen extends ConsumerWidget {
  const PrinterSettingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final printer = ref.watch(printerNotifierProvider);
    final notifier = ref.read(printerNotifierProvider.notifier);

    final statusColor =
        printer.connected ? Colors.green : (printer.available ? Colors.orange : Colors.red);

    return Scaffold(
      appBar: AppBar(title: const Text('Printer')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.bluetooth, color: statusColor),
                      const SizedBox(width: 8),
                      Text(
                        printer.connected
                            ? 'Terhubung: ${printer.connectedDevice?.displayName ?? '-'}'
                            : (printer.available
                                ? 'Bluetooth aktif - belum terhubung'
                                : 'Bluetooth tidak tersedia / mati'),
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  TextButton.icon(
                    onPressed: printer.connected
                        ? notifier.disconnect
                        : null,
                    icon: const Icon(Icons.link_off),
                    label: const Text('Putuskan koneksi'),
                  ),
                ],
              ),
            ),
          ),
          if (printer.lastError != null) ...[
            const SizedBox(height: 12),
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    Icon(
                      Icons.error_outline,
                      color: Theme.of(context).colorScheme.onErrorContainer,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        printer.lastError!,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: 16),
          FilledButton.icon(
            onPressed: printer.scanning || !printer.available ? null : notifier.startScan,
            icon: printer.scanning
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.search),
            label: Text(printer.scanning ? 'Memindai...' : 'Pindai Printer'),
          ),
          const SizedBox(height: 12),
          if (printer.devices.isEmpty)
            Text(
              'Tekan "Pindai Printer" untuk mencari perangkat Bluetooth di sekitar.',
              style: Theme.of(context).textTheme.bodySmall,
            )
          else
            ...printer.devices.map(
              (device) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ListTile(
                  leading: Icon(
                    printer.connectedDevice?.address == device.address
                        ? Icons.check_circle
                        : Icons.bluetooth,
                    color: printer.connectedDevice?.address == device.address
                        ? Colors.green
                        : null,
                  ),
                  title: Text(device.displayName),
                  subtitle: Text(device.address ?? '-'),
                  trailing: printer.connectedDevice?.address == device.address
                      ? null
                      : TextButton(
                          onPressed: printer.busy ? null : () => notifier.connect(device),
                          child: const Text('Hubungkan'),
                        ),
                ),
              ),
            ),
          const Divider(height: 32),
          Text('Ukuran Kertas', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          SegmentedButton<PaperSize>(
            segments: PaperSize.values
                .map((s) => ButtonSegment(value: s, label: Text(s.label)))
                .toList(),
            selected: {printer.paperSize},
            onSelectionChanged: (selection) {
              notifier.setPaperSize(selection.first);
            },
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: printer.busy || !printer.connected
                      ? null
                      : notifier.testPrint,
                  icon: const Icon(Icons.build_outlined),
                  label: const Text('Tes Cetak'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: printer.busy || !printer.connected
                      ? null
                      : notifier.reprint,
                  icon: const Icon(Icons.replay),
                  label: const Text('Cetak Ulang'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            printer.busy ? 'Mencetak...' : 'Gunakan kecil untuk kertas 58 mm, besar untuk 80 mm.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ],
      ),
    );
  }
}