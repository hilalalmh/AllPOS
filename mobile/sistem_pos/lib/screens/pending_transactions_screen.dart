import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../models/pending_transaction.dart';
import '../providers/providers.dart';
import '../utils/money.dart';

class PendingTransactionsScreen extends ConsumerWidget {
  const PendingTransactionsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(syncNotifierProvider);
    final canSync = state.queuedCount > 0 && !state.syncing;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Transaksi Tertunda'),
        actions: [
          IconButton(
            tooltip: 'Sinkronkan sekarang',
            onPressed: canSync
                ? () => ref.read(syncNotifierProvider.notifier).syncNow()
                : null,
            icon: const Icon(Icons.sync),
          ),
        ],
      ),
      body: Column(
        children: [
          if (state.error != null)
            Container(
              width: double.infinity,
              color: Theme.of(context).colorScheme.errorContainer,
              padding: const EdgeInsets.all(12),
              child: Text(
                'Sinkron gagal: ${state.error}',
                style: TextStyle(
                  color: Theme.of(context).colorScheme.onErrorContainer,
                ),
              ),
            ),
          if (state.lastSynced > 0 || state.lastFailed > 0)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  if (state.lastSynced > 0)
                    Text('✓ ${state.lastSynced} tersinkron  '),
                  if (state.lastFailed > 0)
                    Text(
                      '✗ ${state.lastFailed} gagal',
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                ],
              ),
            ),
          Expanded(
            child: state.pending.isEmpty
                ? const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.cloud_done_outlined, size: 56),
                        SizedBox(height: 8),
                        Text('Tidak ada transaksi tertunda.'),
                      ],
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: state.pending.length,
                    itemBuilder: (context, index) =>
                        _PendingTile(item: state.pending[index]),
                  ),
          ),
        ],
      ),
      floatingActionButton: state.syncing
          ? null
          : FloatingActionButton.extended(
              onPressed: canSync
                  ? () async {
                      await ref
                          .read(syncNotifierProvider.notifier)
                          .syncNow();
                    }
                  : null,
              icon: const Icon(Icons.cloud_upload_outlined),
              label: Text(state.syncing
                  ? 'Menyinkron...'
                  : 'Sinkron (${state.queuedCount})'),
            ),
    );
  }
}

class _PendingTile extends ConsumerWidget {
  const _PendingTile({required this.item});

  final PendingTransaction item;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final statusColor = item.isSynced
        ? Colors.green
        : item.isFailed
            ? theme.colorScheme.error
            : theme.colorScheme.primary;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    item.localRef,
                    style: theme.textTheme.titleSmall,
                  ),
                ),
                if (item.isSynced && item.invoiceNumber != null)
                  Text(
                    item.invoiceNumber!,
                    style: theme.textTheme.bodySmall,
                  ),
              ],
            ),
            const SizedBox(height: 4),
            Text(
              item.createdAtLocal.toLocal().toString(),
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                Chip(
                  label: Text(
                    item.isSynced
                        ? 'Tersinkron'
                        : item.isFailed
                            ? 'Gagal'
                            : 'Menunggu',
                  ),
                  labelStyle: TextStyle(color: statusColor),
                  visualDensity: VisualDensity.compact,
                  side: BorderSide(color: statusColor),
                ),
                const Spacer(),
                Text(
                  formatRupiah(item.total),
                  style: theme.textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            if (item.error != null)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Text(
                  item.error!,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: theme.colorScheme.error,
                  ),
                ),
              ),
            if (item.isFailed) ...[
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton.icon(
                    onPressed: () => ref
                        .read(syncNotifierProvider.notifier)
                        .retry(item.id!),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Ulang'),
                  ),
                  TextButton.icon(
                    onPressed: () => ref
                        .read(syncNotifierProvider.notifier)
                        .remove(item.id!),
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Hapus'),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}