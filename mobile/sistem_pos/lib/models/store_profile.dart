class StoreProfile {
  const StoreProfile({
    required this.storeName,
    this.address = '',
    this.phone = '',
    this.footer = 'TERIMA KASIH ~ SILAHKAN DATANG KEMBALI',
  });

  static const defaultProfile = StoreProfile(storeName: 'SISTEM POS');

  final String storeName;
  final String address;
  final String phone;
  final String footer;

  factory StoreProfile.fromJson(Map<String, dynamic> json) => StoreProfile(
        storeName: (json['store_name'] as String?) ?? 'SISTEM POS',
        address: (json['address'] as String?) ?? '',
        phone: (json['phone'] as String?) ?? '',
        footer: (json['footer'] as String?) ??
            'TERIMA KASIH ~ SILAHKAN DATANG KEMBALI',
      );

  Map<String, dynamic> toJson() => {
        'store_name': storeName,
        'address': address,
        'phone': phone,
        'footer': footer,
      };
}