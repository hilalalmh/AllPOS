import 'package:path/path.dart' as p;
import 'package:sqflite/sqflite.dart';

import '../models/pending_transaction.dart';

class OfflineTransactionStore {
  OfflineTransactionStore({String? databasePath}) : _customPath = databasePath;

  final String? _customPath;
  Database? _db;
  Future<Database>? _dbFuture;

  Future<Database> get _database async {
    if (_db != null) return _db!;
    final pending = _dbFuture;
    if (pending != null) return pending;
    final future = _open();
    _dbFuture = future;
    try {
      return await future;
    } catch (_) {
      if (identical(_dbFuture, future)) _dbFuture = null;
      rethrow;
    }
  }

  Future<Database> _open() async {
    final path = _customPath ??
        p.join(await getDatabasesPath(), 'sistem_pos.db');
    final db = await openDatabase(
      path,
      version: 2,
      onCreate: (db, _) async {
        await db.execute('''
          CREATE TABLE pending_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_ref TEXT NOT NULL UNIQUE,
            items_json TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            subtotal REAL NOT NULL,
            discount REAL NOT NULL,
            total REAL NOT NULL,
            paid_amount REAL NOT NULL,
            change_amount REAL NOT NULL,
            created_at_local TEXT NOT NULL,
            cashier_id INTEGER,
            status TEXT NOT NULL,
            invoice_number TEXT,
            error TEXT,
            synced_at TEXT
          )
        ''');
      },
      onUpgrade: (db, oldVersion, newVersion) async {
        if (oldVersion < 2) {
          await db.execute(
            'ALTER TABLE pending_transactions ADD COLUMN cashier_id INTEGER',
          );
        }
      },
    );
    _db = db;
    return db;
  }

  Future<PendingTransaction> insert(PendingTransaction entry) async {
    final db = await _database;
    final id = await db.insert('pending_transactions', entry.toRow());
    return PendingTransaction(
      id: id,
      localRef: entry.localRef,
      items: entry.items,
      paymentMethod: entry.paymentMethod,
      subtotal: entry.subtotal,
      discount: entry.discount,
      total: entry.total,
      paidAmount: entry.paidAmount,
      changeAmount: entry.changeAmount,
      createdAtLocal: entry.createdAtLocal,
      cashierId: entry.cashierId,
      status: entry.status,
      invoiceNumber: entry.invoiceNumber,
      error: entry.error,
      syncedAt: entry.syncedAt,
    );
  }

  Future<List<PendingTransaction>> all() async {
    final db = await _database;
    final rows = await db.query(
      'pending_transactions',
      orderBy: 'created_at_local ASC',
    );
    return rows.map(PendingTransaction.fromRow).toList();
  }

  Future<int> count() async {
    final db = await _database;
    final result = await db.rawQuery(
      'SELECT COUNT(*) AS c FROM pending_transactions WHERE status IN (?, ?)',
      ['PENDING', 'FAILED'],
    );
    return result.first['c'] as int;
  }

  Future<bool> containsRef(String localRef) async {
    final db = await _database;
    final rows = await db.query(
      'pending_transactions',
      where: 'local_ref = ?',
      whereArgs: [localRef],
      limit: 1,
    );
    return rows.isNotEmpty;
  }

  Future<void> markSynced(int id, String invoiceNumber) async {
    final db = await _database;
    await db.update(
      'pending_transactions',
      {
        'status': 'SYNCED',
        'invoice_number': invoiceNumber,
        'synced_at': DateTime.now().toIso8601String(),
        'error': null,
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> markFailed(int id, String error) async {
    final db = await _database;
    await db.update(
      'pending_transactions',
      {'status': 'FAILED', 'error': error},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> resetToPending(int id) async {
    final db = await _database;
    await db.update(
      'pending_transactions',
      {'status': 'PENDING', 'error': null},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<void> remove(int id) async {
    final db = await _database;
    await db.delete('pending_transactions', where: 'id = ?', whereArgs: [id]);
  }
}