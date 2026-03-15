import re
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database.crud.subscription import (
    create_paid_subscription,
    extend_subscription,
    get_subscription_by_user_id,
)
from app.database.crud.tariff import get_tariff_by_id
from app.database.crud.transaction import create_transaction, emit_transaction_side_effects
from app.database.crud.user import subtract_user_balance
from app.database.models import (
    GuestPurchase,
    GuestPurchaseStatus,
    PaymentMethod,
    SystemSetting,
    Tariff,
    TransactionType,
    User,
    UserPromoGroup,
)
from app.services.guest_purchase_service import (
    GuestPurchaseError,
    activate_purchase as svc_activate,
    create_purchase,
    fulfill_purchase,
)
from app.services.payment_method_config_service import get_enabled_methods_for_user
from app.services.subscription_service import SubscriptionService
from app.utils.cache import RateLimitCache
from app.utils.promo_offer import get_user_active_promo_discount_percent

from ..dependencies import get_cabinet_db, get_current_cabinet_user
from ..schemas.gift import (
    ActivateGiftRequest,
    ActivateGiftResponse,
    GiftConfigPaymentMethod,
    GiftConfigResponse,
    GiftConfigSubOption,
    GiftConfigTariff,
    GiftConfigTariffPeriod,
    GiftExtendRequest,
    GiftExtendResponse,
    GiftPurchaseRequest,
    GiftPurchaseResponse,
    GiftPurchaseStatusResponse,
    PendingGiftResponse,
    ReceivedGiftResponse,
    SentGiftResponse,
)


logger = structlog.get_logger(__name__)

router = APIRouter(prefix='/gift', tags=['Cabinet Gift'])

GIFT_ENABLED_KEY = 'CABINET_GIFT_ENABLED'
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_TELEGRAM_RE = re.compile(r'^@?[a-zA-Z][a-zA-Z0-9_]{4,31}$')


def _gift_token_filter(token: str):
    return GuestPurchase.token == token if len(token) >= 64 else GuestPurchase.token.startswith(token)


async def _finalize_gateway_gift_via_balance(
    *,
    db: AsyncSession,
    user: User,
    purchase: GuestPurchase,
) -> GiftPurchaseStatusResponse:
    """Consume topped-up balance and finalize gift when gateway payment has arrived."""
    if purchase.status != GuestPurchaseStatus.PENDING.value:
        return GiftPurchaseStatusResponse(
            status=purchase.status,
            is_gift=True,
            is_code_only=purchase.is_gift and not purchase.gift_recipient_type,
            purchase_token=purchase.token[:12] if purchase.is_gift and not purchase.gift_recipient_type else None,
            recipient_contact_value=purchase.gift_recipient_value,
            gift_message=purchase.gift_message,
            tariff_name=purchase.tariff.name if purchase.tariff else None,
            period_days=purchase.period_days,
            warning=purchase.recipient_warning,
        )

    if user.balance_kopeks < purchase.amount_kopeks:
        return GiftPurchaseStatusResponse(
            status=purchase.status,
            is_gift=True,
            is_code_only=purchase.is_gift and not purchase.gift_recipient_type,
            purchase_token=purchase.token[:12] if purchase.is_gift and not purchase.gift_recipient_type else None,
            recipient_contact_value=purchase.gift_recipient_value,
            gift_message=purchase.gift_message,
            tariff_name=purchase.tariff.name if purchase.tariff else None,
            period_days=purchase.period_days,
            warning=purchase.recipient_warning,
        )

    tx_description = (
        f'Gift gateway settle: {purchase.tariff.name if purchase.tariff else "tariff"} ({purchase.period_days}d)'
    )
    if purchase.gift_recipient_value:
        tx_description += f' -> {purchase.gift_recipient_value}'

    ok = await subtract_user_balance(
        db,
        user,
        purchase.amount_kopeks,
        description=tx_description,
        create_transaction=False,
        consume_promo_offer=False,
    )
    if not ok:
        return GiftPurchaseStatusResponse(
            status=purchase.status,
            is_gift=True,
            is_code_only=purchase.is_gift and not purchase.gift_recipient_type,
            purchase_token=purchase.token[:12] if purchase.is_gift and not purchase.gift_recipient_type else None,
            recipient_contact_value=purchase.gift_recipient_value,
            gift_message=purchase.gift_message,
            tariff_name=purchase.tariff.name if purchase.tariff else None,
            period_days=purchase.period_days,
            warning=purchase.recipient_warning,
        )

    transaction = await create_transaction(
        db,
        user_id=user.id,
        type=TransactionType.GIFT_PAYMENT,
        amount_kopeks=purchase.amount_kopeks,
        description=tx_description,
        payment_method=PaymentMethod.BALANCE,
        commit=False,
    )
    purchase.status = GuestPurchaseStatus.PAID.value
    purchase.paid_at = datetime.now(UTC)
    await db.commit()

    await emit_transaction_side_effects(
        db,
        transaction,
        amount_kopeks=purchase.amount_kopeks,
        user_id=user.id,
        type=TransactionType.GIFT_PAYMENT,
        payment_method=PaymentMethod.BALANCE,
        description=tx_description,
    )

    try:
        await fulfill_purchase(db, purchase.token)
    except Exception:
        logger.exception('Failed to auto-fulfill gateway gift after balance settle', purchase_id=purchase.id)

    await db.refresh(purchase)
    return GiftPurchaseStatusResponse(
        status=purchase.status,
        is_gift=True,
        is_code_only=purchase.is_gift and not purchase.gift_recipient_type,
        purchase_token=purchase.token[:12] if purchase.is_gift and not purchase.gift_recipient_type else None,
        recipient_contact_value=purchase.gift_recipient_value,
        gift_message=purchase.gift_message,
        tariff_name=purchase.tariff.name if purchase.tariff else None,
        period_days=purchase.period_days,
        warning=purchase.recipient_warning,
    )


async def _get_setting_value(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(SystemSetting.value).where(SystemSetting.key == key))
    return result.scalar_one_or_none()


async def _is_gift_enabled(db: AsyncSession) -> bool:
    value = await _get_setting_value(db, GIFT_ENABLED_KEY)
    return bool(value and value.lower() == 'true')


async def _has_explicit_gift_tariffs(db: AsyncSession) -> bool:
    result = await db.execute(
        select(func.count(Tariff.id)).where(Tariff.is_active.is_(True), Tariff.show_in_gift.is_(True))
    )
    return (result.scalar_one() or 0) > 0


@router.get('/config', response_model=GiftConfigResponse)
async def get_gift_config(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    enabled = await _is_gift_enabled(db)
    if not enabled:
        return GiftConfigResponse(is_enabled=False, balance_kopeks=user.balance_kopeks)

    has_explicit_gift_tariffs = await _has_explicit_gift_tariffs(db)
    tariff_query = select(Tariff).where(Tariff.is_active.is_(True))
    if has_explicit_gift_tariffs:
        tariff_query = tariff_query.where(Tariff.show_in_gift.is_(True))

    result = await db.execute(tariff_query.order_by(Tariff.display_order, Tariff.id))
    tariffs_db = result.scalars().all()

    promo_group = user.get_primary_promo_group() if hasattr(user, 'get_primary_promo_group') else None
    if promo_group is None:
        promo_group = getattr(user, 'promo_group', None)
    promo_group_name = promo_group.name if promo_group else None
    promo_offer_discount_percent = get_user_active_promo_discount_percent(user)

    tariffs: list[GiftConfigTariff] = []
    for tariff in tariffs_db:
        period_days_list = tariff.get_available_periods()
        periods: list[GiftConfigTariffPeriod] = []
        for days in period_days_list:
            base_price = tariff.get_price_for_period(days)
            if base_price is None:
                continue
            original_price = base_price
            price = base_price

            if promo_group:
                group_discount = promo_group.get_discount_percent('period', days)
                if group_discount > 0:
                    price = int(price * (100 - group_discount) / 100)
            if promo_offer_discount_percent > 0:
                price = price - price * promo_offer_discount_percent // 100

            price = max(1, price)
            combined_discount = int((original_price - price) * 100 / original_price) if original_price != price else 0

            periods.append(
                GiftConfigTariffPeriod(
                    days=days,
                    price_kopeks=price,
                    price_label=settings.format_price(price),
                    original_price_kopeks=original_price if combined_discount > 0 else None,
                    discount_percent=combined_discount if combined_discount > 0 else None,
                )
            )
        if not periods:
            continue
        tariffs.append(
            GiftConfigTariff(
                id=tariff.id,
                name=tariff.name,
                description=tariff.description,
                traffic_limit_gb=tariff.traffic_limit_gb,
                device_limit=tariff.device_limit,
                periods=periods,
            )
        )

    enabled_methods = await get_enabled_methods_for_user(db, user=user)
    payment_methods: list[GiftConfigPaymentMethod] = []
    for method_data in enabled_methods:
        sub_options = None
        raw_options = method_data.get('options')
        if raw_options:
            sub_options = [GiftConfigSubOption(id=opt['id'], name=opt.get('name', opt['id'])) for opt in raw_options]
        payment_methods.append(
            GiftConfigPaymentMethod(
                method_id=method_data['id'],
                display_name=method_data['name'],
                min_amount_kopeks=method_data.get('min_amount_kopeks'),
                max_amount_kopeks=method_data.get('max_amount_kopeks'),
                sub_options=sub_options,
            )
        )

    return GiftConfigResponse(
        is_enabled=True,
        tariffs=tariffs,
        payment_methods=payment_methods,
        balance_kopeks=user.balance_kopeks,
        currency_symbol=getattr(settings, 'CURRENCY_SYMBOL', '\u20bd'),
        promo_group_name=promo_group_name,
        active_discount_percent=promo_offer_discount_percent if promo_offer_discount_percent > 0 else None,
        active_discount_expires_at=(
            getattr(user, 'promo_offer_discount_expires_at', None) if promo_offer_discount_percent > 0 else None
        ),
    )


@router.post('/purchase', response_model=GiftPurchaseResponse)
async def create_gift_purchase(
    body: GiftPurchaseRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    enabled = await _is_gift_enabled(db)
    if not enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Gift feature is not enabled')

    is_limited = await RateLimitCache.is_rate_limited(user.id, 'gift_purchase', limit=5, window=60)
    if is_limited:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Too many requests')

    if getattr(user, 'restriction_subscription', False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Purchases are restricted for this account')

    has_recipient = bool(body.recipient_type and body.recipient_value)
    if has_recipient:
        recipient_value = body.recipient_value or ''
        if body.recipient_type == 'email' and not _EMAIL_RE.match(recipient_value):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid email format')
        if body.recipient_type == 'telegram' and not _TELEGRAM_RE.match(recipient_value):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid Telegram username format')

        if body.recipient_type == 'telegram':
            normalized = recipient_value.lstrip('@').lower()
            if user.username and user.username.lower() == normalized:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot gift to yourself')
        elif body.recipient_type == 'email':
            if user.email and user.email.lower() == recipient_value.lower():
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot gift to yourself')

    tariff = await get_tariff_by_id(db, body.tariff_id)
    has_explicit_gift_tariffs = await _has_explicit_gift_tariffs(db)
    is_allowed_for_gift = bool(tariff and tariff.is_active and (tariff.show_in_gift or not has_explicit_gift_tariffs))
    if not is_allowed_for_gift:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Tariff not found or inactive')

    price_kopeks = tariff.get_price_for_period(body.period_days)
    if price_kopeks is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Price is not configured for this period')

    promo_group = user.get_primary_promo_group() if hasattr(user, 'get_primary_promo_group') else None
    if promo_group is None:
        promo_group = getattr(user, 'promo_group', None)
    if promo_group:
        discount_percent = promo_group.get_discount_percent('period', body.period_days)
        if discount_percent > 0:
            price_kopeks = int(price_kopeks * (100 - discount_percent) / 100)

    promo_offer_discount_percent = get_user_active_promo_discount_percent(user)
    if promo_offer_discount_percent > 0:
        price_kopeks = price_kopeks - price_kopeks * promo_offer_discount_percent // 100
    price_kopeks = max(1, price_kopeks)

    # Lock user row to prevent concurrent promo offer double-spend
    locked_result = await db.execute(
        select(User)
        .options(
            selectinload(User.user_promo_groups).selectinload(UserPromoGroup.promo_group),
            selectinload(User.promo_group),
        )
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    user = locked_result.scalar_one()

    # Apply promo group discount
    promo_group = user.get_primary_promo_group() if hasattr(user, 'get_primary_promo_group') else None
    if promo_group is None:
        promo_group = getattr(user, 'promo_group', None)

    if promo_group:
        discount_percent = promo_group.get_discount_percent('period', body.period_days)
        if discount_percent > 0:
            price_kopeks = int(price_kopeks * (100 - discount_percent) / 100)

    # Apply active promo offer discount (stacks)
    promo_offer_discount_percent = get_user_active_promo_discount_percent(user)
    if promo_offer_discount_percent > 0:
        price_kopeks = price_kopeks - price_kopeks * promo_offer_discount_percent // 100

    # Ensure minimum price of 1 kopek after all discounts
    price_kopeks = max(1, price_kopeks)

    if user.email:
        buyer_contact_type = 'email'
        buyer_contact_value = user.email
    elif user.username:
        buyer_contact_type = 'telegram'
        buyer_contact_value = f'@{user.username}'
    else:
        buyer_contact_type = 'telegram'
        buyer_contact_value = f'id:{user.telegram_id or user.id}'

    if body.payment_mode == 'gateway':
        from app.cabinet.routes.balance import create_topup
        from app.cabinet.schemas.balance import TopUpRequest
        from app.services.payment_service import PaymentService

        gateway_purchase_kwargs: dict = (
            {
                'gift_recipient_type': body.recipient_type,
                'gift_recipient_value': body.recipient_value,
                'gift_message': body.gift_message,
            }
            if has_recipient
            else {'gift_message': body.gift_message}
        )
        try:
            purchase = await create_purchase(
                db=db,
                tariff=tariff,
                period_days=body.period_days,
                amount_kopeks=price_kopeks,
                contact_type=buyer_contact_type,
                contact_value=buyer_contact_value,
                payment_method=body.payment_method,
                is_gift=True,
                source='cabinet',
                buyer_user_id=user.id,
                commit=False,
                **gateway_purchase_kwargs,
            )
        except GuestPurchaseError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        if body.payment_method == 'telegram_stars':
            from aiogram import Bot

            bot = Bot(token=settings.BOT_TOKEN)
            try:
                payment_service = PaymentService(bot=bot)
                payment_result = await payment_service.create_guest_payment(
                    db=db,
                    amount_kopeks=price_kopeks,
                    payment_method='telegram_stars',
                    description=f'Gift: {tariff.name} ({body.period_days}d)',
                    purchase_token=purchase.token,
                    return_url=(settings.CABINET_URL or '').rstrip('/'),
                )
            finally:
                await bot.session.close()

            if payment_result is None or not payment_result.get('payment_url'):
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail='Payment provider is unavailable, please try again later',
                )
            purchase.payment_id = str(payment_result.get('payment_id') or '')
            payment_url = str(payment_result.get('payment_url'))
        else:
            topup = await create_topup(
                TopUpRequest(
                    amount_kopeks=body.topup_amount_kopeks or price_kopeks,
                    payment_method=body.payment_method or '',
                    payment_option=body.payment_option,
                ),
                user=user,
                db=db,
            )
            purchase.payment_id = topup.payment_id
            payment_url = topup.payment_url

        if promo_offer_discount_percent > 0 and getattr(user, 'promo_offer_discount_percent', 0):
            user.promo_offer_discount_percent = 0
            user.promo_offer_discount_source = None
            user.promo_offer_discount_expires_at = None
        await db.commit()
        await db.refresh(purchase)
        return GiftPurchaseResponse(
            status='created',
            purchase_token=purchase.token[:12],
            payment_url=payment_url,
            warning=None,
        )

    if user.balance_kopeks < price_kopeks:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Insufficient balance')

    purchase_kwargs: dict = (
        {
            'gift_recipient_type': body.recipient_type,
            'gift_recipient_value': body.recipient_value,
            'gift_message': body.gift_message,
        }
        if has_recipient
        else {'gift_message': body.gift_message}
    )
    try:
        purchase = await create_purchase(
            db=db,
            tariff=tariff,
            period_days=body.period_days,
            amount_kopeks=price_kopeks,
            contact_type=buyer_contact_type,
            contact_value=buyer_contact_value,
            payment_method='balance',
            is_gift=True,
            source='cabinet',
            buyer_user_id=user.id,
            commit=False,
            **purchase_kwargs,
        )
    except GuestPurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    balance_ok = await subtract_user_balance(
        db,
        user,
        price_kopeks,
        description=f'Gift: {tariff.name} ({body.period_days}d)',
        create_transaction=False,
        consume_promo_offer=promo_offer_discount_percent > 0,
    )
    if not balance_ok:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Insufficient balance')

    tx_description = f'Gift: {tariff.name} ({body.period_days}d)'
    if has_recipient:
        tx_description += f' -> {body.recipient_value}'

    transaction = await create_transaction(
        db,
        user_id=user.id,
        type=TransactionType.GIFT_PAYMENT,
        amount_kopeks=price_kopeks,
        description=tx_description,
        payment_method=PaymentMethod.BALANCE,
        commit=False,
    )

    purchase.status = GuestPurchaseStatus.PAID.value
    purchase.paid_at = datetime.now(UTC)
    await db.commit()

    await emit_transaction_side_effects(
        db,
        transaction,
        amount_kopeks=price_kopeks,
        user_id=user.id,
        type=TransactionType.GIFT_PAYMENT,
        payment_method=PaymentMethod.BALANCE,
        description=tx_description,
    )

    purchase_token = purchase.token
    try:
        await fulfill_purchase(db, purchase_token)
    except Exception:
        logger.exception('Gift purchase fulfillment failed (purchase is paid, user can activate by code)')

    return GiftPurchaseResponse(status='ok', purchase_token=purchase_token[:12], warning=None)


@router.post('/sent/{token}/extend', response_model=GiftExtendResponse)
async def extend_sent_gift(
    token: str,
    body: GiftExtendRequest | None = None,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    enabled = await _is_gift_enabled(db)
    if not enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Gift feature is not enabled')

    is_limited = await RateLimitCache.is_rate_limited(user.id, 'gift_extend', limit=8, window=60)
    if is_limited:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Too many requests')

    result = await db.execute(
        select(GuestPurchase)
        .options(selectinload(GuestPurchase.tariff), selectinload(GuestPurchase.user))
        .where(_gift_token_filter(token), GuestPurchase.is_gift.is_(True))
        .with_for_update()
    )
    purchase = result.scalars().first()
    if purchase is None or purchase.buyer_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Gift purchase not found')

    if purchase.status in (GuestPurchaseStatus.FAILED.value, GuestPurchaseStatus.EXPIRED.value):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Gift is inactive')
    if purchase.status == GuestPurchaseStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Gift is waiting for payment')

    tariff = purchase.tariff
    if tariff is None:
        tariff = await get_tariff_by_id(db, purchase.tariff_id)
    if tariff is None or not tariff.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Gift tariff is unavailable')

    requested_period_days = body.period_days if body else None
    period_days = int(requested_period_days or purchase.period_days or 0)
    if period_days <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Gift period is invalid')

    price_kopeks = tariff.get_price_for_period(period_days)
    if price_kopeks is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Gift tariff price for this period is unavailable',
        )

    promo_group = user.get_primary_promo_group() if hasattr(user, 'get_primary_promo_group') else None
    if promo_group is None:
        promo_group = getattr(user, 'promo_group', None)
    if promo_group:
        discount_percent = promo_group.get_discount_percent('period', period_days)
        if discount_percent > 0:
            price_kopeks = int(price_kopeks * (100 - discount_percent) / 100)

    promo_offer_discount_percent = get_user_active_promo_discount_percent(user)
    if promo_offer_discount_percent > 0:
        price_kopeks = price_kopeks - price_kopeks * promo_offer_discount_percent // 100
    price_kopeks = max(1, int(price_kopeks))

    if user.balance_kopeks < price_kopeks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'INSUFFICIENT_BALANCE',
                'message': 'Insufficient balance',
                'required_amount': int(price_kopeks),
                'balance': int(user.balance_kopeks),
                'missing_amount': int(max(0, price_kopeks - user.balance_kopeks)),
            },
        )

    charged = await subtract_user_balance(
        db,
        user,
        price_kopeks,
        description=f'Gift extension: {tariff.name} ({period_days}d) [{purchase.token[:12]}]',
        create_transaction=False,
        consume_promo_offer=promo_offer_discount_percent > 0,
    )
    if not charged:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Insufficient balance')

    transaction = await create_transaction(
        db,
        user_id=user.id,
        type=TransactionType.GIFT_PAYMENT,
        amount_kopeks=price_kopeks,
        description=f'Gift extension: {tariff.name} ({period_days}d) [{purchase.token[:12]}]',
        payment_method=PaymentMethod.BALANCE,
        commit=False,
    )

    purchase.period_days += period_days

    recipient_user = purchase.user
    recipient_username = f'@{recipient_user.username}' if recipient_user and recipient_user.username else None
    if purchase.status == GuestPurchaseStatus.DELIVERED.value and purchase.user_id:
        recipient_subscription = await get_subscription_by_user_id(db, purchase.user_id)
        if recipient_subscription:
            recipient_subscription = await extend_subscription(db, recipient_subscription, period_days)
        else:
            recipient_subscription = await create_paid_subscription(
                db=db,
                user_id=purchase.user_id,
                duration_days=period_days,
                traffic_limit_gb=tariff.traffic_limit_gb,
                device_limit=tariff.device_limit,
                connected_squads=tariff.allowed_squads or [],
                tariff_id=tariff.id,
            )
        try:
            service = SubscriptionService()
            if getattr(recipient_user, 'remnawave_uuid', None):
                await service.update_remnawave_user(db, recipient_subscription)
            else:
                await service.create_remnawave_user(db, recipient_subscription)
        except Exception:
            logger.exception(
                'Failed to sync remnawave after gift extension',
                purchase_id=purchase.id,
                recipient_user_id=purchase.user_id,
            )

    await db.commit()

    await emit_transaction_side_effects(
        db,
        transaction,
        amount_kopeks=price_kopeks,
        user_id=user.id,
        type=TransactionType.GIFT_PAYMENT,
        payment_method=PaymentMethod.BALANCE,
        description=f'Gift extension: {tariff.name} ({period_days}d) [{purchase.token[:12]}]',
    )

    return GiftExtendResponse(
        status='extended',
        token=purchase.token[:12],
        added_days=period_days,
        total_period_days=purchase.period_days,
        charged_amount_kopeks=price_kopeks,
        charged_amount_label=settings.format_price(price_kopeks),
        recipient_username=recipient_username,
    )


@router.get('/pending', response_model=list[PendingGiftResponse])
async def get_pending_gifts(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    result = await db.execute(
        select(GuestPurchase)
        .options(selectinload(GuestPurchase.tariff))
        .where(
            GuestPurchase.user_id == user.id,
            GuestPurchase.is_gift.is_(True),
            GuestPurchase.status == GuestPurchaseStatus.PENDING_ACTIVATION.value,
        )
        .order_by(GuestPurchase.created_at.desc())
        .limit(100)
    )
    purchases = result.scalars().all()
    return [
        PendingGiftResponse(
            token=p.token[:12],
            tariff_name=p.tariff.name if p.tariff else None,
            period_days=p.period_days,
            gift_message=p.gift_message,
            sender_display=p.contact_value,
            created_at=p.created_at,
        )
        for p in purchases
    ]


@router.get('/purchase/{token}', response_model=GiftPurchaseStatusResponse)
async def get_gift_purchase_status(
    token: str,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    result = await db.execute(
        select(GuestPurchase)
        .options(selectinload(GuestPurchase.tariff))
        .where(_gift_token_filter(token))
        .with_for_update()
    )
    purchase = result.scalars().first()
    if purchase is None or purchase.buyer_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Purchase not found')

    if purchase.status == GuestPurchaseStatus.PENDING.value and purchase.payment_method not in (None, 'balance'):
        return await _finalize_gateway_gift_via_balance(db=db, user=user, purchase=purchase)

    is_code_only = purchase.is_gift and not purchase.gift_recipient_type
    return GiftPurchaseStatusResponse(
        status=purchase.status,
        is_gift=True,
        is_code_only=is_code_only,
        purchase_token=purchase.token[:12] if is_code_only else None,
        recipient_contact_value=purchase.gift_recipient_value,
        gift_message=purchase.gift_message,
        tariff_name=purchase.tariff.name if purchase.tariff else None,
        period_days=purchase.period_days,
        warning=purchase.recipient_warning,
    )


@router.get('/sent', response_model=list[SentGiftResponse])
async def get_sent_gifts(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    result = await db.execute(
        select(GuestPurchase)
        .options(selectinload(GuestPurchase.tariff), selectinload(GuestPurchase.user))
        .where(GuestPurchase.buyer_user_id == user.id, GuestPurchase.is_gift.is_(True))
        .order_by(GuestPurchase.created_at.desc())
        .limit(100)
    )
    purchases = result.scalars().all()
    return [
        SentGiftResponse(
            token=p.token[:12],
            tariff_id=p.tariff_id,
            tariff_name=p.tariff.name if p.tariff else None,
            period_days=p.period_days,
            device_limit=p.tariff.device_limit if p.tariff else 1,
            status=p.status,
            gift_recipient_value=p.gift_recipient_value,
            gift_message=p.gift_message,
            activated_by_username=(f'@{p.user.username}' if p.user and p.user.username else None),
            created_at=p.created_at,
        )
        for p in purchases
    ]


@router.get('/received', response_model=list[ReceivedGiftResponse])
async def get_received_gifts(
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    result = await db.execute(
        select(GuestPurchase)
        .options(selectinload(GuestPurchase.tariff), selectinload(GuestPurchase.buyer))
        .where(GuestPurchase.user_id == user.id, GuestPurchase.is_gift.is_(True))
        .order_by(GuestPurchase.created_at.desc())
        .limit(100)
    )
    purchases = result.scalars().all()
    return [
        ReceivedGiftResponse(
            token=p.token[:12],
            tariff_name=p.tariff.name if p.tariff else None,
            period_days=p.period_days,
            device_limit=p.tariff.device_limit if p.tariff else 1,
            status=p.status,
            sender_display=(f'@{p.buyer.username}' if p.buyer and p.buyer.username else p.contact_value),
            gift_message=p.gift_message,
            created_at=p.created_at,
        )
        for p in purchases
    ]


@router.post('/activate', response_model=ActivateGiftResponse)
async def activate_gift_by_code(
    body: ActivateGiftRequest,
    user: User = Depends(get_current_cabinet_user),
    db: AsyncSession = Depends(get_cabinet_db),
):
    is_limited = await RateLimitCache.is_rate_limited(user.id, 'gift_activate', limit=10, window=60)
    if is_limited:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail='Too many requests')

    code = body.code.strip()
    if code.upper().startswith('GIFT-'):
        code = code[5:]
    if len(code) < 8:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Code too short')

    token_filter = GuestPurchase.token == code if len(code) >= 64 else GuestPurchase.token.startswith(code)
    result = await db.execute(
        select(GuestPurchase)
        .options(selectinload(GuestPurchase.tariff))
        .where(token_filter, GuestPurchase.is_gift.is_(True))
        .with_for_update()
    )
    purchase = result.scalars().first()
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Gift not found')

    if purchase.user_id is not None and purchase.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Gift not found')
    if purchase.buyer_user_id is not None and purchase.buyer_user_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Cannot activate your own gift')

    if purchase.status == GuestPurchaseStatus.DELIVERED.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Gift code already activated')

    activatable = {GuestPurchaseStatus.PENDING_ACTIVATION.value, GuestPurchaseStatus.PAID.value}
    if purchase.status not in activatable:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='This gift cannot be activated')

    if purchase.user_id is None:
        purchase.user_id = user.id
    if purchase.status == GuestPurchaseStatus.PAID.value:
        purchase.status = GuestPurchaseStatus.PENDING_ACTIVATION.value
    await db.flush()

    try:
        await svc_activate(db, purchase.token, skip_notification=False)
    except GuestPurchaseError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    await db.refresh(purchase)
    if purchase.status != GuestPurchaseStatus.DELIVERED.value:
        logger.warning(
            'Gift activation finished without delivered status',
            purchase_id=purchase.id,
            status=purchase.status,
            user_id=user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Gift activation is not completed yet',
        )

    return ActivateGiftResponse(
        status='activated',
        tariff_name=purchase.tariff.name if purchase.tariff else None,
        period_days=purchase.period_days,
    )
