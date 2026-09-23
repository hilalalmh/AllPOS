import 'package:flutter_test/flutter_test.dart';

import 'package:sistem_pos/services/api_client.dart';

void main() {
  test('ApiClient menghapus slash di akhir base URL', () {
    final api = ApiClient(baseUrl: 'http://10.0.2.2:8000///');
    expect(api.baseUrl, 'http://10.0.2.2:8000');
  });

  test('ApiClient punya timeout default 20 detik', () {
    final api = ApiClient(baseUrl: 'http://10.0.2.2:8000');
    expect(api.timeout, const Duration(seconds: 20));
  });
}