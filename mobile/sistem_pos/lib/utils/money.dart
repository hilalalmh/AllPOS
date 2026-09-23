String formatRupiah(num value, {bool showSymbol = false}) {
  final isNegative = value < 0;
  final abs = value.abs();
  final whole = abs.floor();
  final digits = whole.toString();
  final buffer = StringBuffer();
  for (var i = 0; i < digits.length; i++) {
    if (i > 0 && (digits.length - i) % 3 == 0) {
      buffer.write('.');
    }
    buffer.write(digits[i]);
  }
  final symbol = showSymbol ? 'Rp ' : 'Rp';
  return '$symbol${isNegative ? '-' : ''}$buffer';
}