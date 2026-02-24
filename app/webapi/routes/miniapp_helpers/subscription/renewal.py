from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.tariff import get_tariff_by_id
from app.database.models import Subscription, User
from app.services.subscription_renewal_service import SubscriptionRenewalService
from app.utils.pricing_utils import format_period_description
from app.webapi.schemas.miniapp import MiniAppSubscriptionRenewalPeriod


async def prepare_subscription_renewal_options(
    db: AsyncSession,
    user: User,
    subscription: Subscription,
    renewal_service: SubscriptionRenewalService,
    logger: Any,
) -> tuple[list[MiniAppSubscriptionRenewalPeriod], dict[str | int, dict[str, Any]], str | None]:
    option_payloads: list[tuple[MiniAppSubscriptionRenewalPeriod, dict[str, Any]]] = []

    tariff_id = getattr(subscription, 'tariff_id', None)
    tariff = await get_tariff_by_id(db, tariff_id) if tariff_id else None

    if tariff and tariff.period_prices:
        promo_group = (
            user.get_primary_promo_group()
            if hasattr(user, 'get_primary_promo_group')
            else getattr(user, 'promo_group', None)
        )

        period_discounts: dict[int, int] = {}
        if promo_group:
            raw_discounts = getattr(promo_group, 'period_discounts', None) or {}
            for key, value in raw_discounts.items():
                try:
                    period_discounts[int(key)] = max(0, min(100, int(value)))
                except (TypeError, ValueError):
                    continue

        for period_str, original_price_kopeks in sorted(tariff.period_prices.items(), key=lambda item: int(item[0])):
            period_days = int(period_str)
            discount_percent = period_discounts.get(period_days, 0)
            if discount_percent > 0:
                price_kopeks = int(original_price_kopeks * (100 - discount_percent) / 100)
            else:
                price_kopeks = original_price_kopeks

            months = max(1, period_days // 30)
            per_month = price_kopeks // months if months > 0 else price_kopeks
            label = format_period_description(
                period_days,
                getattr(user, 'language', settings.DEFAULT_LANGUAGE),
            )
            price_label = settings.format_price(price_kopeks)
            original_label = settings.format_price(original_price_kopeks) if discount_percent > 0 else None
            per_month_label = settings.format_price(per_month)

            option_model = MiniAppSubscriptionRenewalPeriod(
                id=f'tariff_{tariff.id}_{period_days}',
                days=period_days,
                months=months,
                price_kopeks=price_kopeks,
                price_label=price_label,
                original_price_kopeks=original_price_kopeks if discount_percent > 0 else None,
                original_price_label=original_label,
                discount_percent=discount_percent,
                price_per_month_kopeks=per_month,
                price_per_month_label=per_month_label,
                title=label,
            )

            pricing = {
                'period_id': option_model.id,
                'period_days': period_days,
                'months': months,
                'final_total': price_kopeks,
                'base_original_total': original_price_kopeks if discount_percent > 0 else price_kopeks,
                'overall_discount_percent': discount_percent,
                'per_month': per_month,
                'tariff_id': tariff.id,
            }
            option_payloads.append((option_model, pricing))
    else:
        available_periods = [period for period in settings.get_available_renewal_periods() if period > 0]
        for period_days in available_periods:
            try:
                pricing_model = await renewal_service.calculate_pricing(
                    db,
                    user,
                    subscription,
                    period_days,
                )
                pricing = pricing_model.to_payload()
            except Exception as error:  # pragma: no cover - defensive logging
                logger.warning(
                    'Failed to calculate renewal pricing for subscription (period)',
                    subscription_id=subscription.id,
                    period_days=period_days,
                    error=error,
                )
                continue

            label = format_period_description(
                period_days,
                getattr(user, 'language', settings.DEFAULT_LANGUAGE),
            )
            price_label = settings.format_price(pricing['final_total'])
            original_label = None
            if pricing['base_original_total'] and pricing['base_original_total'] != pricing['final_total']:
                original_label = settings.format_price(pricing['base_original_total'])
            per_month_label = settings.format_price(pricing['per_month'])

            option_model = MiniAppSubscriptionRenewalPeriod(
                id=pricing['period_id'],
                days=period_days,
                months=pricing['months'],
                price_kopeks=pricing['final_total'],
                price_label=price_label,
                original_price_kopeks=pricing['base_original_total'],
                original_price_label=original_label,
                discount_percent=pricing['overall_discount_percent'],
                price_per_month_kopeks=pricing['per_month'],
                price_per_month_label=per_month_label,
                title=label,
            )
            option_payloads.append((option_model, pricing))

    if not option_payloads:
        return [], {}, None

    option_payloads.sort(key=lambda item: item[0].days or 0)
    recommended_option = max(
        option_payloads,
        key=lambda item: (
            item[1]['overall_discount_percent'],
            item[0].months or 0,
            -(item[1]['final_total'] or 0),
        ),
    )
    recommended_option[0].is_recommended = True

    pricing_map: dict[str | int, dict[str, Any]] = {}
    for option_model, pricing in option_payloads:
        pricing_map[option_model.id] = pricing
        pricing_map[pricing['period_days']] = pricing
        pricing_map[str(pricing['period_days'])] = pricing

    periods = [item[0] for item in option_payloads]
    return periods, pricing_map, recommended_option[0].id
