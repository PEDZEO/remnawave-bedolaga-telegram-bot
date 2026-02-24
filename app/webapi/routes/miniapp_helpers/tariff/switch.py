from __future__ import annotations

from app.utils.promo_offer import get_user_active_promo_discount_percent

from .base import get_tariff_monthly_price


def get_user_period_discount(user, period_days: int) -> int:
    """Получает скидку пользователя на период (унифицировано с ботом)."""
    promo_group = getattr(user, 'promo_group', None) if user else None

    if promo_group:
        discount = promo_group.get_discount_percent('period', period_days)
        if discount > 0:
            return discount

    personal_discount = get_user_active_promo_discount_percent(user) if user else 0
    return personal_discount


def apply_promo_discount(price: int, discount_percent: int) -> int:
    """Применяет скидку к цене."""
    if discount_percent <= 0:
        return price
    discount = int(price * discount_percent / 100)
    return max(0, price - discount)


def calculate_tariff_switch_cost(
    current_tariff,
    new_tariff,
    remaining_days: int,
    promo_group=None,
    user=None,
) -> tuple[int, bool]:
    """
    Рассчитывает стоимость переключения тарифа.
    Логика унифицирована с ботом (tariff_purchase.py).

    Формула: (new_monthly - current_monthly) * remaining_days / 30
    Скидка применяется к обоим тарифам одинаково.

    Returns:
        (cost_kopeks, is_upgrade) - стоимость доплаты и флаг апгрейда
    """
    current_monthly = get_tariff_monthly_price(current_tariff)
    new_monthly = get_tariff_monthly_price(new_tariff)

    discount_percent = get_user_period_discount(user, 30) if user else 0

    # Fallback на promo_group.period_discounts если user не передан
    if discount_percent == 0 and promo_group:
        raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
        for key, value in raw_discounts.items():
            try:
                if int(key) == 30:
                    discount_percent = max(0, min(100, int(value)))
                    break
            except (TypeError, ValueError):
                pass

    if discount_percent > 0:
        current_monthly = apply_promo_discount(current_monthly, discount_percent)
        new_monthly = apply_promo_discount(new_monthly, discount_percent)

    price_diff = new_monthly - current_monthly

    if price_diff <= 0:
        return 0, False

    upgrade_cost = int(price_diff * remaining_days / 30)
    return upgrade_cost, True
