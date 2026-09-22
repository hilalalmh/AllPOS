import 'dart:convert';

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
    required this.baseUrl,
    this.tokenProvider,
  });

  final String baseUrl;
  final String? Function()? tokenProvider;

  Future<dynamic> get(String path) => _send('GET', path);

  Future<dynamic> post(String path, [Object? body]) => _send('POST', path, body);

  Future<dynamic> put(String path, [Object? body]) => _send('PUT', path, body);

  Future<dynamic> delete(String path, [Object? body]) =>
      _send('DELETE', path, body);

  Future<dynamic> _send(String method, String path, [Object? body]) async {
    final uri = Uri.parse('$baseUrl$path');
    final headers = <String, String>{
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    };
    final token = tokenProvider?.call();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }

    late http.Response response;
    final encoded = body == null ? null : jsonEncode(body);
    switch (method) {
      case 'GET':
        response = await http.get(uri, headers: headers);
        break;
      case 'POST':
        response = await http.post(uri, headers: headers, body: encoded);
        break;
      case 'PUT':
        response = await http.put(uri, headers: headers, body: encoded);
        break;
      case 'DELETE':
        response = await http.delete(uri, headers: headers, body: encoded);
        break;
      default:
        throw ApiException(0, 'Metode HTTP tidak dikenal: $method');
    }

    final data = _decode(response);
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(response.statusCode, _errorMessage(data, response.statusCode));
    }
    return data;
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