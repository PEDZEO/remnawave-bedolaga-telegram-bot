from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.tariff import get_tariff_by_id


@dataclass(slots=True)
class TariffPurchaseContext:
    tariff: object
    promo_group: object | None
    period_days: int
    is_daily_tariff: bool
    base_price_kopeks: int
    price_kopeks: int
    discount_percent: int
    description: str


async def build_tariff_purchase_context(
    db: AsyncSession,
    user,
    tariff_id: int,
    period_days: int,
) -> TariffPurchaseContext:
    if not settings.is_tariffs_mode():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'tariffs_mode_disabled',
                'message': 'Tariffs mode is not enabled',
            },
        )

    tariff = await get_tariff_by_id(db, tariff_id)
    if not tariff or not tariff.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                'code': 'tariff_not_found',
                'message': 'Tariff not found or inactive',
            },
        )

    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )
    promo_group_id = promo_group.id if promo_group else None
    if not tariff.is_available_for_promo_group(promo_group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                'code': 'tariff_not_available',
                'message': 'This tariff is not available for your promo group',
            },
        )

    is_daily_tariff = bool(getattr(tariff, 'is_daily', False))
    resolved_period_days = 1 if is_daily_tariff else period_days

    if is_daily_tariff:
        base_price_kopeks = getattr(tariff, 'daily_price_kopeks', 0)
        if base_price_kopeks <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'invalid_daily_price',
                    'message': 'Daily tariff has no price configured',
                },
            )
    else:
        base_price_kopeks = tariff.get_price_for_period(resolved_period_days)
        if base_price_kopeks is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'invalid_period',
                    'message': 'Invalid period for this tariff',
                },
            )

    price_kopeks = int(base_price_kopeks)
    discount_percent = 0
    if not is_daily_tariff and promo_group:
        raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
        for key, value in raw_discounts.items():
            try:
                if int(key) == resolved_period_days:
                    discount_percent = max(0, min(100, int(value)))
                    break
            except (TypeError, ValueError):
                continue
        if discount_percent > 0:
            price_kopeks = int(base_price_kopeks * (100 - discount_percent) / 100)

    if is_daily_tariff:
        description = f"Активация суточного тарифа '{tariff.name}' (первый день)"
    elif discount_percent > 0:
        description = f"Покупка тарифа '{tariff.name}' на {resolved_period_days} дней (скидка {discount_percent}%)"
    else:
        description = f"Покупка тарифа '{tariff.name}' на {resolved_period_days} дней"

    return TariffPurchaseContext(
        tariff=tariff,
        promo_group=promo_group,
        period_days=resolved_period_days,
        is_daily_tariff=is_daily_tariff,
        base_price_kopeks=int(base_price_kopeks),
        price_kopeks=price_kopeks,
        discount_percent=discount_percent,
        description=description,
    )


def ensure_tariff_purchase_balance(user, price_kopeks: int) -> None:
    if user.balance_kopeks >= price_kopeks:
        return

    missing = price_kopeks - user.balance_kopeks
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            'code': 'insufficient_funds',
            'message': f'Недостаточно средств. Не хватает {settings.format_price(missing)}',
            'missing_amount': missing,
        },
    )
