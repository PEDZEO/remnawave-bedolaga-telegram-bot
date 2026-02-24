from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.payment_service import PaymentService
from app.webapi.schemas.miniapp import MiniAppPaymentCreateResponse

from ...miniapp_cryptobot_helpers import compute_cryptobot_limits, get_usd_to_rub_rate
from .amount import current_request_timestamp


async def create_cryptobot_balance_payment_response(
    db: AsyncSession,
    user,
    amount_kopeks: int | None,
) -> MiniAppPaymentCreateResponse:
    method = 'cryptobot'
    if not settings.is_cryptobot_enabled():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
    if amount_kopeks is None or amount_kopeks <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

    rate = await get_usd_to_rub_rate()
    min_amount_kopeks, max_amount_kopeks = compute_cryptobot_limits(rate)
    if amount_kopeks < min_amount_kopeks:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f'Amount is below minimum ({min_amount_kopeks / 100:.2f} RUB)',
        )
    if amount_kopeks > max_amount_kopeks:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f'Amount exceeds maximum ({max_amount_kopeks / 100:.2f} RUB)',
        )

    try:
        amount_usd = float(
            (Decimal(amount_kopeks) / Decimal(100) / Decimal(str(rate))).quantize(
                Decimal('0.01'),
                rounding=ROUND_HALF_UP,
            )
        )
    except (InvalidOperation, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Unable to convert amount to USD',
        ) from None

    payment_service = PaymentService()
    result = await payment_service.create_cryptobot_payment(
        db=db,
        user_id=user.id,
        amount_usd=amount_usd,
        asset=settings.CRYPTOBOT_DEFAULT_ASSET,
        description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
        payload=f'balance_{user.id}_{amount_kopeks}',
    )
    if not result:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

    payment_url = (
        result.get('web_app_invoice_url') or result.get('mini_app_invoice_url') or result.get('bot_invoice_url')
    )
    if not payment_url:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to obtain payment url')

    return MiniAppPaymentCreateResponse(
        method=method,
        payment_url=payment_url,
        amount_kopeks=amount_kopeks,
        extra={
            'local_payment_id': result.get('local_payment_id'),
            'invoice_id': result.get('invoice_id'),
            'amount_usd': amount_usd,
            'rate': rate,
            'requested_at': current_request_timestamp(),
        },
    )
