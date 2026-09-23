String formatRupiah(num value, {bool showSymbol = false}) {
  final isNegative = value < 0;
  final abs = value.abs();
  // Bulatkan ke sen (bukan floor) agar nilai seperti 18.000,5 tidak diam-diam
  // kehilangan sennya; sen hanya ditampilkan bila ada (konsisten dengan struk).
  final totalCents = (abs * 100).round();
  final whole = totalCents ~/ 100;
  final cents = totalCents % 100;
  final digits = whole.toString();
  final buffer = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) {
      buffer.write('.');
    }
    buffer.write(digits[i]);
  }
  if (cents != 0) {
    buffer.write(',${cents.toString().padLeft(2, '0')}');
  }
  final symbol = showSymbol ? 'Rp ' : 'Rp';
  return '$symbol${isNegative ? '-' : ''}$buffer';
}