from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import settings


DEFAULT_SUPPORT_CONTACT_BUTTON_TEXT = '💬 Написать в поддержку'


def build_support_contact_keyboard(
    button_text: str = DEFAULT_SUPPORT_CONTACT_BUTTON_TEXT,
) -> InlineKeyboardMarkup | None:
    support_url = settings.get_support_contact_url()

    if not support_url:
        return None

    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=button_text, url=support_url)]],
    )
