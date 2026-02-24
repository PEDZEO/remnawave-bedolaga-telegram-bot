from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import structlog
from pydantic import ValidationError

from app.config import settings

from ....schemas.miniapp import MiniAppPaymentIframeConfig


logger = structlog.get_logger(__name__)


def normalize_amount_kopeks(
    amount_rubles: float | None,
    amount_kopeks: int | None,
) -> int | None:
    if amount_kopeks is not None:
        try:
            normalized = int(amount_kopeks)
        except (TypeError, ValueError):
            return None
        return normalized if normalized >= 0 else None

    if amount_rubles is None:
        return None

    try:
        decimal_amount = Decimal(str(amount_rubles)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None

    normalized = int((decimal_amount * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return normalized if normalized >= 0 else None


def build_mulenpay_iframe_config() -> MiniAppPaymentIframeConfig | None:
    expected_origin = settings.get_mulenpay_expected_origin()
    if not expected_origin:
        return None

    try:
        return MiniAppPaymentIframeConfig(expected_origin=expected_origin)
    except ValidationError as error:  # pragma: no cover - defensive logging
        logger.error("Invalid MulenPay expected origin ''", expected_origin=expected_origin, error=error)
        return None
