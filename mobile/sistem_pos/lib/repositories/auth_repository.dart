import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/user.dart';
import '../services/api_client.dart';
import 'session_store.dart';

class AuthRepository {
  AuthRepository({
    required this.api,
    required this.store,
  });

  final ApiClient api;
  final SessionStore store;

  Future<User> login(String username, String password) async {
    final response = await api.post('/api/v1/auth/login', {
      'username': username,
      'password': password,
    });
    await store.saveTokens(
      response['access_token'] as String,
      response['refresh_token'] as String,
    );
    final me = await api.get('/api/v1/auth/me');
    final user = User.fromJson(me as Map<String, dynamic>);
    await store.saveUser(user);
    return user;
  }

  Future<void> logout() async {
    // Cabut refresh token di server (best effort), lalu bersihkan lokal.
    final token = store.refreshToken;
    if (token != null && token.isNotEmpty) {
      try {
        await http
            .post(
              Uri.parse('${api.baseUrl}/api/v1/auth/logout'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'refresh_token': token}),
            )
            .timeout(const Duration(seconds: 5));
      } catch (_) {
        // Kegagalan jaringan tidak menghalangi logout lokal.
      }
    }
    await store.clear();
  }
}