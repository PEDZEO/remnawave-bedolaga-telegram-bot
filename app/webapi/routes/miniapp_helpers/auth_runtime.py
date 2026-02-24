from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.user import get_user_by_telegram_id
from app.database.models import User
from app.utils.telegram_webapp import (
    TelegramWebAppAuthError,
    parse_webapp_init_data,
)


async def resolve_user_from_init_data(
    db: AsyncSession,
    init_data: str,
) -> tuple[User, dict[str, Any]]:
    if not init_data:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail='Missing initData',
        )

    try:
        webapp_data = parse_webapp_init_data(init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Invalid Telegram user payload',
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail='Invalid Telegram user identifier',
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    return user, webapp_data
