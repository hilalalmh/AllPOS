import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/app_config.dart';
import '../models/pending_transaction.dart';
import '../models/product.dart';
import '../models/receipt.dart';
import '../models/store_profile.dart';
import '../models/user.dart';
import '../repositories/auth_repository.dart';
import '../repositories/product_repository.dart';
import '../repositories/session_store.dart';
import '../repositories/store_profile_repository.dart';
import '../repositories/transaction_repository.dart';
import '../services/api_client.dart';
import '../services/offline_transaction_store.dart';
import '../services/printer_service.dart';
import '../services/receipt_service.dart';
import '../services/transaction_sync_service.dart';
import 'cart_provider.dart';

final sharedPrefsProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError('Override sharedPrefsProvider di main()'),
);

final sessionStoreProvider = Provider<SessionStore>(
  (ref) => SessionStore(ref.watch(sharedPrefsProvider)),
);

final authExpiredEventsProvider = Provider<StreamController<void>>((ref) {
  final controller = StreamController<void>.broadcast();
  ref.onDispose(controller.close);
  return controller;
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final sessionStore = ref.watch(sessionStoreProvider);
  final authExpired = ref.watch(authExpiredEventsProvider);
  return ApiClient(
    baseUrl: AppConfig.apiBaseUrl,
    tokenProvider: () => sessionStore.accessToken,
    refreshTokenProvider: () => sessionStore.refreshToken,
    onTokensSaved: (access, refresh) =>
        sessionStore.saveTokens(access, refresh),
    onAuthExpired: () async {
      authExpired.add(null);
    },
  );
});

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    api: ref.watch(apiClientProvider),
    store: ref.watch(sessionStoreProvider),
  ),
);

const _unset = Object();

class AuthState {
  const AuthState({this.user, this.loading = false, this.error});

  final User? user;
  final bool loading;
  final String? error;

  bool get isAuthenticated => user != null;

  AuthState copyWith({User? user, bool? loading, Object? error = _unset}) =>
      AuthState(
        user: user ?? this.user,
        loading: loading ?? this.loading,
        error: identical(error, _unset) ? this.error : error as String?,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._repo, this._ref) : super(AuthState(user: _repo.store.user)) {
    _expiredSub = _ref
        .read(authExpiredEventsProvider)
        .stream
        .listen((_) => logout());
  }

  final AuthRepository _repo;
  final Ref _ref;
  StreamSubscription<void>? _expiredSub;

  Future<void> login(String username, String password) async {
    state = state.copyWith(loading: true, error: null);
    try {
      final user = await _repo.login(username.trim(), password);
      _ref.read(cartProvider.notifier).clear();
      _ref.invalidate(productsProvider);
      _ref.invalidate(storeProfileNotifierProvider);
      state = state.copyWith(user: user, loading: false);
    } catch (e) {
      state = state.copyWith(loading: false, error: _message(e));
    }
  }

  Future<void> logout() async {
    _ref.read(cartProvider.notifier).clear();
    await _repo.logout();
    await _ref.read(sessionStoreProvider).clearLastReceipt();
    await _ref.read(syncNotifierProvider.notifier).load();
    state = const AuthState();
  }

  String _message(Object e) {
    if (e is ApiException) return e.message;
    return e.toString();
  }

  @override
  void dispose() {
    _expiredSub?.cancel();
    super.dispose();
  }
}

final authNotifierProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(authRepositoryProvider), ref);
});

final productRepositoryProvider = Provider<ProductRepository>(
  (ref) => ProductRepository(ref.watch(apiClientProvider)),
);

final transactionRepositoryProvider = Provider<TransactionRepository>(
  (ref) => TransactionRepository(ref.watch(apiClientProvider)),
);

final offlineTransactionStoreProvider = Provider<OfflineTransactionStore>(
  (ref) => OfflineTransactionStore(),
);

final transactionSyncServiceProvider = Provider<TransactionSyncService>(
  (ref) => TransactionSyncService(
    api: ref.watch(apiClientProvider),
    store: ref.watch(offlineTransactionStoreProvider),
  ),
);

class SyncState {
  const SyncState({
    this.pending = const [],
    this.syncing = false,
    this.lastSynced = 0,
    this.lastFailed = 0,
    this.error,
  });

  final List<PendingTransaction> pending;
  final bool syncing;
  final int lastSynced;
  final int lastFailed;
  final String? error;

  int get queuedCount => pending.where((t) => t.isPending).length;
  int get failedCount => pending.where((t) => t.isFailed).length;
  int get syncedCount => pending.where((t) => t.isSynced).length;

  SyncState copyWith({
    List<PendingTransaction>? pending,
    bool? syncing,
    int? lastSynced,
    int? lastFailed,
    Object? error = _unset,
  }) =>
      SyncState(
        pending: pending ?? this.pending,
        syncing: syncing ?? this.syncing,
        lastSynced: lastSynced ?? this.lastSynced,
        lastFailed: lastFailed ?? this.lastFailed,
        error: identical(error, _unset) ? this.error : error as String?,
      );
}

class SyncNotifier extends StateNotifier<SyncState> {
  SyncNotifier({
    required this.transactionSyncService,
  }) : super(const SyncState());

  final TransactionSyncService transactionSyncService;

  Future<void> load() async {
    final pending =
        await transactionSyncService.store.all();
    state = state.copyWith(pending: pending, error: null);
  }

  Future<void> syncNow() async {
    if (state.syncing) return;
    state = state.copyWith(syncing: true, error: null);
    try {
      final outcome = await transactionSyncService.syncAll();
      final pending = await transactionSyncService.store.all();
      state = state.copyWith(
        pending: pending,
        syncing: false,
        lastSynced: outcome.synced,
        lastFailed: outcome.failed,
        error: outcome.error,
      );
    } catch (e) {
      state = state.copyWith(
        syncing: false,
        error: e.toString(),
      );
    }
  }

  Future<void> retry(int id) async {
    await transactionSyncService.store.resetToPending(id);
    await load();
  }

  Future<void> remove(int id) async {
    await transactionSyncService.store.remove(id);
    await load();
  }
}

final syncNotifierProvider =
    StateNotifierProvider<SyncNotifier, SyncState>((ref) {
  return SyncNotifier(transactionSyncService: ref.watch(transactionSyncServiceProvider));
});

final productsProvider = FutureProvider<List<Product>>(
  (ref) async {
    final repo = ref.watch(productRepositoryProvider);
    const pageSize = 100;
    final all = <Product>[];
    var page = 1;
    while (page <= 200) {
      final response = await repo.fetchPage(page: page, pageSize: pageSize);
      all.addAll(response.items);
      if (response.page * pageSize >= response.total ||
          response.items.length < pageSize) {
        break;
      }
      page += 1;
    }
    return all;
  },
);

final storeProfileRepositoryProvider = Provider<StoreProfileRepository>(
  (ref) => StoreProfileRepository(api: ref.watch(apiClientProvider)),
);

class StoreProfileState {
  const StoreProfileState({
    this.profile = StoreProfile.defaultProfile,
    this.loading = false,
    this.error,
  });

  final StoreProfile profile;
  final bool loading;
  final String? error;

  StoreProfileState copyWith({
    StoreProfile? profile,
    bool? loading,
    Object? error = _unset,
  }) =>
      StoreProfileState(
        profile: profile ?? this.profile,
        loading: loading ?? this.loading,
        error: identical(error, _unset) ? this.error : error as String?,
      );
}

class StoreProfileNotifier extends StateNotifier<StoreProfileState> {
  StoreProfileNotifier({
    required this.repository,
    required this.sessionStore,
  }) : super(StoreProfileState(profile: sessionStore.storeProfile)) {
    load();
  }

  final StoreProfileRepository repository;
  final SessionStore sessionStore;

  Future<void> load() async {
    state = state.copyWith(loading: true, error: null);
    try {
      final profile = await repository.fetch();
      await sessionStore.saveStoreProfile(profile);
      state = state.copyWith(profile: profile, loading: false);
    } catch (e) {
      state = state.copyWith(
        loading: false,
        error: e is ApiException ? e.message : e.toString(),
      );
    }
  }
}

final storeProfileNotifierProvider =
    StateNotifierProvider<StoreProfileNotifier, StoreProfileState>((ref) {
  return StoreProfileNotifier(
    repository: ref.watch(storeProfileRepositoryProvider),
    sessionStore: ref.watch(sessionStoreProvider),
  );
});

final receiptServiceProvider = Provider<ReceiptService>(
  (ref) {
    final sessionStore = ref.watch(sessionStoreProvider);
    return ReceiptService(
      storeBuilder: () {
        final profile = sessionStore.storeProfile;
        return StoreInfo(
          name: profile.storeName,
          address: profile.address,
          phone: profile.phone,
          footer: profile.footer,
        );
      },
    );
  },
);

final printerServiceProvider = Provider<PrinterService>(
  (ref) => PrinterService(ref.watch(receiptServiceProvider)),
);

class PrinterState {
  const PrinterState({
    this.available = false,
    this.bluetoothOn = false,
    this.scanning = false,
    this.connected = false,
    this.devices = const [],
    this.connectedDevice,
    this.paperSize = PaperSize.mm58,
    this.busy = false,
    this.lastReceipt,
    this.lastError,
  });

  final bool available;
  final bool bluetoothOn;
  final bool scanning;
  final bool connected;
  final List<PrinterDevice> devices;
  final PrinterDevice? connectedDevice;
  final PaperSize paperSize;
  final bool busy;
  final ReceiptData? lastReceipt;
  final String? lastError;

  PrinterState copyWith({
    bool? available,
    bool? bluetoothOn,
    bool? scanning,
    bool? connected,
    List<PrinterDevice>? devices,
    Object? connectedDevice = _unset,
    PaperSize? paperSize,
    bool? busy,
    Object? lastReceipt = _unset,
    Object? lastError = _unset,
  }) =>
      PrinterState(
        available: available ?? this.available,
        bluetoothOn: bluetoothOn ?? this.bluetoothOn,
        scanning: scanning ?? this.scanning,
        connected: connected ?? this.connected,
        devices: devices ?? this.devices,
        connectedDevice: identical(connectedDevice, _unset)
            ? this.connectedDevice
            : connectedDevice as PrinterDevice?,
        paperSize: paperSize ?? this.paperSize,
        busy: busy ?? this.busy,
        lastReceipt: identical(lastReceipt, _unset)
            ? this.lastReceipt
            : lastReceipt as ReceiptData?,
        lastError: identical(lastError, _unset)
            ? this.lastError
            : lastError as String?,
      );
}

class PrinterNotifier extends StateNotifier<PrinterState> {
  PrinterNotifier({
    required this.printerService,
    required this.sessionStore,
  }) : super(const PrinterState()) {
    _restore();
  }

  final PrinterService printerService;
  final SessionStore sessionStore;

  Future<void> _restore() async {
    final available = await printerService.isAvailable;
    final on = await printerService.isOn;
    final lastPrinter = sessionStore.lastPrinter;
    var connected = false;
    var device = lastPrinter;
    if (available && on && lastPrinter != null) {
      try {
        await printerService.connect(lastPrinter);
        connected = true;
      } catch (_) {
        connected = false;
      }
    }
    state = state.copyWith(
      available: available,
      bluetoothOn: on,
      connected: connected,
      connectedDevice: connected ? device : null,
      paperSize: sessionStore.paperSize,
      lastReceipt: sessionStore.lastReceipt,
    );
  }

  Future<void> startScan() async {
    state = state.copyWith(scanning: true, lastError: null);
    try {
      final devices = await printerService.scan(
        timeout: const Duration(seconds: 6),
      );
      state = state.copyWith(scanning: false, devices: devices);
    } catch (e) {
      state = state.copyWith(scanning: false, lastError: _message(e));
    }
  }

  Future<void> connect(PrinterDevice device) async {
    state = state.copyWith(busy: true, lastError: null);
    try {
      await printerService.connect(device);
      await sessionStore.saveLastPrinter(device);
      state = state.copyWith(
        busy: false,
        connected: true,
        connectedDevice: device,
      );
    } catch (e) {
      state = state.copyWith(busy: false, connected: false, lastError: _message(e));
    }
  }

  Future<void> disconnect() async {
    state = state.copyWith(busy: true, lastError: null);
    try {
      await printerService.disconnect();
      await sessionStore.clearLastPrinter();
      state = state.copyWith(
        busy: false,
        connected: false,
        connectedDevice: null,
      );
    } catch (e) {
      state = state.copyWith(
        busy: false,
        connected: false,
        connectedDevice: null,
        lastError: _message(e),
      );
    }
  }

  Future<void> setPaperSize(PaperSize size) async {
    await sessionStore.savePaperSize(size);
    state = state.copyWith(paperSize: size);
  }

  Future<void> testPrint() async {
    state = state.copyWith(busy: true, lastError: null);
    try {
      await printerService.testPrint();
      state = state.copyWith(busy: false);
    } catch (e) {
      state = state.copyWith(busy: false, lastError: _message(e));
    }
  }

  Future<void> printReceipt(ReceiptData receipt) async {
    state = state.copyWith(
      busy: true,
      lastError: null,
      lastReceipt: receipt,
    );
    await sessionStore.saveLastReceipt(receipt);
    try {
      await printerService.printReceipt(receipt, state.paperSize);
      state = state.copyWith(busy: false);
    } catch (e) {
      state = state.copyWith(busy: false, lastError: _message(e));
    }
  }

  Future<void> reprint() async {
    final receipt = state.lastReceipt;
    if (receipt == null) {
      state = state.copyWith(lastError: 'Belum ada struk untuk dicetak ulang.');
      return;
    }
    await printReceipt(receipt);
  }

  String _message(Object e) {
    if (e is ApiException) return e.message;
    return e.toString();
  }
}

final printerNotifierProvider =
    StateNotifierProvider<PrinterNotifier, PrinterState>((ref) {
  return PrinterNotifier(
    printerService: ref.watch(printerServiceProvider),
    sessionStore: ref.watch(sessionStoreProvider),
  );
});