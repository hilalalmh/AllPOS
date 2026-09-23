import '../models/transaction.dart';
import '../services/api_client.dart';

class TransactionRepository {
  TransactionRepository(this._api);

  final ApiClient _api;

  Future<Transaction> create({
    required List<Map<String, dynamic>> items,
    required String paymentMethod,
    required num paidAmount,
    num discount = 0,
  }) async {
    final response = await _api.post(
      '/api/v1/transactions',
      {
        'items': items,
        'payment_method': paymentMethod,
        'paid_amount': paidAmount,
        'discount': discount,
      },
    );
    return Transaction.fromJson(response as Map<String, dynamic>);
  }

  Future<Transaction> fetchTransaction(int id) async {
    final response = await _api.get('/api/v1/transactions/$id');
    return Transaction.fromJson(response as Map<String, dynamic>);
  }
}