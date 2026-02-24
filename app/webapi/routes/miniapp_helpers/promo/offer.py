import re
from typing import Any

from app.config import settings
from app.database.models import PromoOfferTemplate


_TEMPLATE_ID_PATTERN = re.compile(r'promo_template_(?P<template_id>\d+)$')
_OFFER_TYPE_ICONS = {
    'extend_discount': '💎',
    'purchase_discount': '🎯',
    'test_access': '🧪',
}
_EFFECT_TYPE_ICONS = {
    'percent_discount': '🎁',
    'test_access': '🧪',
    'balance_bonus': '💰',
}
_DEFAULT_OFFER_ICON = '🎉'


def extract_template_id(notification_type: str | None) -> int | None:
    if not notification_type:
        return None

    match = _TEMPLATE_ID_PATTERN.match(notification_type)
    if not match:
        return None

    try:
        return int(match.group('template_id'))
    except (TypeError, ValueError):
        return None


def extract_offer_extra(offer: Any) -> dict[str, Any]:
    extra = getattr(offer, 'extra_data', None)
    return extra if isinstance(extra, dict) else {}


def extract_offer_type(offer: Any, template: PromoOfferTemplate | None) -> str | None:
    extra = extract_offer_extra(offer)
    offer_type = extra.get('offer_type') if isinstance(extra.get('offer_type'), str) else None
    if offer_type:
        return offer_type
    template_type = getattr(template, 'offer_type', None)
    return template_type if isinstance(template_type, str) else None


def normalize_effect_type(effect_type: str | None) -> str:
    normalized = (effect_type or 'percent_discount').strip().lower()
    if normalized == 'balance_bonus':
        return 'percent_discount'
    return normalized or 'percent_discount'


def determine_offer_icon(offer_type: str | None, effect_type: str) -> str:
    if offer_type and offer_type in _OFFER_TYPE_ICONS:
        return _OFFER_TYPE_ICONS[offer_type]
    if effect_type in _EFFECT_TYPE_ICONS:
        return _EFFECT_TYPE_ICONS[effect_type]
    return _DEFAULT_OFFER_ICON


def extract_offer_test_squad_uuids(offer: Any) -> list[str]:
    extra = extract_offer_extra(offer)
    raw = extra.get('test_squad_uuids') or extra.get('squads') or []

    if isinstance(raw, str):
        raw = [raw]

    uuids: list[str] = []
    try:
        for item in raw:
            if not item:
                continue
            uuids.append(str(item))
    except TypeError:
        return []

    return uuids


def format_offer_message(
    template: PromoOfferTemplate | None,
    offer: Any,
    *,
    server_name: str | None = None,
) -> str | None:
    message_template: str | None = None

    if template and isinstance(template.message_text, str):
        message_template = template.message_text
    else:
        extra = extract_offer_extra(offer)
        raw_message = extra.get('message_text') or extra.get('text')
        if isinstance(raw_message, str):
            message_template = raw_message

    if not message_template:
        return None

    extra = extract_offer_extra(offer)
    discount_percent = getattr(offer, 'discount_percent', None)
    try:
        discount_percent = int(discount_percent)
    except (TypeError, ValueError):
        discount_percent = None

    replacements: dict[str, Any] = {}
    if discount_percent is not None:
        replacements.setdefault('discount_percent', discount_percent)

    for key in ('valid_hours', 'active_discount_hours', 'test_duration_hours'):
        value = extra.get(key)
        if value is None and template is not None:
            template_value = getattr(template, key, None)
        else:
            template_value = None
        replacements.setdefault(key, value if value is not None else template_value)

    if replacements.get('active_discount_hours') is None and template:
        replacements['active_discount_hours'] = getattr(template, 'valid_hours', None)

    if replacements.get('test_duration_hours') is None and template:
        replacements['test_duration_hours'] = getattr(template, 'test_duration_hours', None)

    if server_name:
        replacements.setdefault('server_name', server_name)

    for key, value in extra.items():
        if isinstance(key, str) and key not in replacements and isinstance(value, (str, int, float)):
            replacements[key] = value

    try:
        return message_template.format(**replacements)
    except Exception:  # pragma: no cover - fallback for malformed templates
        return message_template


def extract_offer_duration_hours(
    offer: Any,
    template: PromoOfferTemplate | None,
    effect_type: str,
) -> int | None:
    extra = extract_offer_extra(offer)
    if effect_type == 'test_access':
        source = extra.get('test_duration_hours')
        if source is None and template is not None:
            source = getattr(template, 'test_duration_hours', None)
    else:
        source = extra.get('active_discount_hours')
        if source is None and template is not None:
            source = getattr(template, 'active_discount_hours', None)

    try:
        if source is None:
            return None
        hours = int(float(source))
        return hours if hours > 0 else None
    except (TypeError, ValueError):
        return None


def format_bonus_label(amount_kopeks: int) -> str | None:
    if amount_kopeks <= 0:
        return None
    try:
        return settings.format_price(amount_kopeks)
    except Exception:  # pragma: no cover - defensive
        return f'{amount_kopeks / 100:.2f}'
