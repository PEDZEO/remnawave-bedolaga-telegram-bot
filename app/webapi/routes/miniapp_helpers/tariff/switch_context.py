from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.tariff import get_tariff_by_id


@dataclass(slots=True)
class TariffSwitchContext:
    subscription: Any
    current_tariff: Any
    new_tariff: Any
    promo_group: Any
    remaining_days: int


async def resolve_tariff_switch_context(
    db: AsyncSession,
    user: Any,
    new_tariff_id: int,
    *,
    unavailable_message: str,
) -> TariffSwitchContext:
    subscription = getattr(user, 'subscription', None)
    if not subscription or not subscription.tariff_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'no_subscription', 'message': 'No active subscription with tariff'},
        )

    if subscription.status not in ('active', 'trial'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'subscription_inactive', 'message': 'Subscription is not active'},
        )

    current_tariff = await get_tariff_by_id(db, subscription.tariff_id)
    new_tariff = await get_tariff_by_id(db, new_tariff_id)
    if not new_tariff or not new_tariff.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'tariff_not_found', 'message': 'Tariff not found or inactive'},
        )

    if subscription.tariff_id == new_tariff_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'same_tariff', 'message': 'Already on this tariff'},
        )

    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )
    promo_group_id = promo_group.id if promo_group else None
    if not new_tariff.is_available_for_promo_group(promo_group_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={'code': 'tariff_not_available', 'message': unavailable_message},
        )

    remaining_days = 0
    if subscription.end_date and subscription.end_date > datetime.now(UTC):
        delta = subscription.end_date - datetime.now(UTC)
        remaining_days = max(0, delta.days)

    return TariffSwitchContext(
        subscription=subscription,
        current_tariff=current_tariff,
        new_tariff=new_tariff,
        promo_group=promo_group,
        remaining_days=remaining_days,
    )
