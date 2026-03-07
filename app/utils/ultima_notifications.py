"""Helpers for Ultima-mode notification keyboards.

In Ultima mode we avoid bot-menu callback buttons in user notifications,
because the primary UX entrypoint is the Mini App.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy import select

from app.database.database import AsyncSessionLocal
from app.database.models import SystemSetting


logger = structlog.get_logger(__name__)

ULTIMA_MODE_ENABLED_KEY = 'CABINET_ULTIMA_MODE_ENABLED'
_CACHE_TTL_SECONDS = 20.0
_cached_ultima_enabled: bool = False
_cache_expires_at_monotonic: float = 0.0

_MENU_CALLBACK_PREFIX = 'menu_'
_BLOCKED_CALLBACKS = frozenset({'back_to_menu', 'menu_profile_unavailable'})


async def is_ultima_mode_enabled_cached() -> bool:
    """Return Ultima mode flag with a lightweight TTL cache."""
    global _cached_ultima_enabled, _cache_expires_at_monotonic

    now = time.monotonic()
    if now < _cache_expires_at_monotonic:
        return _cached_ultima_enabled

    enabled = False
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(SystemSetting.value).where(SystemSetting.key == ULTIMA_MODE_ENABLED_KEY))
            value = result.scalar_one_or_none()
            enabled = str(value).strip().lower() == 'true'
    except Exception as error:  # pragma: no cover - defensive fallback
        logger.warning('Failed to read Ultima mode flag for notifications', error=error)
        enabled = False

    _cached_ultima_enabled = enabled
    _cache_expires_at_monotonic = now + _CACHE_TTL_SECONDS
    return enabled


def _is_bot_menu_callback(callback_data: str | None) -> bool:
    if not callback_data:
        return False
    if callback_data in _BLOCKED_CALLBACKS:
        return True
    return callback_data.startswith(_MENU_CALLBACK_PREFIX)


async def strip_bot_menu_buttons_for_ultima(markup: Any | None) -> Any | None:
    """Remove bot-menu callback buttons from inline keyboards in Ultima mode.

    Keeps non-menu actions (URLs/web-app buttons/other callbacks) intact.
    """
    if markup is None:
        return None

    if not isinstance(markup, InlineKeyboardMarkup):
        return markup

    if not await is_ultima_mode_enabled_cached():
        return markup

    filtered_rows = []
    for row in markup.inline_keyboard:
        filtered_row = [button for button in row if not _is_bot_menu_callback(getattr(button, 'callback_data', None))]
        if filtered_row:
            filtered_rows.append(filtered_row)

    if not filtered_rows:
        return None

    return InlineKeyboardMarkup(inline_keyboard=filtered_rows)

