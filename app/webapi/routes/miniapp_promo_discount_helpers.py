from typing import Any

from app.database.models import PromoGroup


def safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def normalize_period_discounts(raw: dict[Any, Any] | None) -> dict[str, int]:
    if not isinstance(raw, dict):
        return {}

    normalized: dict[str, int] = {}
    for key, value in raw.items():
        try:
            period = int(key)
            normalized[str(period)] = int(value)
        except (TypeError, ValueError):
            continue

    return normalized


def extract_promo_discounts(group: PromoGroup | None) -> dict[str, Any]:
    if not group:
        return {
            'server_discount_percent': 0,
            'traffic_discount_percent': 0,
            'device_discount_percent': 0,
            'period_discounts': {},
            'apply_discounts_to_addons': True,
        }

    return {
        'server_discount_percent': max(0, safe_int(getattr(group, 'server_discount_percent', 0))),
        'traffic_discount_percent': max(0, safe_int(getattr(group, 'traffic_discount_percent', 0))),
        'device_discount_percent': max(0, safe_int(getattr(group, 'device_discount_percent', 0))),
        'period_discounts': normalize_period_discounts(getattr(group, 'period_discounts', None)),
        'apply_discounts_to_addons': bool(getattr(group, 'apply_discounts_to_addons', True)),
    }
