from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.crud.promo_offer_template import get_promo_offer_template_by_id
from app.database.models import PromoOfferTemplate, Subscription, SubscriptionTemporaryAccess, User

from ..miniapp_promo_offer_helpers import (
    determine_offer_icon,
    extract_offer_duration_hours,
    extract_offer_extra,
    extract_offer_test_squad_uuids,
    extract_offer_type,
    extract_template_id,
    format_bonus_label,
    format_offer_message,
    normalize_effect_type,
)
from ..schemas.miniapp import MiniAppConnectedServer, MiniAppPromoOffer
from .runtime import resolve_connected_servers


ActiveOfferContext = tuple[Any, int | None, datetime | None]


async def find_active_test_access_offers(
    db: AsyncSession,
    subscription: Subscription | None,
) -> list[ActiveOfferContext]:
    if not subscription or not getattr(subscription, 'id', None):
        return []

    now = datetime.now(UTC)
    result = await db.execute(
        select(SubscriptionTemporaryAccess)
        .options(selectinload(SubscriptionTemporaryAccess.offer))
        .where(
            SubscriptionTemporaryAccess.subscription_id == subscription.id,
            SubscriptionTemporaryAccess.is_active == True,
            SubscriptionTemporaryAccess.expires_at > now,
        )
        .order_by(SubscriptionTemporaryAccess.expires_at.desc())
    )

    entries = list(result.scalars().all())
    if not entries:
        return []

    offer_map: dict[int, tuple[Any, datetime | None]] = {}
    for entry in entries:
        offer = getattr(entry, 'offer', None)
        if not offer:
            continue

        effect_type = normalize_effect_type(getattr(offer, 'effect_type', None))
        if effect_type != 'test_access':
            continue

        expires_at = getattr(entry, 'expires_at', None)
        if not expires_at or expires_at <= now:
            continue

        offer_id = getattr(offer, 'id', None)
        if not isinstance(offer_id, int):
            continue

        current = offer_map.get(offer_id)
        if current is None:
            offer_map[offer_id] = (offer, expires_at)
        else:
            _, current_expiry = current
            if current_expiry is None or (expires_at and expires_at > current_expiry):
                offer_map[offer_id] = (offer, expires_at)

    contexts: list[ActiveOfferContext] = []
    for offer, expires_at in offer_map.values():
        contexts.append((offer, None, expires_at))

    contexts.sort(key=lambda item: item[2] or now, reverse=True)
    return contexts


async def build_promo_offer_models(
    db: AsyncSession,
    available_offers: list[Any],
    active_offers: list[ActiveOfferContext] | None,
    *,
    user: User,
) -> list[MiniAppPromoOffer]:
    promo_offers: list[MiniAppPromoOffer] = []
    template_cache: dict[int, PromoOfferTemplate | None] = {}

    candidates: list[Any] = [offer for offer in available_offers if offer]
    active_offer_contexts: list[ActiveOfferContext] = []
    if active_offers:
        for offer, discount_override, expires_override in active_offers:
            if not offer:
                continue
            active_offer_contexts.append((offer, discount_override, expires_override))
            candidates.append(offer)

    squad_map: dict[str, MiniAppConnectedServer] = {}
    if candidates:
        all_uuids: list[str] = []
        for offer in candidates:
            all_uuids.extend(extract_offer_test_squad_uuids(offer))
        if all_uuids:
            unique = list(dict.fromkeys(all_uuids))
            resolved = await resolve_connected_servers(db, unique)
            squad_map = {server.uuid: server for server in resolved}

    async def get_template(template_id: int | None) -> PromoOfferTemplate | None:
        if not template_id:
            return None
        if template_id not in template_cache:
            template_cache[template_id] = await get_promo_offer_template_by_id(db, template_id)
        return template_cache[template_id]

    def build_test_squads(offer: Any) -> list[MiniAppConnectedServer]:
        test_squads: list[MiniAppConnectedServer] = []
        for uuid in extract_offer_test_squad_uuids(offer):
            resolved = squad_map.get(uuid)
            if resolved:
                test_squads.append(MiniAppConnectedServer(uuid=resolved.uuid, name=resolved.name))
            else:
                test_squads.append(MiniAppConnectedServer(uuid=uuid, name=uuid))
        return test_squads

    def resolve_title(
        offer: Any,
        template: PromoOfferTemplate | None,
        offer_type: str | None,
    ) -> str | None:
        extra = extract_offer_extra(offer)
        if isinstance(extra.get('title'), str) and extra['title'].strip():
            return extra['title'].strip()
        if template and template.name:
            return template.name
        if offer_type:
            return offer_type.replace('_', ' ').title()
        return None

    for offer in available_offers:
        template_id = extract_template_id(getattr(offer, 'notification_type', None))
        template = await get_template(template_id)
        effect_type = normalize_effect_type(getattr(offer, 'effect_type', None))
        offer_type = extract_offer_type(offer, template)
        test_squads = build_test_squads(offer)
        server_name = test_squads[0].name if test_squads else None
        message_text = format_offer_message(template, offer, server_name=server_name)
        bonus_label = format_bonus_label(int(getattr(offer, 'bonus_amount_kopeks', 0) or 0))
        discount_percent = getattr(offer, 'discount_percent', 0)
        try:
            discount_percent = int(discount_percent)
        except (TypeError, ValueError):
            discount_percent = 0

        extra = extract_offer_extra(offer)
        button_text = None
        if isinstance(extra.get('button_text'), str) and extra['button_text'].strip():
            button_text = extra['button_text'].strip()
        elif template and isinstance(template.button_text, str):
            button_text = template.button_text

        promo_offers.append(
            MiniAppPromoOffer(
                id=int(getattr(offer, 'id', 0) or 0),
                status='pending',
                notification_type=getattr(offer, 'notification_type', None),
                offer_type=offer_type,
                effect_type=effect_type,
                discount_percent=max(0, discount_percent),
                bonus_amount_kopeks=int(getattr(offer, 'bonus_amount_kopeks', 0) or 0),
                bonus_amount_label=bonus_label,
                expires_at=getattr(offer, 'expires_at', None),
                claimed_at=getattr(offer, 'claimed_at', None),
                is_active=bool(getattr(offer, 'is_active', False)),
                template_id=template_id,
                template_name=getattr(template, 'name', None),
                button_text=button_text,
                title=resolve_title(offer, template, offer_type),
                message_text=message_text,
                icon=determine_offer_icon(offer_type, effect_type),
                test_squads=test_squads,
            )
        )

    if active_offer_contexts:
        seen_active_ids: set[int] = set()
        for active_offer_record, discount_override, expires_override in reversed(active_offer_contexts):
            offer_id = int(getattr(active_offer_record, 'id', 0) or 0)
            if offer_id and offer_id in seen_active_ids:
                continue
            if offer_id:
                seen_active_ids.add(offer_id)

            template_id = extract_template_id(getattr(active_offer_record, 'notification_type', None))
            template = await get_template(template_id)
            effect_type = normalize_effect_type(getattr(active_offer_record, 'effect_type', None))
            offer_type = extract_offer_type(active_offer_record, template)
            discount_value = discount_override if discount_override is not None else 0
            show_active = (discount_value and discount_value > 0) or effect_type == 'test_access'
            if not show_active:
                continue

            test_squads = build_test_squads(active_offer_record)
            server_name = test_squads[0].name if test_squads else None
            message_text = format_offer_message(template, active_offer_record, server_name=server_name)
            bonus_label = format_bonus_label(int(getattr(active_offer_record, 'bonus_amount_kopeks', 0) or 0))

            started_at = getattr(active_offer_record, 'claimed_at', None)
            expires_at = expires_override or getattr(active_offer_record, 'expires_at', None)
            duration_seconds: int | None = None
            duration_hours = extract_offer_duration_hours(active_offer_record, template, effect_type)
            if expires_at is None and duration_hours and started_at:
                expires_at = started_at + timedelta(hours=duration_hours)
            if expires_at and started_at:
                try:
                    duration_seconds = int((expires_at - started_at).total_seconds())
                except Exception:  # pragma: no cover - defensive
                    duration_seconds = None

            if (discount_value is None or discount_value <= 0) and effect_type != 'test_access':
                try:
                    discount_value = int(getattr(active_offer_record, 'discount_percent', 0) or 0)
                except (TypeError, ValueError):
                    discount_value = 0
            if discount_value is None:
                discount_value = 0

            extra = extract_offer_extra(active_offer_record)
            button_text = None
            if isinstance(extra.get('button_text'), str) and extra['button_text'].strip():
                button_text = extra['button_text'].strip()
            elif template and isinstance(template.button_text, str):
                button_text = template.button_text

            promo_offers.insert(
                0,
                MiniAppPromoOffer(
                    id=offer_id,
                    status='active',
                    notification_type=getattr(active_offer_record, 'notification_type', None),
                    offer_type=offer_type,
                    effect_type=effect_type,
                    discount_percent=max(0, discount_value or 0),
                    bonus_amount_kopeks=int(getattr(active_offer_record, 'bonus_amount_kopeks', 0) or 0),
                    bonus_amount_label=bonus_label,
                    expires_at=getattr(active_offer_record, 'expires_at', None),
                    claimed_at=started_at,
                    is_active=False,
                    template_id=template_id,
                    template_name=getattr(template, 'name', None),
                    button_text=button_text,
                    title=resolve_title(active_offer_record, template, offer_type),
                    message_text=message_text,
                    icon=determine_offer_icon(offer_type, effect_type),
                    test_squads=test_squads,
                    active_discount_expires_at=expires_at,
                    active_discount_started_at=started_at,
                    active_discount_duration_seconds=duration_seconds,
                ),
            )

    return promo_offers
