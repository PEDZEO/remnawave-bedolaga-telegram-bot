from __future__ import annotations

import json
from dataclasses import dataclass

from aiogram import types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import SystemSetting
from app.utils.miniapp_url import add_miniapp_cache_buster


ULTIMA_MODE_ENABLED_KEY = 'CABINET_ULTIMA_MODE_ENABLED'
ULTIMA_START_CONFIG_KEY = 'ULTIMA_START_BOT_CONFIG'

DEFAULT_MESSAGE_TEXT = (
    '🙌 <b>Первые 3 дня бесплатно для всех пользователей:</b>\n\n'
    '1️⃣ Откройте приложение\n'
    '2️⃣ Нажмите «Установка и настройка» и следуйте инструкции, чтобы подключить устройство\n'
    '3️⃣ Готово! Пользуйтесь VPN бесплатно 3 дня\n\n'
    'Возникли вопросы или сложности? Напишите в службу поддержки, мы обязательно вам поможем 👨🏻‍💻'
)
DEFAULT_BUTTON_TEXT = '📱 Приложение'


@dataclass(slots=True)
class UltimaStartConfig:
    message_text: str
    button_text: str
    button_url: str


async def is_ultima_mode_enabled(db: AsyncSession) -> bool:
    result = await db.execute(select(SystemSetting.value).where(SystemSetting.key == ULTIMA_MODE_ENABLED_KEY))
    value = result.scalar_one_or_none()
    return str(value).strip().lower() == 'true'


async def get_ultima_start_config(db: AsyncSession) -> UltimaStartConfig:
    result = await db.execute(select(SystemSetting.value).where(SystemSetting.key == ULTIMA_START_CONFIG_KEY))
    raw = result.scalar_one_or_none()

    payload: dict[str, str] = {}
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                payload = loaded
        except (TypeError, json.JSONDecodeError):
            payload = {}

    message_text = str(payload.get('message_text') or DEFAULT_MESSAGE_TEXT).strip()
    button_text = str(payload.get('button_text') or DEFAULT_BUTTON_TEXT).strip()
    button_url = _normalize_button_url(payload.get('button_url'))

    return UltimaStartConfig(
        message_text=message_text or DEFAULT_MESSAGE_TEXT,
        button_text=button_text or DEFAULT_BUTTON_TEXT,
        button_url=button_url,
    )


async def set_ultima_start_config(
    db: AsyncSession,
    *,
    message_text: str,
    button_text: str,
    button_url: str,
) -> UltimaStartConfig:
    config = UltimaStartConfig(
        message_text=message_text.strip() or DEFAULT_MESSAGE_TEXT,
        button_text=button_text.strip() or DEFAULT_BUTTON_TEXT,
        button_url=_normalize_button_url(button_url),
    )

    payload = {
        'message_text': config.message_text,
        'button_text': config.button_text,
        'button_url': config.button_url,
    }

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == ULTIMA_START_CONFIG_KEY))
    setting = result.scalar_one_or_none()
    if setting is None:
        setting = SystemSetting(key=ULTIMA_START_CONFIG_KEY, value=json.dumps(payload, ensure_ascii=False))
        db.add(setting)
    else:
        setting.value = json.dumps(payload, ensure_ascii=False)

    await db.flush()
    return config


def build_ultima_start_keyboard(config: UltimaStartConfig) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=config.button_text,
                    web_app=types.WebAppInfo(url=config.button_url),
                )
            ]
        ]
    )


def _normalize_button_url(value: object) -> str:
    raw = str(value or '').strip()
    if raw.startswith('http://') or raw.startswith('https://'):
        return add_miniapp_cache_buster(raw)

    miniapp_url = (settings.MINIAPP_CUSTOM_URL or '').strip()
    if miniapp_url.startswith('http://') or miniapp_url.startswith('https://'):
        return add_miniapp_cache_buster(miniapp_url)

    bot_username = (settings.BOT_USERNAME or '').strip().lstrip('@')
    if bot_username:
        return f'https://t.me/{bot_username}/app'

    return 'https://t.me'
