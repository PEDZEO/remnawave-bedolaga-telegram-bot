from __future__ import annotations

from decimal import ROUND_HALF_UP, ROUND_UP, Decimal, InvalidOperation
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.tariff import get_tariff_by_id
from app.database.models import Subscription, User

from .common import parse_period_identifier


def resolve_renewal_period(period_days_raw: int | str | None, period_id: str | None) -> int:
    period_days: int | None = None
    if period_days_raw is not None:
        try:
            period_days = int(period_days_raw)
        except (TypeError, ValueError) as error:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={'code': 'invalid_period', 'message': 'Invalid renewal period'},
            ) from error

    if period_days is None:
        period_days = parse_period_identifier(period_id)

    if period_days is None or period_days <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_period', 'message': 'Invalid renewal period'},
        )

    return period_days


async def build_tariff_renewal_pricing(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    period_days: int,
) -> dict[str, Any] | None:
    tariff_id = getattr(subscription, 'tariff_id', None)
    if not tariff_id:
        return None

    tariff = await get_tariff_by_id(db, tariff_id)
    if not tariff or not tariff.period_prices:
        return None

    available_periods = [int(period) for period in tariff.period_prices.keys()]
    if period_days not in available_periods:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'period_unavailable',
                'message': 'Selected renewal period is not available for this tariff',
            },
        )

    original_price_kopeks = tariff.period_prices.get(str(period_days), tariff.period_prices.get(period_days, 0))
    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )

    discount_percent = 0
    if promo_group:
        raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
        for key, value in raw_discounts.items():
            try:
                if int(key) == period_days:
                    discount_percent = max(0, min(100, int(value)))
                    break
            except (TypeError, ValueError):
                continue

    final_total = (
        int(original_price_kopeks * (100 - discount_percent) / 100)
        if discount_percent > 0
        else int(original_price_kopeks)
    )
    return {
        'period_days': period_days,
        'original_price_kopeks': int(original_price_kopeks),
        'discount_percent': discount_percent,
        'final_total': final_total,
        'tariff_id': tariff.id,
    }


def ensure_classic_renewal_period_available(period_days: int) -> None:
    available_periods = [period for period in settings.get_available_renewal_periods() if period > 0]
    if period_days in available_periods:
        return

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail={'code': 'period_unavailable', 'message': 'Selected renewal period is not available'},
    )


def resolve_renewal_method(method: str | None) -> str:
    return (method or '').strip().lower()


def ensure_renewal_method_or_balance(*, method: str, final_total: int, balance_kopeks: int) -> None:
    if method:
        return

    if final_total > 0 and balance_kopeks < final_total:
        missing = final_total - balance_kopeks
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': 'Not enough funds to renew the subscription',
                'missing_amount_kopeks': missing,
            },
        )

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail={
            'code': 'payment_method_required',
            'message': 'Payment method is required when balance is insufficient',
        },
    )


def ensure_renewal_method_supported(method: str, supported_methods: set[str]) -> None:
    if method in supported_methods:
        return

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail={'code': 'unsupported_method', 'message': 'Payment method is not supported for renewal'},
    )


def ensure_cryptobot_amount_limits(
    *,
    missing_amount: int,
    min_amount_kopeks: int,
    max_amount_kopeks: int,
) -> None:
    if missing_amount < min_amount_kopeks:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'amount_below_minimum',
                'message': f'Amount is below minimum ({min_amount_kopeks / 100:.2f} RUB)',
            },
        )

    if missing_amount > max_amount_kopeks:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'amount_above_maximum',
                'message': f'Amount exceeds maximum ({max_amount_kopeks / 100:.2f} RUB)',
            },
        )


def compute_amount_usd_from_kopeks(missing_amount: int, rate: float) -> float:
    try:
        decimal_amount = Decimal(missing_amount) / Decimal(100) / Decimal(str(rate))
        amount_usd = float(decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_UP))
    except (InvalidOperation, ValueError) as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'conversion_failed', 'message': 'Unable to convert amount to USD'},
        ) from error

    if amount_usd <= 0:
        amount_usd = float(decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    return amount_usd


def extract_cryptobot_payment_urls(result: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    payment_url = (
        result.get('web_app_invoice_url') or result.get('mini_app_invoice_url') or result.get('bot_invoice_url')
    )
    if not payment_url:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={'code': 'payment_url_missing', 'message': 'Failed to obtain payment url'},
        )

    extra_payload = {
        'bot_invoice_url': result.get('bot_invoice_url'),
        'mini_app_invoice_url': result.get('mini_app_invoice_url'),
        'web_app_invoice_url': result.get('web_app_invoice_url'),
    }
    return payment_url, {key: value for key, value in extra_payload.items() if value}
