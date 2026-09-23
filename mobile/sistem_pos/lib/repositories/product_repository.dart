import '../models/product.dart';
import '../services/api_client.dart';

class ProductPage {
  const ProductPage({
    required this.items,
    required this.total,
    required this.page,
  });

  final List<Product> items;
  final int total;
  final int page;
}

class ProductRepository {
  ProductRepository(this._api);

  final ApiClient _api;

  Future<ProductPage> fetchPage({String? query, int page = 1, int pageSize = 100}) async {
    final params = <String, String>{
      'page': '$page',
      'page_size': '$pageSize',
    };
    if (query != null && query.isNotEmpty) {
      params['q'] = query;
    }
    final queryString = params.entries.map((e) => '${e.key}=${e.value}').join('&');
    final response = await _api.get('/api/v1/products?$queryString');
    final items = (response['items'] as List<dynamic>)
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
    return ProductPage(
      items: items,
      total: response['total'] as int? ?? items.length,
      page: response['page'] as int? ?? page,
    );
  }
}