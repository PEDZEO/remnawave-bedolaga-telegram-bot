from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.payment_service import PaymentService
from app.services.subscription_renewal_service import (
    build_payment_descriptor,
    encode_payment_payload,
)

from ...miniapp_cryptobot_helpers import compute_cryptobot_limits, get_usd_to_rub_rate
from .renewal_submit import (
    compute_amount_usd_from_kopeks,
    ensure_cryptobot_amount_limits,
    extract_cryptobot_payment_urls,
)


async def create_renewal_cryptobot_payment(
    db: AsyncSession,
    user,
    subscription,
    *,
    period_days: int,
    final_total: int,
    missing_amount: int,
    description: str,
    pricing_snapshot,
) -> dict:
    if not settings.is_cryptobot_enabled():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')

    rate = await get_usd_to_rub_rate()
    min_amount_kopeks, max_amount_kopeks = compute_cryptobot_limits(rate)
    ensure_cryptobot_amount_limits(
        missing_amount=missing_amount,
        min_amount_kopeks=min_amount_kopeks,
        max_amount_kopeks=max_amount_kopeks,
    )
    amount_usd = compute_amount_usd_from_kopeks(missing_amount, rate)

    descriptor = build_payment_descriptor(
        user.id,
        subscription.id,
        period_days,
        final_total,
        missing_amount,
        pricing_snapshot=pricing_snapshot,
    )
    payment_payload = encode_payment_payload(descriptor)

    payment_service = PaymentService()
    result = await payment_service.create_cryptobot_payment(
        db=db,
        user_id=user.id,
        amount_usd=amount_usd,
        asset=settings.CRYPTOBOT_DEFAULT_ASSET,
        description=description,
        payload=payment_payload,
    )
    if not result:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={'code': 'payment_creation_failed', 'message': 'Failed to create payment'},
        )

    payment_url, payment_extra = extract_cryptobot_payment_urls(result)
    return {
        'payment_url': payment_url,
        'payment_payload': payment_payload,
        'payment_extra': payment_extra,
        'payment_id': result.get('local_payment_id'),
        'invoice_id': result.get('invoice_id'),
    }
