String twoDigits(int v) => v.toString().padLeft(2, '0');

String formatDateIndo(DateTime local) =>
    '${twoDigits(local.day)}-${twoDigits(local.month)}-${local.year} '
    '${twoDigits(local.hour)}:${twoDigits(local.minute)}';