from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PaymentMethod, User
from app.services.subscription_renewal_service import decode_payment_payload

from ..schemas.miniapp import MiniAppPaymentStatusQuery, MiniAppPaymentStatusResult
from .miniapp_payment_lookup_helpers import (
    find_recent_deposit,
    parse_client_timestamp,
)
from .miniapp_payment_status_helpers import (
    build_pending_payment_status,
    classify_payment_status,
)


async def resolve_cryptobot_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.cryptobot import (
        get_cryptobot_payment_by_id,
        get_cryptobot_payment_by_invoice_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_cryptobot_payment_by_id(db, query.local_payment_id)
    if not payment and query.invoice_id:
        payment = await get_cryptobot_payment_by_invoice_id(db, query.invoice_id)

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='cryptobot',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
                'payment_id': query.payment_id,
            },
        )

    status_raw = payment.status
    is_paid = (status_raw or '').lower() == 'paid'
    status = classify_payment_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    amount_kopeks = None
    try:
        amount_kopeks = int(Decimal(payment.amount) * Decimal(100))
    except (InvalidOperation, TypeError):
        amount_kopeks = None

    descriptor = decode_payment_payload(getattr(payment, 'payload', '') or '', expected_user_id=user.id)
    purpose = 'subscription_renewal' if descriptor else 'balance_topup'

    return MiniAppPaymentStatusResult(
        method='cryptobot',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=amount_kopeks,
        currency=payment.asset,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.invoice_id,
        extra={
            'status': payment.status,
            'asset': payment.asset,
            'local_payment_id': payment.id,
            'invoice_id': payment.invoice_id,
            'payload': query.payload,
            'started_at': query.started_at,
            'purpose': purpose,
            'subscription_id': descriptor.subscription_id if descriptor else None,
            'period_days': descriptor.period_days if descriptor else None,
        },
    )


async def resolve_heleket_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.heleket import (
        get_heleket_payment_by_id,
        get_heleket_payment_by_order_id,
        get_heleket_payment_by_uuid,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_heleket_payment_by_id(db, query.local_payment_id)
    if not payment and query.payment_id:
        payment = await get_heleket_payment_by_uuid(db, query.payment_id)
    if not payment and query.invoice_id:
        payment = await get_heleket_payment_by_uuid(db, query.invoice_id)
    if not payment and query.bill_id:
        payment = await get_heleket_payment_by_order_id(db, query.bill_id)

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='heleket',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'uuid': query.payment_id or query.invoice_id,
                'order_id': query.bill_id,
            },
        )

    status_raw = payment.status
    is_paid = bool(payment.is_paid)
    status = classify_payment_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method='heleket',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.uuid,
        message=None,
        extra={
            'status': payment.status,
            'local_payment_id': payment.id,
            'uuid': payment.uuid,
            'order_id': payment.order_id,
            'payer_amount': payment.payer_amount,
            'payer_currency': payment.payer_currency,
            'discount_percent': payment.discount_percent,
            'exchange_rate': payment.exchange_rate,
            'payment_url': payment.payment_url,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def resolve_cloudpayments_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.cloudpayments import (
        get_cloudpayments_payment_by_id,
        get_cloudpayments_payment_by_invoice_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_cloudpayments_payment_by_id(db, query.local_payment_id)
    if not payment and query.invoice_id:
        payment = await get_cloudpayments_payment_by_invoice_id(db, query.invoice_id)
    if not payment and query.payment_id:
        payment = await get_cloudpayments_payment_by_invoice_id(db, query.payment_id)

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='cloudpayments',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'invoice_id': query.invoice_id,
            },
        )

    status_raw = payment.status
    is_paid = bool(payment.is_paid)
    status = classify_payment_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method='cloudpayments',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.invoice_id,
        message=None,
        extra={
            'status': payment.status,
            'local_payment_id': payment.id,
            'invoice_id': payment.invoice_id,
            'transaction_id_cp': payment.transaction_id_cp,
            'card_type': payment.card_type,
            'card_last_four': payment.card_last_four,
            'payment_url': payment.payment_url,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def resolve_freekassa_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    from app.database.crud.freekassa import (
        get_freekassa_payment_by_id,
        get_freekassa_payment_by_order_id,
    )

    payment = None
    if query.local_payment_id:
        payment = await get_freekassa_payment_by_id(db, query.local_payment_id)
    if not payment and query.payment_id:
        payment = await get_freekassa_payment_by_order_id(db, query.payment_id)

    if not payment or payment.user_id != user.id:
        return build_pending_payment_status(
            method='freekassa',
            query=query,
            message='Payment not found',
            extra={
                'local_payment_id': query.local_payment_id,
                'order_id': query.payment_id,
            },
        )

    status_raw = payment.status
    is_paid = bool(payment.is_paid)
    status = classify_payment_status(status_raw, is_paid)
    completed_at = payment.paid_at or payment.updated_at or payment.created_at

    return MiniAppPaymentStatusResult(
        method='freekassa',
        status=status,
        is_paid=status == 'paid',
        amount_kopeks=payment.amount_kopeks,
        currency=payment.currency,
        completed_at=completed_at,
        transaction_id=payment.transaction_id,
        external_id=payment.freekassa_order_id,
        message=None,
        extra={
            'status': payment.status,
            'local_payment_id': payment.id,
            'order_id': payment.order_id,
            'freekassa_order_id': payment.freekassa_order_id,
            'payment_url': payment.payment_url,
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def resolve_stars_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    started_at = parse_client_timestamp(query.started_at)
    transaction = await find_recent_deposit(
        db,
        user_id=user.id,
        payment_method=PaymentMethod.TELEGRAM_STARS,
        amount_kopeks=query.amount_kopeks,
        started_at=started_at,
    )

    if not transaction:
        return build_pending_payment_status(
            method='stars',
            query=query,
            message='Waiting for confirmation',
        )

    return MiniAppPaymentStatusResult(
        method='stars',
        status='paid',
        is_paid=True,
        amount_kopeks=transaction.amount_kopeks,
        currency='RUB',
        completed_at=transaction.completed_at or transaction.created_at,
        transaction_id=transaction.id,
        external_id=transaction.external_id,
        extra={
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )


async def resolve_tribute_payment_status(
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    started_at = parse_client_timestamp(query.started_at)
    transaction = await find_recent_deposit(
        db,
        user_id=user.id,
        payment_method=PaymentMethod.TRIBUTE,
        amount_kopeks=query.amount_kopeks,
        started_at=started_at,
    )

    if not transaction:
        return build_pending_payment_status(
            method='tribute',
            query=query,
            message='Waiting for confirmation',
        )

    return MiniAppPaymentStatusResult(
        method='tribute',
        status='paid',
        is_paid=True,
        amount_kopeks=transaction.amount_kopeks,
        currency='RUB',
        completed_at=transaction.completed_at or transaction.created_at,
        transaction_id=transaction.id,
        external_id=transaction.external_id,
        extra={
            'payload': query.payload,
            'started_at': query.started_at,
        },
    )
