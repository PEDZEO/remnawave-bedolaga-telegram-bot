from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.subscription_renewal_service import (
    SubscriptionRenewalChargeError,
    SubscriptionRenewalService,
)


async def execute_tariff_renewal(
    db: AsyncSession,
    user,
    subscription,
    *,
    period_days: int,
    final_total: int,
    description: str,
    logger,
) -> object:
    from app.database.crud.subscription import extend_subscription
    from app.database.crud.transaction import create_transaction
    from app.database.crud.user import subtract_user_balance
    from app.database.models import TransactionType
    from app.utils.promo_offer import get_user_active_promo_discount_percent

    try:
        success = await subtract_user_balance(
            db,
            user,
            final_total,
            description,
            consume_promo_offer=get_user_active_promo_discount_percent(user) > 0,
            mark_as_paid_subscription=True,
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={'code': 'balance_error', 'message': 'Failed to subtract balance'},
            )

        updated_subscription = await extend_subscription(db, subscription, period_days)
        await create_transaction(
            db,
            user_id=user.id,
            type=TransactionType.SUBSCRIPTION_PAYMENT,
            amount_kopeks=final_total,
            description=description,
        )

        try:
            from app.services.subscription_service import SubscriptionService

            service = SubscriptionService()
            await service.update_remnawave_user(
                db,
                updated_subscription,
                reset_traffic=settings.RESET_TRAFFIC_ON_PAYMENT,
                reset_reason='subscription renewal (miniapp)',
            )
        except Exception as error:
            logger.error('Ошибка синхронизации с RemnaWave при продлении (miniapp)', error=error)

        return updated_subscription
    except Exception as error:
        await db.rollback()
        logger.error('Failed to renew tariff subscription', subscription_id=subscription.id, error=error)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'renewal_failed', 'message': 'Failed to renew subscription'},
        ) from error


async def execute_classic_renewal(
    db: AsyncSession,
    renewal_service: SubscriptionRenewalService,
    user,
    subscription,
    pricing_model,
    *,
    description: str,
    logger,
):
    try:
        return await renewal_service.finalize(
            db,
            user,
            subscription,
            pricing_model,
            description=description,
        )
    except SubscriptionRenewalChargeError as error:
        logger.error(
            'Failed to charge balance for subscription renewal',
            subscription_id=subscription.id,
            error=error,
        )
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={'code': 'charge_failed', 'message': 'Failed to charge balance'},
        ) from error
