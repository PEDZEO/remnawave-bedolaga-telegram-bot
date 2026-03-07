from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import SystemSetting


ULTIMA_AGREEMENT_KEY = 'CABINET_ULTIMA_AGREEMENT_CONTENT'
DEFAULT_ULTIMA_AGREEMENT_CONTENT = (
    '<h3>Пользовательское соглашение</h3>'
    '<p>Используя сервис, вы подтверждаете согласие с правилами использования.</p>'
)


@dataclass(slots=True)
class UltimaAgreementContent:
    requested_language: str
    language: str
    content: str
    updated_at: str | None


def _normalize_language(value: str | None) -> str:
    default_language = str(getattr(settings, 'DEFAULT_LANGUAGE', 'ru') or 'ru')
    normalized = (value or default_language).strip().lower().split('-', 1)[0]
    return normalized or default_language


def _load_translations(raw_value: str | None) -> dict[str, str]:
    if not raw_value:
        return {}
    try:
        loaded = json.loads(raw_value)
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(loaded, dict):
        return {}
    result: dict[str, str] = {}
    for key, value in loaded.items():
        lang = _normalize_language(str(key))
        text = str(value or '').strip()
        if text:
            result[lang] = text
    return result


async def get_ultima_agreement(db: AsyncSession, language: str | None) -> UltimaAgreementContent:
    requested_language = _normalize_language(language)
    default_language = _normalize_language(getattr(settings, 'DEFAULT_LANGUAGE', 'ru'))

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == ULTIMA_AGREEMENT_KEY))
    setting = result.scalar_one_or_none()
    translations = _load_translations(setting.value if setting else None)

    resolved_language = requested_language
    content = translations.get(resolved_language, '')
    if not content and default_language != resolved_language:
        fallback_content = translations.get(default_language, '')
        if fallback_content:
            resolved_language = default_language
            content = fallback_content

    if not content:
        content = DEFAULT_ULTIMA_AGREEMENT_CONTENT

    updated_at = setting.updated_at.isoformat() if setting and setting.updated_at else None
    return UltimaAgreementContent(
        requested_language=requested_language,
        language=resolved_language,
        content=content,
        updated_at=updated_at,
    )


async def set_ultima_agreement(db: AsyncSession, language: str | None, content: str) -> UltimaAgreementContent:
    lang = _normalize_language(language)
    normalized_content = str(content or '').strip() or DEFAULT_ULTIMA_AGREEMENT_CONTENT

    result = await db.execute(select(SystemSetting).where(SystemSetting.key == ULTIMA_AGREEMENT_KEY))
    setting = result.scalar_one_or_none()

    translations = _load_translations(setting.value if setting else None)
    translations[lang] = normalized_content

    payload = json.dumps(translations, ensure_ascii=False)

    if setting is None:
        setting = SystemSetting(key=ULTIMA_AGREEMENT_KEY, value=payload)
        db.add(setting)
    else:
        setting.value = payload

    await db.flush()
    return await get_ultima_agreement(db, lang)
