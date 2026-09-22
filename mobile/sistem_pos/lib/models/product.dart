class Product {
  const Product({
    required this.id,
    required this.categoryId,
    required this.name,
    required this.price,
    this.description,
    this.sku,
    this.imageUrl,
    this.isActive = true,
  });

  final int id;
  final int categoryId;
  final String name;
  final num price;
  final String? description;
  final String? sku;
  final String? imageUrl;
  final bool isActive;

  factory Product.fromJson(Map<String, dynamic> json) => Product(
        id: json['id'] as int,
        categoryId: json['category_id'] as int,
        name: json['name'] as String,
        price: json['price'] as num,
        description: json['description'] as String?,
        sku: json['sku'] as String?,
        imageUrl: json['image_url'] as String?,
        isActive: json['is_active'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'category_id': categoryId,
        'name': name,
        'price': price,
        'description': description,
        'sku': sku,
        'image_url': imageUrl,
        'is_active': isActive,
      };
}