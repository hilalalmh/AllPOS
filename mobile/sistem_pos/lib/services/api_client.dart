import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => message;
}

class ApiClient {
  ApiClient({
    required String baseUrl,
    this.tokenProvider,
    this.refreshTokenProvider,
    this.onTokensSaved,
    this.onAuthExpired,
    this.timeout = const Duration(seconds: 20),
  }) : baseUrl = baseUrl.replaceFirst(RegExp(r'/+$'), '');

  final String baseUrl;
  final String? Function()? tokenProvider;
  final String? Function()? refreshTokenProvider;
  final Future<void> Function(String accessToken, String refreshToken)?
      onTokensSaved;
  final Future<void> Function()? onAuthExpired;
  final Duration timeout;

  Future<bool>? _refreshing;

  Future<dynamic> get(String path) => _send('GET', path);

  Future<dynamic> post(String path, [Object? body]) => _send('POST', path, body);

  Future<dynamic> put(String path, [Object? body]) => _send('PUT', path, body);

  Future<dynamic> delete(String path, [Object? body]) =>
      _send('DELETE', path, body);

  Future<dynamic> _send(String method, String path, [Object? body]) =>
      _sendWithRetry(method, path, body, retried: false);

  Future<dynamic> _sendWithRetry(
    String method,
    String path,
    Object? body, {
    required bool retried,
  }) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    final token = tokenProvider?.call();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    final refreshToken = refreshTokenProvider?.call();
    final hadSession = (refreshToken?.isNotEmpty ?? false) || (token?.isNotEmpty ?? false);

    late http.Response response;
    try {
      final encoded = body == null ? null : jsonEncode(body);
      final request = _perform(method, uri, headers, encoded);
      response = await request.timeout(timeout);
    } catch (_) {
      rethrow;
    }
    final data = _decode(response);

    if (response.statusCode == 401 && !retried && await _refresh()) {
      return _sendWithRetry(method, path, body, retried: true);
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      if (response.statusCode == 401 && hadSession) {
        await onAuthExpired?.call();
        throw const ApiException(401, 'Sesi berakhir. Silakan masuk kembali.');
      }
      throw ApiException(response.statusCode, _errorMessage(data, response.statusCode));
    }
    return data;
  }

  Future<bool> _refresh() {
    final pending = _refreshing;
    if (pending != null) return pending;
    final future = _refreshInner();
    _refreshing = future;
    future.whenComplete(() {
      if (identical(_refreshing, future)) _refreshing = null;
    });
    return future;
  }

  Future<bool> _refreshInner() async {
    final refreshToken = refreshTokenProvider?.call();
    if (refreshToken == null || refreshToken.isEmpty) return false;
    try {
      final uri = Uri.parse('$baseUrl/api/v1/auth/refresh');
      final headers = <String, String>{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      };
      final response = await http
          .post(
            uri,
            headers: headers,
            body: jsonEncode({'refresh_token': refreshToken}),
          )
          .timeout(timeout);
      if (response.statusCode < 200 || response.statusCode >= 300) {
        return false;
      }
      final data = _decode(response);
      if (data is! Map<String, dynamic>) return false;
      final access = data['access_token'];
      final refresh = data['refresh_token'];
      if (access is! String || refresh is! String) return false;
      await onTokensSaved?.call(access, refresh);
      return true;
    } on SocketException {
      rethrow;
    } on TimeoutException {
      rethrow;
    } on http.ClientException {
      rethrow;
    } catch (_) {
      // Respons HTTP non-2xx berarti sesi benar-benar berakhir (token invalid).
      return false;
    }
  }

  Future<http.Response> _perform(
    String method,
    Uri uri,
    Map<String, String> headers,
    String? encoded,
  ) {
    switch (method) {
      case 'GET':
        return http.get(uri, headers: headers);
      case 'POST':
        return http.post(uri, headers: headers, body: encoded);
      case 'PUT':
        return http.put(uri, headers: headers, body: encoded);
      case 'DELETE':
        return http.delete(uri, headers: headers, body: encoded);
      default:
        throw ApiException(0, 'Metode HTTP tidak dikenal: $method');
    }
  }

  dynamic _decode(http.Response response) {
    if (response.body.isEmpty) return null;
    if (response.headers['content-type']?.contains('application/json') ?? false) {
      return jsonDecode(utf8.decode(response.bodyBytes));
    }
    return utf8.decode(response.bodyBytes);
  }

  String _errorMessage(dynamic data, int statusCode) {
    if (data is Map<String, dynamic>) {
      final detail = data['detail'];
      if (detail is String && detail.isNotEmpty) return detail;
      if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map<String, dynamic> && first['msg'] != null) {
          return first['msg'].toString();
        }
        return first.toString();
      }
    }
    if (data is String && data.isNotEmpty) return data;
    return 'Terjadi kesalahan (HTTP $statusCode)';
  }
}