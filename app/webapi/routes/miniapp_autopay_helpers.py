"""Autopay helper functions for miniapp routes."""

from typing import Any

from app.config import settings
from app.database.models import Subscription

from ..schemas.miniapp import MiniAppSubscriptionAutopay


_AUTOPAY_DEFAULT_DAY_OPTIONS = (1, 3, 7, 14)


def _normalize_autopay_days(value: Any | None) -> int | None:
    if value is None:
        return None
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None
    return numeric if numeric >= 0 else None


def _get_autopay_day_options(subscription: Subscription | None) -> list[int]:
    options: set[int] = set()
    for candidate in _AUTOPAY_DEFAULT_DAY_OPTIONS:
        normalized = _normalize_autopay_days(candidate)
        if normalized is not None:
            options.add(normalized)

    default_setting = _normalize_autopay_days(getattr(settings, 'DEFAULT_AUTOPAY_DAYS_BEFORE', None))
    if default_setting is not None:
        options.add(default_setting)

    if subscription is not None:
        current = _normalize_autopay_days(getattr(subscription, 'autopay_days_before', None))
        if current is not None:
            options.add(current)

    return sorted(options)


def _build_autopay_payload(
    subscription: Subscription | None,
) -> MiniAppSubscriptionAutopay | None:
    if subscription is None:
        return None

    enabled = bool(getattr(subscription, 'autopay_enabled', False))
    days_before = _normalize_autopay_days(getattr(subscription, 'autopay_days_before', None))
    options = _get_autopay_day_options(subscription)

    default_days = days_before
    if default_days is None:
        default_days = _normalize_autopay_days(getattr(settings, 'DEFAULT_AUTOPAY_DAYS_BEFORE', None))
    if default_days is None and options:
        default_days = options[0]

    autopay_kwargs: dict[str, Any] = {
        'enabled': enabled,
        'autopay_enabled': enabled,
        'days_before': days_before,
        'autopay_days_before': days_before,
        'default_days_before': default_days,
        'autopay_days_options': options,
        'days_options': options,
        'options': options,
        'available_days': options,
        'availableDays': options,
        'autopayEnabled': enabled,
        'autopayDaysBefore': days_before,
        'autopayDaysOptions': options,
        'daysBefore': days_before,
        'daysOptions': options,
        'defaultDaysBefore': default_days,
    }

    return MiniAppSubscriptionAutopay(**autopay_kwargs)


def _autopay_response_extras(
    enabled: bool,
    days_before: int | None,
    options: list[int],
    autopay_payload: MiniAppSubscriptionAutopay | None,
) -> dict[str, Any]:
    extras: dict[str, Any] = {
        'autopayEnabled': enabled,
        'autopayDaysBefore': days_before,
        'autopayDaysOptions': options,
    }
    if days_before is not None:
        extras['daysBefore'] = days_before
    if options:
        extras['daysOptions'] = options
    if autopay_payload is not None:
        extras['autopaySettings'] = autopay_payload
    return extras
