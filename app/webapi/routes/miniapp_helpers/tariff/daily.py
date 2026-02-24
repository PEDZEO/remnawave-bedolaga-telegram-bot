from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.tariff import get_tariff_by_id
from app.database.models import SubscriptionStatus, User


async def get_daily_tariff_for_subscription(
    db: AsyncSession,
    subscription,
):
    tariff_id = getattr(subscription, 'tariff_id', None)
    if not tariff_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'no_tariff', 'message': 'Subscription has no tariff'},
        )

    tariff = await get_tariff_by_id(db, tariff_id)
    if not tariff or not getattr(tariff, 'is_daily', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={'code': 'not_daily_tariff', 'message': 'Subscription is not on a daily tariff'},
        )

    return tariff


def toggle_pause_state(subscription) -> bool:
    is_currently_paused = getattr(subscription, 'is_daily_paused', False)
    new_paused_state = not is_currently_paused
    subscription.is_daily_paused = new_paused_state
    return new_paused_state


def ensure_daily_resume_allowed(
    user: User,
    subscription,
    tariff,
) -> bool:
    daily_price = getattr(tariff, 'daily_price_kopeks', 0)
    if daily_price > 0 and user.balance_kopeks < daily_price:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_balance',
                'message': 'Insufficient balance to resume daily subscription',
                'required': daily_price,
                'balance': user.balance_kopeks,
            },
        )

    if subscription.status == SubscriptionStatus.DISABLED.value:
        subscription.status = SubscriptionStatus.ACTIVE.value
        subscription.last_daily_charge_at = datetime.now(UTC)
        subscription.end_date = datetime.now(UTC) + timedelta(days=1)
        return True

    return False


def build_daily_toggle_message(language: str, is_paused: bool) -> str:
    if is_paused:
        return 'Суточная подписка приостановлена' if language == 'ru' else 'Daily subscription paused'
    return 'Суточная подписка возобновлена' if language == 'ru' else 'Daily subscription resumed'
