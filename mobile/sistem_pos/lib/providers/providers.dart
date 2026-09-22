import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../core/app_config.dart';
import '../models/product.dart';
import '../models/receipt.dart';
import '../models/user.dart';
import '../repositories/auth_repository.dart';
import '../repositories/product_repository.dart';
import '../repositories/session_store.dart';
import '../services/api_client.dart';
import '../services/printer_service.dart';
import '../services/receipt_service.dart';

final sharedPrefsProvider = Provider<SharedPreferences>(
  (ref) => throw UnimplementedError('Override sharedPrefsProvider di main()'),
);

final sessionStoreProvider = Provider<SessionStore>(
  (ref) => SessionStore(ref.watch(sharedPrefsProvider)),
);

final apiClientProvider = Provider<ApiClient>(
  (ref) => ApiClient(
    baseUrl: AppConfig.apiBaseUrl,
    tokenProvider: () => ref.watch(sessionStoreProvider).accessToken,
  ),
);

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    api: ref.watch(apiClientProvider),
    store: ref.watch(sessionStoreProvider),
  ),
);

class AuthState {
  const AuthState({this.user, this.loading = false, this.error});

  final User? user;
  final bool loading;
  final String? error;

  bool get isAuthenticated => user != null;

  AuthState copyWith({User? user, bool? loading, String? error}) => AuthState(
        user: user ?? this.user,
        loading: loading ?? this.loading,
        error: error ?? this.error,
      );
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier(this._repo) : super(AuthState(user: _repo.store.user));

  final AuthRepository _repo;

  Future<void> login(String username, String password) async {
    state = state.copyWith(loading: true, error: null);
    try {
      final user = await _repo.login(username.trim(), password);
      state = state.copyWith(user: user, loading: false);
    } catch (e) {
      state = state.copyWith(loading: false, error: _message(e));
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    state = const AuthState();
  }

  String _message(Object e) {
    if (e is ApiException) return e.message;
    return e.toString();
  }
}

final authNotifierProvider =
    StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier(ref.watch(authRepositoryProvider));
});

final productRepositoryProvider = Provider<ProductRepository>(
  (ref) => ProductRepository(ref.watch(apiClientProvider)),
);

final productsProvider = FutureProvider<List<Product>>(
  (ref) => ref.watch(productRepositoryProvider).fetchProducts(),
);

final receiptServiceProvider = Provider<ReceiptService>(
  (ref) => ReceiptService(),
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
    PrinterDevice? connectedDevice,
    PaperSize? paperSize,
    bool? busy,
    ReceiptData? lastReceipt,
    String? lastError,
  }) =>
      PrinterState(
        available: available ?? this.available,
        bluetoothOn: bluetoothOn ?? this.bluetoothOn,
        scanning: scanning ?? this.scanning,
        connected: connected ?? this.connected,
        devices: devices ?? this.devices,
        connectedDevice: connectedDevice ?? this.connectedDevice,
        paperSize: paperSize ?? this.paperSize,
        busy: busy ?? this.busy,
        lastReceipt: lastReceipt ?? this.lastReceipt,
        lastError: lastError ?? this.lastError,
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
      state = state.copyWith(busy: false, connected: false, connectedDevice: null);
    } catch (e) {
      state = state.copyWith(busy: false, lastError: _message(e));
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