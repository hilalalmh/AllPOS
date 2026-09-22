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

  Future<void> logout() => store.clear();
}