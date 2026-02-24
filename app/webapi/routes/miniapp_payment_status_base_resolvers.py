from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.payment_service import PaymentService

from ..schemas.miniapp import MiniAppPaymentStatusQuery, MiniAppPaymentStatusResult
from .miniapp_payment_status_helpers import (
    build_pending_payment_status,
    classify_payment_status,
)


async def resolve_yookassa_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
    *,
    method: str = 'yookassa',
) -> MiniAppPaymentStatusResult:
    from app.database.crud.yookassa import (
        get_yookassa_payment_by_id,
        get_yookassa_payment_by_local_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_yookassa_payment_by_local_id(db, query.local_payment_id)
    if not payment and query.payment_id:
        payment = await get_yookassa_payment_by_id(db, query.payment_id)

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method=method,
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'payment_id': query.payment_id,
                'invoice_id': query.payment_id,
            },
        )

    succeeded = bool(payment.is_paid and (payment.status or '').lower() == 'succeeded')
    status = classify_payment_status(payment.status, succeeded)
    completed_at = payment.captured_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method=method,
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.yookassa_payment_id,
        extra={
            'status': payment.status,
            'is_paid': payment.is_paid,
            'local_payment_id': payment.id,
            'payment_id': payment.yookassa_payment_id,
            'invoice_id': payment.yookassa_payment_id,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def resolve_mulenpay_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    if not query.local_payment_id:
        return build_pending_payment_status(
            method='mulenpay',
            query=query,
            message='Missing payment identifier',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payment_id': query.payment_id,
            },
        )

    status_info = await payment_service.get_mulenpay_payment_status(db, query.local_payment_id)
    payment = status_info.get('payment') if status_info else None

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='mulenpay',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payment_id': query.payment_id,
            },
        )

    status_raw = status_info.get('status') or payment.status
    is_paid = bool(payment.is_paid)
    status = classify_payment_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at
    message = None
    if status == 'failed':
        remote_status = status_info.get('remote_status_code') or status_raw
        if remote_status:
            message = f'Status: {remote_status}'

    return MiniAppPaymentStatusResult(
        method='mulenpay',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=str(payment.mulen_payment_id or payment.uuid),
        message=message,
        extra={
            'status': payment.status,
            'remote_status': status_info.get('remote_status_code'),
            'local_payment_id': payment.id,
            'payment_id': payment.mulen_payment_id,
            'uuid': str(payment.uuid),
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )
