import re

from fastapi import HTTPException, status

from app.database.models import Subscription, User
from app.utils.pricing_utils import get_remaining_months


_PERIOD_ID_PATTERN = re.compile(r'(\d+)')


def parse_period_identifier(identifier: str | None) -> int | None:
    if not identifier:
        return None

    match = _PERIOD_ID_PATTERN.search(str(identifier))
    if not match:
        return None

    try:
        return int(match.group(1))
    except (TypeError, ValueError):
        return None


def get_addon_discount_percent_for_user(
    user: User | None,
    category: str,
    period_days_hint: int | None = None,
) -> int:
    if user is None:
        return 0

    promo_group = getattr(user, 'promo_group', None)
    if promo_group is None:
        return 0

    if not getattr(promo_group, 'apply_discounts_to_addons', True):
        return 0

    try:
        percent = user.get_promo_discount(category, period_days_hint)
    except AttributeError:
        return 0

    try:
        return int(percent)
    except (TypeError, ValueError):
        return 0


def get_period_hint_from_subscription(
    subscription: Subscription | None,
) -> int | None:
    if not subscription:
        return None

    months_remaining = get_remaining_months(subscription.end_date)
    if months_remaining <= 0:
        return None

    return months_remaining * 30


def validate_subscription_id(
    requested_id: int | None,
    subscription: Subscription,
) -> None:
    if requested_id is None:
        return

    try:
        requested = int(requested_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'invalid_subscription_id',
                'message': 'Invalid subscription identifier',
            },
        ) from None

    if requested != subscription.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={
                'code': 'subscription_mismatch',
                'message': 'Subscription does not belong to the authorized user',
            },
        )
