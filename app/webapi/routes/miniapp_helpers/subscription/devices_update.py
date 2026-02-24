from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import Subscription, User
from app.utils.pricing_utils import apply_percentage_discount, calculate_prorated_price, get_remaining_months

from .common import get_addon_discount_percent_for_user


def resolve_device_limits(payload, subscription: Subscription) -> tuple[int, int]:
    raw_value = payload.devices if payload.devices is not None else payload.device_limit
    if raw_value is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'validation_error', 'message': 'Device limit is required'},
        )

    try:
        new_devices = int(raw_value)
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'validation_error', 'message': 'Invalid device limit'},
        ) from None

    if new_devices <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'validation_error', 'message': 'Device limit must be positive'},
        )

    if settings.MAX_DEVICES_LIMIT > 0 and new_devices > settings.MAX_DEVICES_LIMIT:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'devices_limit_exceeded',
                'message': f'Превышен максимальный лимит устройств ({settings.MAX_DEVICES_LIMIT})',
            },
        )

    current_devices_value = subscription.device_limit
    if current_devices_value is None:
        current_devices_value = settings.DEFAULT_DEVICE_LIMIT or 1

    return int(current_devices_value), new_devices


def calculate_devices_upgrade_cost(
    user: User,
    subscription: Subscription,
    *,
    current_devices: int,
    new_devices: int,
) -> tuple[int, int]:
    devices_difference = new_devices - current_devices
    if devices_difference <= 0:
        return 0, 0

    current_chargeable = max(0, current_devices - settings.DEFAULT_DEVICE_LIMIT)
    new_chargeable = max(0, new_devices - settings.DEFAULT_DEVICE_LIMIT)
    chargeable_diff = new_chargeable - current_chargeable
    price_per_month = chargeable_diff * settings.PRICE_PER_DEVICE

    months_remaining = get_remaining_months(subscription.end_date)
    period_hint_days = months_remaining * 30 if months_remaining > 0 else None
    devices_discount = get_addon_discount_percent_for_user(user, 'devices', period_hint_days)
    discounted_per_month, _ = apply_percentage_discount(price_per_month, devices_discount)

    price_to_charge, charged_months = calculate_prorated_price(
        discounted_per_month,
        subscription.end_date,
    )
    return int(price_to_charge), int(charged_months)


async def charge_devices_upgrade(
    db: AsyncSession,
    user: User,
    *,
    current_devices: int,
    new_devices: int,
    price_to_charge: int,
    charged_months: int,
    subscription_end_date,
) -> None:
    if price_to_charge <= 0:
        return

    from app.database.crud.transaction import create_transaction
    from app.database.crud.user import subtract_user_balance
    from app.database.models import TransactionType

    if getattr(user, 'balance_kopeks', 0) < price_to_charge:
        missing = price_to_charge - getattr(user, 'balance_kopeks', 0)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': f'Недостаточно средств на балансе. Не хватает {settings.format_price(missing)}',
            },
        )

    description = f'Изменение количества устройств с {current_devices} до {new_devices}'
    success = await subtract_user_balance(
        db,
        user,
        price_to_charge,
        description,
    )
    if not success:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'balance_charge_failed',
                'message': 'Failed to charge user balance',
            },
        )

    await create_transaction(
        db=db,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=price_to_charge,
        description=f'{description} на {charged_months or get_remaining_months(subscription_end_date)} мес',
    )
