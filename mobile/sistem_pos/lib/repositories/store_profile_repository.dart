import '../models/store_profile.dart';
import '../services/api_client.dart';

class StoreProfileRepository {
  StoreProfileRepository({required this.api});

  final ApiClient api;

  Future<StoreProfile> fetch() async {
    final response = await api.get('/api/v1/store-profile');
    return StoreProfile.fromJson(response as Map<String, dynamic>);
  }
}