class User {
  const User({
    required this.id,
    required this.roleId,
    required this.username,
    required this.fullName,
    required this.isActive,
    required this.role,
  });

  final int id;
  final int roleId;
  final String username;
  final String fullName;
  final bool isActive;
  final String role;

  factory User.fromJson(Map<String, dynamic> json) => User(
        id: json['id'] as int,
        roleId: json['role_id'] as int,
        username: json['username'] as String,
        fullName: json['full_name'] as String,
        isActive: json['is_active'] as bool,
        role: json['role'] as String,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'role_id': roleId,
        'username': username,
        'full_name': fullName,
        'is_active': isActive,
        'role': role,
      };
}