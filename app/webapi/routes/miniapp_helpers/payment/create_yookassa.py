from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.payment_service import PaymentService
from app.webapi.schemas.miniapp import MiniAppPaymentCreateResponse

from .amount import current_request_timestamp


def _ensure_yookassa_amount_allowed(amount_kopeks: int | None) -> int:
    if amount_kopeks is None or amount_kopeks <= 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
    if amount_kopeks < settings.YOOKASSA_MIN_AMOUNT_KOPEKS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
    if amount_kopeks > settings.YOOKASSA_MAX_AMOUNT_KOPEKS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')
    return amount_kopeks


async def create_yookassa_balance_payment_response(
    db: AsyncSession,
    user,
    amount_kopeks: int | None,
) -> MiniAppPaymentCreateResponse:
    method = 'yookassa'
    if not settings.is_yookassa_enabled():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
    amount_kopeks = _ensure_yookassa_amount_allowed(amount_kopeks)

    payment_service = PaymentService()
    result = await payment_service.create_yookassa_payment(
        db=db,
        user_id=user.id,
        amount_kopeks=amount_kopeks,
        description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
    )
    if not result or not result.get('confirmation_url'):
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

    return MiniAppPaymentCreateResponse(
        method=method,
        payment_url=result['confirmation_url'],
        amount_kopeks=amount_kopeks,
        extra={
            'local_payment_id': result.get('local_payment_id'),
            'payment_id': result.get('yookassa_payment_id'),
            'status': result.get('status'),
            'requested_at': current_request_timestamp(),
        },
    )


async def create_yookassa_sbp_balance_payment_response(
    db: AsyncSession,
    user,
    amount_kopeks: int | None,
) -> MiniAppPaymentCreateResponse:
    method = 'yookassa_sbp'
    if not settings.is_yookassa_enabled() or not getattr(settings, 'YOOKASSA_SBP_ENABLED', False):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
    amount_kopeks = _ensure_yookassa_amount_allowed(amount_kopeks)

    payment_service = PaymentService()
    result = await payment_service.create_yookassa_sbp_payment(
        db=db,
        user_id=user.id,
        amount_kopeks=amount_kopeks,
        description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
    )
    confirmation_url = result.get('confirmation_url') if result else None
    if not result or not confirmation_url:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

    extra: dict[str, object] = {
        'local_payment_id': result.get('local_payment_id'),
        'payment_id': result.get('yookassa_payment_id'),
        'status': result.get('status'),
        'requested_at': current_request_timestamp(),
    }
    confirmation_token = result.get('confirmation_token')
    if confirmation_token:
        extra['confirmation_token'] = confirmation_token

    return MiniAppPaymentCreateResponse(
        method=method,
        payment_url=confirmation_url,
        amount_kopeks=amount_kopeks,
        extra=extra,
    )
