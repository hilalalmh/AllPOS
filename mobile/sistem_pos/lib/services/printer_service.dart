import 'package:bluetooth_print/bluetooth_print.dart' as bt;
import 'package:bluetooth_print/bluetooth_print_model.dart' as bt_model;

import '../models/receipt.dart';
import 'receipt_service.dart';

enum PaperSize {
  mm58('58 mm'),
  mm80('80 mm');

  const PaperSize(this.label);

  final String label;
}

class PrinterDevice {
  const PrinterDevice({
    this.name,
    this.address,
    this.type = 0,
    this.connected = false,
  });

  final String? name;
  final String? address;
  final int type;
  final bool connected;

  String get displayName => (name == null || name!.isEmpty) ? address ?? 'Printer' : name!;

  bt_model.BluetoothDevice toBluetoothDevice() => bt_model.BluetoothDevice()
    ..name = name
    ..address = address
    ..type = type;

  Map<String, dynamic> toJson() => {
        'name': name,
        'address': address,
        'type': type,
      };

  factory PrinterDevice.fromJson(Map<String, dynamic> json) => PrinterDevice(
        name: json['name'] as String?,
        address: json['address'] as String?,
        type: json['type'] as int? ?? 0,
      );
}

class PrinterUnavailableException implements Exception {
  const PrinterUnavailableException();

  @override
  String toString() => 'Bluetooth tidak tersedia atau sedang mati.';
}

class PrinterConnectException implements Exception {
  const PrinterConnectException();

  @override
  String toString() => 'Printer belum terhubung. Hubungkan dahulu.';
}

class PrinterService {
  PrinterService(this._receiptService);

  final ReceiptService _receiptService;
  final bt.BluetoothPrint _bt = bt.BluetoothPrint.instance;

  Future<bool> get isAvailable => _bt.isAvailable;

  Future<bool> get isOn => _bt.isOn;

  Future<bool> get isConnected async => (await _bt.isConnected) ?? false;

  Future<List<PrinterDevice>> scan({
    Duration timeout = const Duration(seconds: 6),
  }) async {
    final devices = await _bt.startScan(timeout: timeout);
    return devices
        .map(
          (d) => PrinterDevice(
            name: d.name,
            address: d.address,
            type: d.type ?? 0,
            connected: d.connected ?? false,
          ),
        )
        .toList();
  }

  Future<void> connect(PrinterDevice device) async {
    final result = await _bt.connect(device.toBluetoothDevice());
    if (result != true) {
      throw const PrinterConnectException();
    }
  }

  Future<void> disconnect() async {
    await _bt.disconnect();
  }

  Future<void> testPrint() async {
    await _ensureConnected();
    await _bt.printTest();
  }

  Future<void> printReceipt(ReceiptData receipt, PaperSize paper) async {
    await _ensureConnected();
    final lines = _receiptService.buildLines(receipt, paper);
    await _bt.printReceipt(_receiptService.printerConfig(paper), lines);
  }

  Future<void> _ensureConnected() async {
    if (!await _bt.isAvailable || !await _bt.isOn) {
      throw const PrinterUnavailableException();
    }
    final connected = await _bt.isConnected;
    if (connected != true) {
      throw const PrinterConnectException();
    }
  }
}