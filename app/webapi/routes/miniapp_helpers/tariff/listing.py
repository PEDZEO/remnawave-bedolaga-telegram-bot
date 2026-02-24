from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.crud.tariff import get_tariff_by_id, get_tariffs_for_user
from app.webapi.schemas.miniapp import (
    MiniAppCurrentTariff,
    MiniAppPromoGroup,
    MiniAppTariff,
)

from ..promo.discount import extract_promo_discounts
from ..tariff_state import build_current_tariff_model
from .model import build_tariff_model


def resolve_user_promo_group(user) -> tuple[Any, int | None]:
    promo_group = (
        user.get_primary_promo_group()
        if hasattr(user, 'get_primary_promo_group')
        else getattr(user, 'promo_group', None)
    )
    return promo_group, (promo_group.id if promo_group else None)


async def build_tariffs_payload(
    db: AsyncSession,
    user,
) -> tuple[list[MiniAppTariff], MiniAppCurrentTariff | None, MiniAppPromoGroup | None]:
    promo_group, promo_group_id = resolve_user_promo_group(user)
    tariffs = await get_tariffs_for_user(db, promo_group_id)

    subscription = getattr(user, 'subscription', None)
    current_tariff_id = subscription.tariff_id if subscription else None
    current_tariff_model: MiniAppCurrentTariff | None = None
    current_tariff = None

    remaining_days = 0
    if subscription and subscription.end_date:
        delta = subscription.end_date - datetime.now(UTC)
        remaining_days = max(0, delta.days)

    if current_tariff_id:
        current_tariff = await get_tariff_by_id(db, current_tariff_id)
        if current_tariff:
            current_tariff_model = await build_current_tariff_model(db, current_tariff, promo_group)

    tariff_models: list[MiniAppTariff] = []
    for tariff in tariffs:
        model = await build_tariff_model(
            db,
            tariff,
            current_tariff_id,
            promo_group,
            current_tariff=current_tariff,
            remaining_days=remaining_days,
            user=user,
        )
        tariff_models.append(model)

    promo_group_model = None
    if promo_group:
        promo_group_model = MiniAppPromoGroup(
            id=promo_group.id,
            name=promo_group.name,
            **extract_promo_discounts(promo_group),
        )

    return tariff_models, current_tariff_model, promo_group_model
