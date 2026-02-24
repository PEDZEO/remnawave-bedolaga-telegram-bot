from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.payment_service import PaymentService, get_wata_payment_by_link_id

from ....schemas.miniapp import MiniAppPaymentStatusQuery, MiniAppPaymentStatusResult
from .common import (
    build_pending_payment_status,
    classify_payment_status,
)


async def resolve_platega_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.platega import (
        get_platega_payment_by_correlation_id,
        get_platega_payment_by_id,
        get_platega_payment_by_transaction_id,
    )

    payment = None
    local_id = query.local_payment_id
    if local_id:
        payment = await get_platega_payment_by_id(db, local_id)

    if not payment and query.payment_id:
        payment = await get_platega_payment_by_transaction_id(db, query.payment_id)

    if not payment and query.payload:
        correlation = str(query.payload).replace('platega:', '')
        payment = await get_platega_payment_by_correlation_id(db, correlation)

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='platega',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'payment_id': query.payment_id,
            },
        )

    status_info = await payment_service.get_platega_payment_status(db, payment.id)
    refreshed_payment = (status_info or {}).get('payment') or payment

    status_raw = (status_info or {}).get('status') or getattr(payment, 'status', None)
    is_paid_flag = bool((status_info or {}).get('is_paid') or getattr(payment, 'is_paid', False))
    status_value = classify_payment_status(status_raw, is_paid_flag)

    completed_at = (
        getattr(refreshed_payment, 'paid_at', None)
        or getattr(refreshed_payment, 'updated_at', None)
        or getattr(refreshed_payment, 'created_at', None)
    )

    extra: dict[str, Any] = {
        'local_payment_id': refreshed_payment.id,
        'payment_id': refreshed_payment.platega_transaction_id,
        'correlation_id': refreshed_payment.correlation_id,
        'status': status_raw,
        'is_paid': getattr(refreshed_payment, 'is_paid', False),
        'payload': query.payload,
        'started_at': query.started_at,
    }

    if status_info and status_info.get('remote'):
        extra['remote'] = status_info.get('remote')

    return MiniAppPaymentStatusResult(
        method='platega',
        status=status_value,
        is_paid=status_value == 'paid',
        amount_kopeks=refreshed_payment.amount_kopeks,
        currency=refreshed_payment.currency,
        completed_at=completed_at,
        transaction_id=refreshed_payment.transaction_id,
        external_id=refreshed_payment.platega_transaction_id,
        message=None,
        extra=extra,
    )


async def resolve_wata_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    local_id = query.local_payment_id
    payment_link_id = query.payment_link_id or query.payment_id or query.invoice_id
    fallback_payment = None

    if not local_id and payment_link_id:
        fallback_payment = await get_wata_payment_by_link_id(db, payment_link_id)
        if fallback_payment:
            local_id = fallback_payment.id

    if not local_id:
        return build_pending_payment_status(
            method='wata',
            query=query,
            message='Missing payment identifier',
            extra={
                'local_payment_id': query.local_payment_id,
                'payment_link_id': payment_link_id,
                'payment_id': query.payment_id,
                'invoice_id': query.invoice_id,
            },
        )

    status_info = await payment_service.get_wata_payment_status(db, local_id)
    payment = (status_info or {}).get('payment') or fallback_payment

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='wata',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': local_id,
                'payment_link_id': (payment_link_id or getattr(payment, 'payment_link_id', None)),
                'payment_id': query.payment_id,
                'invoice_id': query.invoice_id,
            },
        )

    remote_link = (status_info or {}).get('remote_link') if status_info else None
    transaction_payload = (status_info or {}).get('transaction') if status_info else None
    status_raw = (status_info or {}).get('status') or getattr(payment, 'status', None)
    is_paid_flag = bool((status_info or {}).get('is_paid') or getattr(payment, 'is_paid', False))
    status_value = classify_payment_status(status_raw, is_paid_flag)
    completed_at = (
        getattr(payment, 'paid_at', None)
        or getattr(payment, 'updated_at', None)
        or getattr(payment, 'created_at', None)
    )

    message = None
    if status_value == 'failed':
        message = (
            (transaction_payload or {}).get('errorDescription')
            or (transaction_payload or {}).get('errorCode')
            or (remote_link or {}).get('status')
        )

    extra: dict[str, Any] = {
        'local_payment_id': payment.id,
        'payment_link_id': payment.payment_link_id,
        'payment_id': payment.payment_link_id,
        'status': status_raw,
        'is_paid': getattr(payment, 'is_paid', False),
        'order_id': getattr(payment, 'order_id', None),
        'payload': query.payload,
        'started_at': query.started_at,
    }
    if remote_link:
        extra['remote_link'] = remote_link
    if transaction_payload:
        extra['transaction'] = transaction_payload

    return MiniAppPaymentStatusResult(
        method='wata',
        status=status_value,
        is_paid=status_value == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.payment_link_id,
        message=message,
        extra=extra,
    )


async def resolve_pal24_payment_status(
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.pal24 import get_pal24_payment_by_bill_id

    local_id = query.local_payment_id
    if not local_id and query.invoice_id:
        payment_by_bill = await get_pal24_payment_by_bill_id(db, query.invoice_id)
        if payment_by_bill and payment_by_bill.user_id == user.id:
            local_id = payment_by_bill.id

    if not local_id:
        return build_pending_payment_status(
            method='pal24',
            query=query,
            message='Missing payment identifier',
            extra={
                'local_payment_id': query.local_payment_id,
                'bill_id': query.invoice_id,
                'order_id': None,
            },
        )

    status_info = await payment_service.get_pal24_payment_status(db, local_id)
    payment = status_info.get('payment') if status_info else None

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='pal24',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': local_id,
                'bill_id': query.invoice_id,
                'order_id': None,
            },
        )

    status_raw = status_info.get('status') or payment.status
    is_paid = bool(payment.is_paid)
    status = classify_payment_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at
    message = None
    if status == 'failed':
        remote_status = status_info.get('remote_status') or status_raw
        if remote_status:
            message = f'Status: {remote_status}'

    links_info = status_info.get('links') if status_info else {}

    return MiniAppPaymentStatusResult(
        method='pal24',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.bill_id,
        message=message,
        extra={
            'status': payment.status,
            'remote_status': status_info.get('remote_status'),
            'local_payment_id': payment.id,
            'bill_id': payment.bill_id,
            'order_id': payment.order_id,
            'payment_method': getattr(payment, 'payment_method', None),
            'payload': query.payload,
            'started_at': query.started_at,
            'links': links_info or None,
            'sbp_url': status_info.get('sbp_url') if status_info else None,
            'card_url': status_info.get('card_url') if status_info else None,
            'link_url': status_info.get('link_url') if status_info else None,
            'link_page_url': status_info.get('link_page_url') if status_info else None,
            'primary_url': status_info.get('primary_url') if status_info else None,
            'secondary_url': status_info.get('secondary_url') if status_info else None,
            'selected_method': status_info.get('selected_method') if status_info else None,
        },
    )
