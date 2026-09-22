import '../models/product.dart';
import '../services/api_client.dart';

class ProductRepository {
  ProductRepository(this._api);

  final ApiClient _api;

  Future<List<Product>> fetchProducts({String? query, int page = 1, int pageSize = 50}) async {
    final params = <String, String>{
      'page': '$page',
      'page_size': '$pageSize',
    };
    if (query != null && query.isNotEmpty) {
      params['q'] = query;
    }
    final queryString = params.entries.map((e) => '${e.key}=${e.value}').join('&');
    final response = await _api.get('/api/v1/products?$queryString');
    final items = response['items'] as List<dynamic>;
    return items
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}