from datetime import date, datetime, time
from zoneinfo import ZoneInfo

BUSINESS_TZ = ZoneInfo("Asia/Jakarta")


def start_datetime(d: date) -> datetime:
    """Awal hari (00:00:00.000000) di zona bisnis WIB, tetap aware."""
    return datetime.combine(d, time.min, tzinfo=BUSINESS_TZ)


def end_datetime(d: date) -> datetime:
    """Akhir hari (23:59:59.999999) di zona bisnis WIB, tetap aware."""
    return datetime.combine(d, time.max, tzinfo=BUSINESS_TZ)


def business_day_bounds(
    start_date: date | None, end_date: date | None
) -> tuple[datetime, datetime]:
    """Konversi rentang tanggal (lokal bisnis WIB) menjadi batas datetime aware.

    Kolom `created_at` bertipe `timestamptz` (disimpan UTC). Input tanggal dari
    client memakai kalender lokal (Asia/Jakarta), jadi batas dibuat aware di zona
    bisnis agar perbandingan di DB konsisten (tidak bergeser 7 jam).
    """
    today = datetime.now(BUSINESS_TZ).date()
    start = start_date or today
    end = end_date or today
    if end < start:
        end = start
    return start_datetime(start), end_datetime(end)