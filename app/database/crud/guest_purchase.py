import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import GuestPurchase, GuestPurchaseStatus


def generate_guest_purchase_token() -> str:
    # 64-char-ish token with enough entropy for safe prefix activation links.
    return secrets.token_urlsafe(48)


async def create_guest_purchase(
    db: AsyncSession,
    *,
    tariff_id: int,
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
    status: str = GuestPurchaseStatus.PENDING.value,
    payment_id: str | None = None,
    token: str | None = None,
    commit: bool = True,
) -> GuestPurchase:
    purchase = GuestPurchase(
        token=token or generate_guest_purchase_token(),
        status=status,
        tariff_id=tariff_id,
        period_days=period_days,
        amount_kopeks=amount_kopeks,
        contact_type=contact_type,
        contact_value=contact_value,
        payment_method=payment_method,
        payment_id=payment_id,
        is_gift=is_gift,
        buyer_user_id=buyer_user_id,
        gift_recipient_type=gift_recipient_type,
        gift_recipient_value=gift_recipient_value,
        gift_message=gift_message,
        source=source,
    )
    db.add(purchase)
    if commit:
        await db.commit()
        await db.refresh(purchase)
    else:
        await db.flush()
    return purchase


async def get_guest_purchase_by_token(
    db: AsyncSession,
    token: str,
    *,
    for_update: bool = False,
) -> GuestPurchase | None:
    query = select(GuestPurchase).where(GuestPurchase.token == token)
    if for_update:
        query = query.with_for_update()
    result = await db.execute(query)
    return result.scalars().first()


async def mark_guest_purchase_paid(
    db: AsyncSession,
    purchase: GuestPurchase,
    *,
    payment_id: str | None = None,
) -> GuestPurchase:
    purchase.status = GuestPurchaseStatus.PAID.value
    purchase.paid_at = datetime.now(UTC)
    if payment_id:
        purchase.payment_id = payment_id
    await db.commit()
    await db.refresh(purchase)
    return purchase
