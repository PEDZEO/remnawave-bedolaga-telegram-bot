from collections.abc import Collection

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.user import get_user_by_telegram_id
from app.database.models import Subscription, User
from app.utils.telegram_webapp import TelegramWebAppAuthError, parse_webapp_init_data


async def authorize_miniapp_user(
    init_data: str,
    db: AsyncSession,
) -> User:
    if not init_data:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': 'Authorization data is missing'},
        )

    try:
        webapp_data = parse_webapp_init_data(init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    return user


def ensure_paid_subscription(
    user: User,
    *,
    allowed_statuses: Collection[str] | None = None,
) -> Subscription:
    subscription = getattr(user, 'subscription', None)
    if not subscription:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'subscription_not_found', 'message': 'Subscription not found'},
        )

    normalized_allowed_statuses = set(allowed_statuses or {'active'})

    if getattr(subscription, 'is_trial', False) and 'trial' not in normalized_allowed_statuses:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                'code': 'paid_subscription_required',
                'message': 'This action is available only for paid subscriptions',
            },
        )

    actual_status = getattr(subscription, 'actual_status', None) or ''

    if actual_status not in normalized_allowed_statuses:
        if actual_status == 'trial':
            detail = {
                'code': 'paid_subscription_required',
                'message': 'This action is available only for paid subscriptions',
            }
        elif actual_status == 'disabled':
            detail = {
                'code': 'subscription_disabled',
                'message': 'Subscription is disabled',
            }
        else:
            detail = {
                'code': 'subscription_inactive',
                'message': 'Subscription must be active to manage settings',
            }

        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=detail)

    if not getattr(subscription, 'is_active', False) and 'expired' not in normalized_allowed_statuses:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                'code': 'subscription_inactive',
                'message': 'Subscription must be active to manage settings',
            },
        )

    return subscription
