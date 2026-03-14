import re
from datetime import UTC, datetime

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.guest_purchase import create_guest_purchase
from app.database.crud.subscription import (
    create_paid_subscription,
    extend_subscription,
    get_subscription_by_user_id,
)
from app.database.crud.tariff import get_tariff_by_id
from app.database.models import GuestPurchase, GuestPurchaseStatus, Tariff, User
from app.services.subscription_service import SubscriptionService


logger = structlog.get_logger(__name__)

_TELEGRAM_USERNAME_RE = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]{4,31}$')


class GuestPurchaseError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def create_purchase(
    db: AsyncSession,
    *,
    tariff: Tariff,
    period_days: int,
    amount_kopeks: int,
    contact_type: str | None,
    contact_value: str | None,
    payment_method: str | None,
    is_gift: bool = False,
    gift_recipient_type: str | None = None,
    gift_recipient_value: str | None = None,
    gift_message: str | None = None,
    source: str = 'cabinet',
    buyer_user_id: int | None = None,
    commit: bool = True,
) -> GuestPurchase:
    return await create_guest_purchase(
        db,
        commit=commit,
        tariff_id=tariff.id,
        period_days=period_days,
        amount_kopeks=amount_kopeks,
        contact_type=contact_type,
        contact_value=contact_value,
        payment_method=payment_method,
        is_gift=is_gift,
        gift_recipient_type=gift_recipient_type,
        gift_recipient_value=gift_recipient_value,
        gift_message=gift_message,
        source=source,
        buyer_user_id=buyer_user_id,
        status=GuestPurchaseStatus.PENDING.value,
    )


async def _find_user_by_gift_recipient(
    db: AsyncSession,
    *,
    recipient_type: str | None,
    recipient_value: str | None,
) -> User | None:
    if not recipient_type or not recipient_value:
        return None

    if recipient_type == 'telegram':
        username = recipient_value.lstrip('@').strip()
        if not _TELEGRAM_USERNAME_RE.match(username):
            return None
        result = await db.execute(select(User).where(func.lower(User.username) == username.lower()))
        return result.scalars().first()

    if recipient_type == 'email':
        email = recipient_value.strip().lower()
        result = await db.execute(select(User).where(func.lower(User.email) == email))
        return result.scalars().first()

    return None


async def _apply_purchase_subscription(
    db: AsyncSession,
    *,
    user: User,
    purchase: GuestPurchase,
    tariff: Tariff,
) -> None:
    existing_subscription = await get_subscription_by_user_id(db, user.id)
    if existing_subscription is not None:
        # Gift should extend user access instead of hard-replacing current period.
        subscription = await extend_subscription(
            db,
            existing_subscription,
            days=purchase.period_days,
            tariff_id=tariff.id,
            traffic_limit_gb=tariff.traffic_limit_gb,
            device_limit=tariff.device_limit,
            connected_squads=tariff.allowed_squads or [],
            commit=True,
        )
        await db.refresh(subscription)
    else:
        subscription = await create_paid_subscription(
            db=db,
            user_id=user.id,
            duration_days=purchase.period_days,
            traffic_limit_gb=tariff.traffic_limit_gb,
            device_limit=tariff.device_limit,
            connected_squads=tariff.allowed_squads or [],
            tariff_id=tariff.id,
            update_server_counters=True,
        )

    subscription_service = SubscriptionService()
    try:
        if user.remnawave_uuid:
            await subscription_service.update_remnawave_user(db, subscription)
        else:
            await subscription_service.create_remnawave_user(db, subscription)
    except Exception:
        logger.exception('Failed to sync remnawave after gift activation', user_id=user.id, purchase_id=purchase.id)

    purchase.subscription_url = subscription.subscription_url
    purchase.subscription_crypto_link = subscription.subscription_crypto_link


async def fulfill_purchase(
    db: AsyncSession,
    purchase_token: str,
    *,
    pre_resolved_telegram_id: int | None = None,  # compatibility signature
) -> GuestPurchase | None:
    _ = pre_resolved_telegram_id
    result = await db.execute(select(GuestPurchase).where(GuestPurchase.token == purchase_token).with_for_update())
    purchase = result.scalars().first()
    if purchase is None:
        return None

    if purchase.status != GuestPurchaseStatus.PAID.value:
        return purchase

    tariff = await get_tariff_by_id(db, purchase.tariff_id)
    if tariff is None:
        raise GuestPurchaseError('Tariff not found', status_code=500)

    recipient_user = await _find_user_by_gift_recipient(
        db,
        recipient_type=purchase.gift_recipient_type,
        recipient_value=purchase.gift_recipient_value,
    )

    # No resolvable recipient -> leave as code-only paid gift.
    if recipient_user is None:
        return purchase

    purchase.user_id = recipient_user.id
    purchase.status = GuestPurchaseStatus.PENDING_ACTIVATION.value
    await db.commit()
    await db.refresh(purchase)
    return purchase


async def activate_purchase(
    db: AsyncSession,
    purchase_token: str,
    *,
    skip_notification: bool = False,  # compatibility signature
) -> GuestPurchase:
    _ = skip_notification
    result = await db.execute(select(GuestPurchase).where(GuestPurchase.token == purchase_token).with_for_update())
    purchase = result.scalars().first()

    if purchase is None:
        raise GuestPurchaseError('Purchase not found', status_code=404)

    if purchase.status == GuestPurchaseStatus.DELIVERED.value:
        return purchase

    if purchase.status != GuestPurchaseStatus.PENDING_ACTIVATION.value:
        raise GuestPurchaseError('Purchase is not pending activation', status_code=400)

    if not purchase.user_id:
        raise GuestPurchaseError('No user linked to purchase', status_code=500)

    tariff = await get_tariff_by_id(db, purchase.tariff_id)
    if tariff is None:
        raise GuestPurchaseError('Tariff not found', status_code=500)

    user_result = await db.execute(select(User).where(User.id == purchase.user_id))
    user = user_result.scalars().first()
    if user is None:
        raise GuestPurchaseError('User not found', status_code=500)

    await _apply_purchase_subscription(db, user=user, purchase=purchase, tariff=tariff)

    purchase.status = GuestPurchaseStatus.DELIVERED.value
    purchase.delivered_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(purchase)
    return purchase
