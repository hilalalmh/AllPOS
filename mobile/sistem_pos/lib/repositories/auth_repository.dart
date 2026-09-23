import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/user.dart';
import '../services/api_client.dart';
import 'session_store.dart';

class AuthRepository {
  AuthRepository({required this.api, required this.store});

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
    try {
      final me = await api.get('/api/v1/auth/me');
      final user = User.fromJson(me as Map<String, dynamic>);
      await store.saveUser(user);
      return user;
    } catch (_) {
      // Profil gagal dimuat: jangan biarkan sesi parsial (token tersimpan
      // tapi user kosong) yang bikin UI menampilkan layar rusak.
      await store.clear();
      rethrow;
    }
  }

  Future<void> logout() async {
    // Cabut refresh token di server (best effort, tanpa menahan UI), lalu
    // bersihkan lokal secepatnya agar logout tidak menggantung 5 detik.
    final token = store.refreshToken;
    if (token != null && token.isNotEmpty) {
      unawaited(
        http
            .post(
              Uri.parse('${api.baseUrl}/api/v1/auth/logout'),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'refresh_token': token}),
            )
            .timeout(const Duration(seconds: 5)),
      );
    }
    await store.clear();
  }
}
