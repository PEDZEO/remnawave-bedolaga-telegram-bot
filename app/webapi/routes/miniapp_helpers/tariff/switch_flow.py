from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException, status

from app.config import settings

from .switch import calculate_tariff_switch_cost


@dataclass(slots=True)
class TariffSwitchPricing:
    upgrade_cost: int
    is_upgrade: bool
    switching_from_daily: bool
    new_period_days: int


def calculate_switch_pricing(
    current_tariff,
    new_tariff,
    remaining_days: int,
    promo_group,
    user,
) -> TariffSwitchPricing:
    current_is_daily = getattr(current_tariff, 'is_daily', False) if current_tariff else False
    new_is_daily = getattr(new_tariff, 'is_daily', False)
    switching_from_daily = current_is_daily and not new_is_daily

    if switching_from_daily:
        min_period_days = 30
        min_period_price = 0
        if new_tariff.period_prices:
            min_period_days = min(int(key) for key in new_tariff.period_prices.keys())
            min_period_price = new_tariff.period_prices.get(str(min_period_days), 0)
        return TariffSwitchPricing(
            upgrade_cost=int(min_period_price),
            is_upgrade=min_period_price > 0,
            switching_from_daily=True,
            new_period_days=int(min_period_days),
        )

    upgrade_cost, is_upgrade = calculate_tariff_switch_cost(
        current_tariff,
        new_tariff,
        remaining_days,
        promo_group,
        user,
    )
    return TariffSwitchPricing(
        upgrade_cost=int(upgrade_cost),
        is_upgrade=bool(is_upgrade),
        switching_from_daily=False,
        new_period_days=0,
    )


def ensure_switch_balance(user, upgrade_cost: int) -> None:
    if user.balance_kopeks >= upgrade_cost:
        return

    missing = upgrade_cost - user.balance_kopeks
    raise HTTPException(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        detail={
            'code': 'insufficient_funds',
            'message': f'Недостаточно средств. Не хватает {settings.format_price(missing)}',
            'missing_amount': missing,
        },
    )


def build_switch_charge_description(
    *,
    new_tariff_name: str,
    switching_from_daily: bool,
    new_period_days: int,
    remaining_days: int,
) -> str:
    if switching_from_daily:
        return f"Переход с суточного на тариф '{new_tariff_name}' ({new_period_days} дней)"
    return f"Переход на тариф '{new_tariff_name}' (доплата за {remaining_days} дней)"


def build_switch_result_message(language: str, tariff_name: str, upgrade_cost: int) -> str:
    if upgrade_cost > 0:
        if language == 'ru':
            return f"Тариф изменён на '{tariff_name}'. Списано {settings.format_price(upgrade_cost)}"
        return f"Switched to '{tariff_name}'. Charged {settings.format_price(upgrade_cost)}"

    if language == 'ru':
        return f"Тариф изменён на '{tariff_name}'"
    return f"Switched to '{tariff_name}'"
