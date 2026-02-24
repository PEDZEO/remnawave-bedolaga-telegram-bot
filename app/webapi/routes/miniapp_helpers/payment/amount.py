from datetime import UTC, datetime
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal, InvalidOperation
from uuid import uuid4

from app.config import settings


_DECIMAL_ONE_HUNDRED = Decimal(100)
_DECIMAL_CENT = Decimal('0.01')


def current_request_timestamp() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def compute_stars_min_amount() -> int | None:
    try:
        rate = Decimal(str(settings.get_stars_rate()))
    except (InvalidOperation, TypeError):
        return None

    if rate <= 0:
        return None

    return int((rate * _DECIMAL_ONE_HUNDRED).to_integral_value(rounding=ROUND_HALF_UP))


def normalize_stars_amount(amount_kopeks: int) -> tuple[int, int]:
    try:
        rate = Decimal(str(settings.get_stars_rate()))
    except (InvalidOperation, TypeError):
        raise ValueError('Stars rate is not configured')

    if rate <= 0:
        raise ValueError('Stars rate must be positive')

    amount_rubles = Decimal(amount_kopeks) / _DECIMAL_ONE_HUNDRED
    stars_amount = int((amount_rubles / rate).to_integral_value(rounding=ROUND_FLOOR))
    if stars_amount <= 0:
        stars_amount = 1

    normalized_rubles = (Decimal(stars_amount) * rate).quantize(
        _DECIMAL_CENT,
        rounding=ROUND_HALF_UP,
    )
    normalized_amount_kopeks = int((normalized_rubles * _DECIMAL_ONE_HUNDRED).to_integral_value(rounding=ROUND_HALF_UP))

    return stars_amount, normalized_amount_kopeks


def build_balance_invoice_payload(user_id: int, amount_kopeks: int) -> str:
    suffix = uuid4().hex[:8]
    return f'balance_{user_id}_{amount_kopeks}_{suffix}'
