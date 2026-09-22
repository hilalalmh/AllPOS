import 'dart:convert';

import 'package:http/http.dart' as http;

Future<void> main() async {
  final base = const String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );
  print('Cek kesehatan API: $base');
  final health = await http.get(Uri.parse('$base/api/v1/health'));
  print('GET /api/v1/health -> ${health.statusCode} ${utf8.decode(health.bodyBytes)}');
  if (health.statusCode != 200) {
    throw StateError('Kesehatan API gagal');
  }

  final login = await http.post(
    Uri.parse('$base/api/v1/auth/login'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({'username': 'owner', 'password': 'admin123'}),
  );
  print('POST /api/v1/auth/login -> ${login.statusCode}');
  if (login.statusCode != 200) {
    throw StateError('Login gagal: ${login.body}');
  }
  final token = (jsonDecode(login.body) as Map<String, dynamic>)['access_token'] as String;

  final products = await http.get(
    Uri.parse('$base/api/v1/products?page=1&page_size=50'),
    headers: {'Authorization': 'Bearer $token'},
  );
  print('GET /api/v1/products -> ${products.statusCode}');
  if (products.statusCode != 200) {
    throw StateError('Ambil produk gagal');
  }
  final items = (jsonDecode(products.body) as Map<String, dynamic>)['items'] as List<dynamic>;
  print('Produk tersedia: ${items.map((e) => (e as Map<String, dynamic>)['name']).toList()}');

  print('OK: Flutter (Dart) terhubung ke backend FastAPI.');
}