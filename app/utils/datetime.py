from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

ARGENTINA_TZ = timezone(timedelta(hours=-3), name="America/Argentina/Buenos_Aires")


def argentina_now():
    return datetime.now(ARGENTINA_TZ)


def format_time_hs(value):
    if not value:
        return ""
    return value.strftime("%H:%Mhs")


def format_datetime_argentina(value):
    if not value:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ARGENTINA_TZ).strftime("%Y-%m-%d %H:%Mhs")


def format_duration_hs(value):
    if value in (None, ""):
        return "00:00hs"
    try:
        decimal_hours = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "00:00hs"
    total_minutes = int((decimal_hours * Decimal("60")).quantize(Decimal("1")))
    hours, minutes = divmod(max(total_minutes, 0), 60)
    return f"{hours:02d}:{minutes:02d}hs"


def format_duration_input(value):
    return format_duration_hs(value).removesuffix("hs")
