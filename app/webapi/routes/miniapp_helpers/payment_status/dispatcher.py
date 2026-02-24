from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.services.payment_service import PaymentService

from ....schemas.miniapp import MiniAppPaymentStatusQuery, MiniAppPaymentStatusResult
from .base import (
    resolve_mulenpay_payment_status,
    resolve_yookassa_payment_status,
)
from .common import (
    build_unknown_payment_status,
    is_supported_payment_method,
    normalize_payment_method,
)
from .direct import (
    resolve_cloudpayments_payment_status,
    resolve_cryptobot_payment_status,
    resolve_freekassa_payment_status,
    resolve_heleket_payment_status,
    resolve_stars_payment_status,
    resolve_tribute_payment_status,
)
from .gateway import (
    resolve_pal24_payment_status,
    resolve_platega_payment_status,
    resolve_wata_payment_status,
)


async def resolve_payment_status_entry(
    *,
    payment_service: PaymentService,
    db: AsyncSession,
    user: User,
    query: MiniAppPaymentStatusQuery,
) -> MiniAppPaymentStatusResult:
    method = normalize_payment_method(query.method)
    if not method:
        return build_unknown_payment_status(method='', message='Payment method is required')

    if not is_supported_payment_method(method):
        return build_unknown_payment_status(method=method, message='Unsupported payment method')

    if method in {'yookassa', 'yookassa_sbp'}:
        return await resolve_yookassa_payment_status(
            db,
            user,
            query,
            method=method,
        )
    if method == 'mulenpay':
        return await resolve_mulenpay_payment_status(payment_service, db, user, query)
    if method == 'platega':
        return await resolve_platega_payment_status(payment_service, db, user, query)
    if method == 'wata':
        return await resolve_wata_payment_status(payment_service, db, user, query)
    if method == 'pal24':
        return await resolve_pal24_payment_status(payment_service, db, user, query)
    if method == 'cryptobot':
        return await resolve_cryptobot_payment_status(db, user, query)
    if method == 'heleket':
        return await resolve_heleket_payment_status(db, user, query)
    if method == 'cloudpayments':
        return await resolve_cloudpayments_payment_status(db, user, query)
    if method == 'freekassa':
        return await resolve_freekassa_payment_status(db, user, query)
    if method == 'stars':
        return await resolve_stars_payment_status(db, user, query)
    if method == 'tribute':
        return await resolve_tribute_payment_status(db, user, query)

    return build_unknown_payment_status(method=method, message='Unsupported payment method')
