from typing import Any

from app.config import settings
from app.database.models import Subscription, User
from app.utils.promo_offer import get_user_active_promo_discount_percent
from app.utils.timezone import format_local_datetime

from .miniapp_format_helpers import format_payment_method_title


def normalize_language_code(user: User | None) -> str:
    language = getattr(user, 'language', None) or settings.DEFAULT_LANGUAGE or 'ru'
    return language.split('-')[0].lower()


def build_renewal_status_message(user: User | None) -> str:
    language_code = normalize_language_code(user)
    if language_code in {'ru', 'fa'}:
        return 'Стоимость указана с учётом ваших текущих серверов, трафика и устройств.'
    return 'Prices already include your current servers, traffic, and devices.'


def build_promo_offer_payload(user: User | None) -> dict[str, Any] | None:
    percent = get_user_active_promo_discount_percent(user)
    if percent <= 0:
        return None

    payload: dict[str, Any] = {'percent': percent}

    expires_at = getattr(user, 'promo_offer_discount_expires_at', None)
    if expires_at:
        payload['expires_at'] = expires_at

    language_code = normalize_language_code(user)
    if language_code in {'ru', 'fa'}:
        payload['message'] = 'Дополнительная скидка применяется автоматически.'
    else:
        payload['message'] = 'Extra discount is applied automatically.'

    return payload


def build_renewal_success_message(
    user: User,
    subscription: Subscription,
    charged_amount: int,
    promo_discount_value: int = 0,
) -> str:
    language_code = normalize_language_code(user)
    amount_label = settings.format_price(max(0, charged_amount))
    date_label = format_local_datetime(subscription.end_date, '%d.%m.%Y %H:%M') if subscription.end_date else ''

    if language_code in {'ru', 'fa'}:
        if charged_amount > 0:
            message = (
                f'Подписка продлена до {date_label}. ' if date_label else 'Подписка продлена. '
            ) + f'Списано {amount_label}.'
        else:
            message = f'Подписка продлена до {date_label}.' if date_label else 'Подписка успешно продлена.'
    elif charged_amount > 0:
        message = (
            f'Subscription renewed until {date_label}. ' if date_label else 'Subscription renewed. '
        ) + f'Charged {amount_label}.'
    else:
        message = f'Subscription renewed until {date_label}.' if date_label else 'Subscription renewed successfully.'

    if promo_discount_value > 0:
        discount_label = settings.format_price(promo_discount_value)
        if language_code in {'ru', 'fa'}:
            message += f' Применена дополнительная скидка {discount_label}.'
        else:
            message += f' Promo discount applied: {discount_label}.'

    return message


def build_renewal_pending_message(
    user: User,
    missing_amount: int,
    method: str,
) -> str:
    language_code = normalize_language_code(user)
    amount_label = settings.format_price(max(0, missing_amount))
    method_title = format_payment_method_title(method)

    if language_code in {'ru', 'fa'}:
        if method_title:
            return (
                f'Недостаточно средств на балансе. Доплатите {amount_label} через {method_title}, '
                'чтобы завершить продление.'
            )
        return f'Недостаточно средств на балансе. Доплатите {amount_label}, чтобы завершить продление.'

    if method_title:
        return f'Not enough balance. Pay the remaining {amount_label} via {method_title} to finish the renewal.'
    return f'Not enough balance. Pay the remaining {amount_label} to finish the renewal.'
