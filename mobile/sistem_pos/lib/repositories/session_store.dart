import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/receipt.dart';
import '../models/store_profile.dart';
import '../models/user.dart';
import '../services/printer_service.dart';

class SessionStore {
  SessionStore(this._prefs);

  static const _accessKey = 'session.access_token';
  static const _refreshKey = 'session.refresh_token';
  static const _userKey = 'session.user';
  static const _printerNameKey = 'printer.name';
  static const _printerAddressKey = 'printer.address';
  static const _printerTypeKey = 'printer.type';
  static const _paperSizeKey = 'printer.paper_size';
  static const _lastReceiptKey = 'printer.last_receipt';
  static const _storeProfileKey = 'store.profile';

  final SharedPreferences _prefs;

  String? get accessToken => _prefs.getString(_accessKey);

  String? get refreshToken => _prefs.getString(_refreshKey);

  User? get user {
    final raw = _prefs.getString(_userKey);
    if (raw == null) return null;
    try {
      return User.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> saveTokens(String accessToken, String refreshToken) async {
    await _prefs.setString(_accessKey, accessToken);
    await _prefs.setString(_refreshKey, refreshToken);
  }

  Future<void> saveUser(User user) async {
    await _prefs.setString(_userKey, jsonEncode(user.toJson()));
  }

  Future<void> clear() async {
    await _prefs.remove(_accessKey);
    await _prefs.remove(_refreshKey);
    await _prefs.remove(_userKey);
  }

  PaperSize get paperSize =>
      _prefs.getString(_paperSizeKey) == '80' ? PaperSize.mm80 : PaperSize.mm58;

  Future<void> savePaperSize(PaperSize size) async {
    await _prefs.setString(_paperSizeKey, size == PaperSize.mm80 ? '80' : '58');
  }

  PrinterDevice? get lastPrinter {
    final name = _prefs.getString(_printerNameKey);
    final address = _prefs.getString(_printerAddressKey);
    if (address == null) return null;
    return PrinterDevice(
      name: name,
      address: address,
      type: _prefs.getInt(_printerTypeKey) ?? 0,
    );
  }

  Future<void> saveLastPrinter(PrinterDevice device) async {
    await _prefs.setString(_printerNameKey, device.name ?? '');
    await _prefs.setString(_printerAddressKey, device.address ?? '');
    await _prefs.setInt(_printerTypeKey, device.type);
  }

  Future<void> clearLastPrinter() async {
    await _prefs.remove(_printerNameKey);
    await _prefs.remove(_printerAddressKey);
    await _prefs.remove(_printerTypeKey);
  }

  Future<void> clearLastReceipt() async {
    await _prefs.remove(_lastReceiptKey);
  }

  ReceiptData? get lastReceipt {
    final raw = _prefs.getString(_lastReceiptKey);
    if (raw == null) return null;
    try {
      return ReceiptData.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return null;
    }
  }

  Future<void> saveLastReceipt(ReceiptData receipt) async {
    await _prefs.setString(_lastReceiptKey, jsonEncode(receipt.toJson()));
  }

  StoreProfile get storeProfile {
    final raw = _prefs.getString(_storeProfileKey);
    if (raw == null) return StoreProfile.defaultProfile;
    try {
      return StoreProfile.fromJson(jsonDecode(raw) as Map<String, dynamic>);
    } catch (_) {
      return StoreProfile.defaultProfile;
    }
  }

  Future<void> saveStoreProfile(StoreProfile profile) async {
    await _prefs.setString(_storeProfileKey, jsonEncode(profile.toJson()));
  }
}