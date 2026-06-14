from decimal import Decimal, InvalidOperation


def format_currency_ars(value):
    if value in (None, ""):
        return ""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ""
    rounded = amount.quantize(Decimal("1")) if amount == amount.to_integral() else amount.quantize(Decimal("0.01"))
    integer_part, _, decimal_part = f"{rounded:f}".partition(".")
    sign = ""
    if integer_part.startswith("-"):
        sign = "-"
        integer_part = integer_part[1:]
    groups = []
    while integer_part:
        groups.append(integer_part[-3:])
        integer_part = integer_part[:-3]
    formatted = ".".join(reversed(groups or ["0"]))
    if decimal_part and int(decimal_part) != 0:
        formatted = f"{formatted},{decimal_part.rstrip('0')}"
    return f"$ {sign}{formatted}"
