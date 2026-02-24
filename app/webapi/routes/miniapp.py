from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.crud.discount_offer import (
    get_latest_claimed_offer_for_user,
    get_offer_by_id,
    list_active_discount_offers_for_user,
    mark_offer_claimed,
)
from app.database.crud.promo_group import get_auto_assign_promo_groups
from app.database.crud.promo_offer_template import get_promo_offer_template_by_id
from app.database.crud.rules import get_rules_by_language
from app.database.crud.subscription import (
    create_trial_subscription,
    extend_subscription,
    update_subscription_autopay,
)
from app.database.crud.transaction import (
    create_transaction,
    get_user_total_spent_kopeks,
)
from app.database.crud.user import get_user_by_telegram_id, subtract_user_balance
from app.database.models import (
    Transaction,
    TransactionType,
)
from app.services.faq_service import FaqService
from app.services.maintenance_service import maintenance_service
from app.services.payment_service import PaymentService
from app.services.privacy_policy_service import PrivacyPolicyService
from app.services.promo_offer_service import promo_offer_service
from app.services.promocode_service import PromoCodeService
from app.services.public_offer_service import PublicOfferService
from app.services.remnawave_service import (
    RemnaWaveConfigurationError,
    RemnaWaveService,
)
from app.services.subscription_purchase_service import (
    PurchaseBalanceError,
    PurchaseValidationError,
    purchase_service,
)
from app.services.subscription_renewal_service import (
    SubscriptionRenewalService,
    calculate_missing_amount,
    with_admin_notification_service,
)
from app.services.subscription_service import SubscriptionService
from app.services.trial_activation_service import (
    TrialPaymentChargeFailed,
    TrialPaymentInsufficientFunds,
    charge_trial_activation_if_required,
    preview_trial_activation_charge,
    revert_trial_activation,
    rollback_trial_subscription_activation,
)
from app.services.tribute_service import TributeService
from app.utils.subscription_utils import get_happ_cryptolink_redirect_link
from app.utils.telegram_webapp import (
    TelegramWebAppAuthError,
    parse_webapp_init_data,
)

from ..dependencies import get_db_session
from ..schemas.miniapp import (
    MiniAppAutoPromoGroupLevel,
    MiniAppConnectedServer,
    MiniAppDailySubscriptionToggleRequest,
    MiniAppDailySubscriptionToggleResponse,
    MiniAppDeviceRemovalRequest,
    MiniAppDeviceRemovalResponse,
    MiniAppFaq,
    MiniAppFaqItem,
    MiniAppLegalDocuments,
    MiniAppMaintenanceStatusResponse,
    MiniAppPaymentCreateRequest,
    MiniAppPaymentCreateResponse,
    MiniAppPaymentIntegrationType,
    MiniAppPaymentMethod,
    MiniAppPaymentMethodsRequest,
    MiniAppPaymentMethodsResponse,
    MiniAppPaymentOption,
    MiniAppPaymentStatusRequest,
    MiniAppPaymentStatusResponse,
    MiniAppPaymentStatusResult,
    MiniAppPromoCode,
    MiniAppPromoCodeActivationRequest,
    MiniAppPromoCodeActivationResponse,
    MiniAppPromoGroup,
    MiniAppPromoOfferClaimRequest,
    MiniAppPromoOfferClaimResponse,
    MiniAppRichTextDocument,
    MiniAppSubscriptionAutopayRequest,
    MiniAppSubscriptionAutopayResponse,
    MiniAppSubscriptionDevicesUpdateRequest,
    MiniAppSubscriptionPurchaseOptionsRequest,
    MiniAppSubscriptionPurchaseOptionsResponse,
    MiniAppSubscriptionPurchasePreviewRequest,
    MiniAppSubscriptionPurchasePreviewResponse,
    MiniAppSubscriptionPurchaseRequest,
    MiniAppSubscriptionPurchaseResponse,
    MiniAppSubscriptionRenewalOptionsRequest,
    MiniAppSubscriptionRenewalOptionsResponse,
    MiniAppSubscriptionRenewalRequest,
    MiniAppSubscriptionRenewalResponse,
    MiniAppSubscriptionRequest,
    MiniAppSubscriptionResponse,
    MiniAppSubscriptionServersUpdateRequest,
    MiniAppSubscriptionSettingsRequest,
    MiniAppSubscriptionSettingsResponse,
    MiniAppSubscriptionTrafficUpdateRequest,
    MiniAppSubscriptionTrialRequest,
    MiniAppSubscriptionTrialResponse,
    MiniAppSubscriptionUpdateResponse,
    MiniAppSubscriptionUser,
    MiniAppTariffPurchaseRequest,
    MiniAppTariffPurchaseResponse,
    MiniAppTariffsRequest,
    MiniAppTariffsResponse,
    MiniAppTariffSwitchPreviewResponse,
    MiniAppTariffSwitchRequest,
    MiniAppTariffSwitchResponse,
    MiniAppTrafficTopupRequest,
    MiniAppTrafficTopupResponse,
)
from .miniapp_auth_helpers import authorize_miniapp_user, ensure_paid_subscription
from .miniapp_autopay_helpers import (
    _autopay_response_extras,
    _build_autopay_payload,
    _get_autopay_day_options,
    _normalize_autopay_days,
)
from .miniapp_cryptobot_helpers import compute_cryptobot_limits, get_usd_to_rub_rate
from .miniapp_format_helpers import (
    bytes_to_gb,
    format_gb,
    format_gb_label,
    format_limit_label,
    status_label,
)
from .miniapp_helpers.auth_runtime import resolve_user_from_init_data
from .miniapp_helpers.payment.amount import (
    build_balance_invoice_payload,
    compute_stars_min_amount,
    current_request_timestamp,
    normalize_stars_amount,
)
from .miniapp_helpers.payment.create_cryptobot import (
    create_cryptobot_balance_payment_response,
)
from .miniapp_helpers.payment.create_input import (
    resolve_create_payment_amount,
    resolve_create_payment_method,
)
from .miniapp_helpers.payment.create_yookassa import (
    create_yookassa_balance_payment_response,
    create_yookassa_sbp_balance_payment_response,
)
from .miniapp_helpers.payment.request import (
    build_mulenpay_iframe_config,
)
from .miniapp_helpers.payment_status.dispatcher import resolve_payment_status_entry
from .miniapp_helpers.promo.discount import extract_promo_discounts
from .miniapp_helpers.promo.offer import (
    extract_offer_extra,
    normalize_effect_type,
)
from .miniapp_helpers.promo_models import (
    ActiveOfferContext,
    build_promo_offer_models,
    find_active_test_access_offers,
)
from .miniapp_helpers.referral import build_referral_info
from .miniapp_helpers.runtime import (
    load_devices_info,
    load_subscription_links,
    resolve_connected_servers,
)
from .miniapp_helpers.subscription.common import (
    validate_subscription_id,
)
from .miniapp_helpers.subscription.devices_update import (
    calculate_devices_upgrade_cost,
    charge_devices_upgrade,
    resolve_device_limits,
)
from .miniapp_helpers.subscription.renewal import (
    prepare_subscription_renewal_options,
)
from .miniapp_helpers.subscription.renewal_execute import (
    execute_classic_renewal,
    execute_tariff_renewal,
)
from .miniapp_helpers.subscription.renewal_payment import (
    create_renewal_cryptobot_payment,
)
from .miniapp_helpers.subscription.renewal_submit import (
    build_tariff_renewal_pricing,
    ensure_classic_renewal_period_available,
    ensure_renewal_method_or_balance,
    ensure_renewal_method_supported,
    resolve_renewal_method,
    resolve_renewal_period,
)
from .miniapp_helpers.subscription.servers_update import (
    apply_servers_update_plan,
    build_servers_update_plan,
    resolve_selected_server_order,
    resolve_server_changes,
)
from .miniapp_helpers.subscription.settings import (
    build_subscription_settings,
)
from .miniapp_helpers.subscription.traffic_update import (
    calculate_traffic_upgrade_cost,
    charge_traffic_upgrade,
    ensure_traffic_update_allowed,
    resolve_new_traffic_value,
)
from .miniapp_helpers.subscription.update_finalize import (
    finalize_subscription_update,
)
from .miniapp_helpers.tariff.base import ensure_tariffs_mode_enabled
from .miniapp_helpers.tariff.daily import (
    build_daily_toggle_message,
    ensure_daily_resume_allowed,
    get_daily_tariff_for_subscription,
    sync_daily_resume_if_needed,
    toggle_pause_state,
)
from .miniapp_helpers.tariff.listing import build_tariffs_payload
from .miniapp_helpers.tariff.purchase import (
    build_tariff_purchase_context,
    ensure_tariff_purchase_balance,
)
from .miniapp_helpers.tariff.switch_context import resolve_tariff_switch_context
from .miniapp_helpers.tariff.switch_flow import (
    apply_tariff_switch_to_subscription,
    build_switch_charge_description,
    build_switch_result_message,
    calculate_switch_pricing,
    ensure_switch_balance,
    execute_switch_charge,
    resolve_tariff_squads,
)
from .miniapp_helpers.tariff.topup import (
    build_topup_description,
    calculate_topup_price,
    ensure_topup_balance,
    execute_topup_purchase,
    get_tariff_for_topup,
    validate_topup_package,
)
from .miniapp_helpers.tariff_state import (
    get_current_tariff_model,
    is_trial_available_for_user,
)
from .miniapp_misc_helpers import (
    is_remnawave_configured,
    resolve_display_name,
    serialize_transaction,
)
from .miniapp_purchase_selection_helpers import merge_purchase_selection_from_request
from .miniapp_renewal_message_helpers import (
    build_promo_offer_payload,
    build_renewal_pending_message,
    build_renewal_status_message,
    build_renewal_success_message,
)


logger = structlog.get_logger(__name__)

router = APIRouter()

promo_code_service = PromoCodeService()
renewal_service = SubscriptionRenewalService()


@router.post(
    '/maintenance/status',
    response_model=MiniAppMaintenanceStatusResponse,
)
async def get_maintenance_status(
    payload: MiniAppSubscriptionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppMaintenanceStatusResponse:
    _, _ = await resolve_user_from_init_data(db, payload.init_data)
    status_info = maintenance_service.get_status_info()
    return MiniAppMaintenanceStatusResponse(
        is_active=bool(status_info.get('is_active')),
        message=maintenance_service.get_maintenance_message(),
        reason=status_info.get('reason'),
    )


@router.post(
    '/payments/methods',
    response_model=MiniAppPaymentMethodsResponse,
)
async def get_payment_methods(
    payload: MiniAppPaymentMethodsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPaymentMethodsResponse:
    _, _ = await resolve_user_from_init_data(db, payload.init_data)

    methods: list[MiniAppPaymentMethod] = []

    if settings.TELEGRAM_STARS_ENABLED:
        stars_min_amount = compute_stars_min_amount()
        methods.append(
            MiniAppPaymentMethod(
                id='stars',
                icon='⭐',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=stars_min_amount,
                amount_step_kopeks=stars_min_amount,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_yookassa_enabled():
        if getattr(settings, 'YOOKASSA_SBP_ENABLED', False):
            methods.append(
                MiniAppPaymentMethod(
                    id='yookassa_sbp',
                    icon='🏦',
                    requires_amount=True,
                    currency='RUB',
                    min_amount_kopeks=settings.YOOKASSA_MIN_AMOUNT_KOPEKS,
                    max_amount_kopeks=settings.YOOKASSA_MAX_AMOUNT_KOPEKS,
                    integration_type=MiniAppPaymentIntegrationType.REDIRECT,
                )
            )

        methods.append(
            MiniAppPaymentMethod(
                id='yookassa',
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.YOOKASSA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.YOOKASSA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_mulenpay_enabled():
        mulenpay_iframe_config = build_mulenpay_iframe_config()
        mulenpay_integration = (
            MiniAppPaymentIntegrationType.IFRAME if mulenpay_iframe_config else MiniAppPaymentIntegrationType.REDIRECT
        )
        methods.append(
            MiniAppPaymentMethod(
                id='mulenpay',
                name=settings.get_mulenpay_display_name(),
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.MULENPAY_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.MULENPAY_MAX_AMOUNT_KOPEKS,
                integration_type=mulenpay_integration,
                iframe_config=mulenpay_iframe_config,
            )
        )

    if settings.is_pal24_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='pal24',
                icon='🏦',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.PAL24_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.PAL24_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
                options=[
                    MiniAppPaymentOption(
                        id='sbp',
                        icon='🏦',
                        title_key='topup.method.pal24.option.sbp.title',
                        description_key='topup.method.pal24.option.sbp.description',
                        title='Faster Payments (SBP)',
                        description='Instant SBP transfer with no fees.',
                    ),
                    MiniAppPaymentOption(
                        id='card',
                        icon='💳',
                        title_key='topup.method.pal24.option.card.title',
                        description_key='topup.method.pal24.option.card.description',
                        title='Bank card',
                        description='Pay with a bank card via PayPalych.',
                    ),
                ],
            )
        )

    if settings.is_wata_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='wata',
                icon='🌊',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.WATA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.WATA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_platega_enabled() and settings.get_platega_active_methods():
        platega_methods = settings.get_platega_active_methods()
        definitions = settings.get_platega_method_definitions()
        options: list[MiniAppPaymentOption] = []

        for method_code in platega_methods:
            info = definitions.get(method_code, {})
            options.append(
                MiniAppPaymentOption(
                    id=str(method_code),
                    icon=info.get('icon') or ('🏦' if method_code == 2 else '💳'),
                    title_key=f'topup.method.platega.option.{method_code}.title',
                    description_key=f'topup.method.platega.option.{method_code}.description',
                    title=info.get('title') or info.get('name') or f'Platega {method_code}',
                    description=info.get('description') or info.get('name'),
                )
            )

        methods.append(
            MiniAppPaymentMethod(
                id='platega',
                icon='💳',
                requires_amount=True,
                currency=settings.PLATEGA_CURRENCY,
                min_amount_kopeks=settings.PLATEGA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.PLATEGA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
                options=options,
            )
        )

    if settings.is_cryptobot_enabled():
        rate = await get_usd_to_rub_rate()
        min_amount_kopeks, max_amount_kopeks = compute_cryptobot_limits(rate)
        methods.append(
            MiniAppPaymentMethod(
                id='cryptobot',
                icon='🪙',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=min_amount_kopeks,
                max_amount_kopeks=max_amount_kopeks,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_heleket_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='heleket',
                icon='🪙',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=100 * 100,
                max_amount_kopeks=100_000 * 100,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_cloudpayments_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='cloudpayments',
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.CLOUDPAYMENTS_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.CLOUDPAYMENTS_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.is_freekassa_enabled():
        methods.append(
            MiniAppPaymentMethod(
                id='freekassa',
                icon='💳',
                requires_amount=True,
                currency='RUB',
                min_amount_kopeks=settings.FREEKASSA_MIN_AMOUNT_KOPEKS,
                max_amount_kopeks=settings.FREEKASSA_MAX_AMOUNT_KOPEKS,
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    if settings.TRIBUTE_ENABLED:
        methods.append(
            MiniAppPaymentMethod(
                id='tribute',
                icon='💎',
                requires_amount=False,
                currency='RUB',
                integration_type=MiniAppPaymentIntegrationType.REDIRECT,
            )
        )

    order_map = {
        'stars': 1,
        'yookassa_sbp': 2,
        'yookassa': 3,
        'cloudpayments': 4,
        'freekassa': 5,
        'mulenpay': 6,
        'pal24': 7,
        'platega': 8,
        'wata': 9,
        'cryptobot': 10,
        'heleket': 11,
        'tribute': 12,
    }
    methods.sort(key=lambda item: order_map.get(item.id, 99))

    return MiniAppPaymentMethodsResponse(methods=methods)


@router.post(
    '/payments/create',
    response_model=MiniAppPaymentCreateResponse,
)
async def create_payment_link(
    payload: MiniAppPaymentCreateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPaymentCreateResponse:
    user, _ = await resolve_user_from_init_data(db, payload.init_data)

    method = resolve_create_payment_method(payload.method)
    amount_kopeks = resolve_create_payment_amount(
        amount_rubles=payload.amount_rubles,
        amount_kopeks=payload.amount_kopeks,
    )

    if method == 'stars':
        if not settings.TELEGRAM_STARS_ENABLED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if not settings.BOT_TOKEN:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Bot token is not configured')

        requested_amount_kopeks = amount_kopeks
        try:
            stars_amount, amount_kopeks = normalize_stars_amount(amount_kopeks)
        except ValueError as exc:
            logger.error('Failed to normalize Stars amount', exc=exc)
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Failed to prepare Stars payment',
            ) from exc

        bot = Bot(token=settings.BOT_TOKEN)
        invoice_payload = build_balance_invoice_payload(user.id, amount_kopeks)
        try:
            payment_service = PaymentService(bot)
            invoice_link = await payment_service.create_stars_invoice(
                amount_kopeks=amount_kopeks,
                description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
                payload=invoice_payload,
                stars_amount=stars_amount,
            )
        finally:
            await bot.session.close()

        if not invoice_link:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create invoice')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=invoice_link,
            amount_kopeks=amount_kopeks,
            extra={
                'invoice_payload': invoice_payload,
                'requested_at': current_request_timestamp(),
                'stars_amount': stars_amount,
                'requested_amount_kopeks': requested_amount_kopeks,
            },
        )

    if method == 'yookassa_sbp':
        return await create_yookassa_sbp_balance_payment_response(
            db=db,
            user=user,
            amount_kopeks=amount_kopeks,
        )

    if method == 'yookassa':
        return await create_yookassa_balance_payment_response(
            db=db,
            user=user,
            amount_kopeks=amount_kopeks,
        )

    if method == 'mulenpay':
        if not settings.is_mulenpay_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.MULENPAY_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.MULENPAY_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        payment_service = PaymentService()
        result = await payment_service.create_mulenpay_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language,
        )
        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'payment_id': result.get('mulen_payment_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'platega':
        if not settings.is_platega_enabled() or not settings.get_platega_active_methods():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.PLATEGA_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.PLATEGA_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        active_methods = settings.get_platega_active_methods()
        method_option = payload.payment_option or str(active_methods[0])
        try:
            method_code = int(str(method_option).strip())
        except (TypeError, ValueError):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Invalid Platega payment option')

        if method_code not in active_methods:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Selected Platega method is unavailable')

        payment_service = PaymentService()
        result = await payment_service.create_platega_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language or settings.DEFAULT_LANGUAGE,
            payment_method_code=method_code,
        )

        redirect_url = result.get('redirect_url') if result else None
        if not result or not redirect_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=redirect_url,
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'payment_id': result.get('transaction_id'),
                'correlation_id': result.get('correlation_id'),
                'selected_option': str(method_code),
                'payload': result.get('payload'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'wata':
        if not settings.is_wata_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.WATA_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.WATA_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        payment_service = PaymentService()
        result = await payment_service.create_wata_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language,
        )
        payment_url = result.get('payment_url') if result else None
        if not result or not payment_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=payment_url,
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'payment_link_id': result.get('payment_link_id'),
                'payment_id': result.get('payment_link_id'),
                'status': result.get('status'),
                'order_id': result.get('order_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'pal24':
        if not settings.is_pal24_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')
        if amount_kopeks < settings.PAL24_MIN_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount is below minimum')
        if amount_kopeks > settings.PAL24_MAX_AMOUNT_KOPEKS:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount exceeds maximum')

        option = (payload.payment_option or '').strip().lower()
        if option not in {'card', 'sbp'}:
            option = 'sbp'
        provider_method = 'card' if option == 'card' else 'sbp'

        payment_service = PaymentService()
        result = await payment_service.create_pal24_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language or settings.DEFAULT_LANGUAGE,
            payment_method=provider_method,
        )
        if not result:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        preferred_urls: list[str | None] = []
        if option == 'sbp':
            preferred_urls.append(result.get('sbp_url') or result.get('transfer_url'))
        elif option == 'card':
            preferred_urls.append(result.get('card_url'))
        preferred_urls.extend(
            [
                result.get('link_url'),
                result.get('link_page_url'),
                result.get('payment_url'),
                result.get('transfer_url'),
            ]
        )
        payment_url = next((url for url in preferred_urls if url), None)
        if not payment_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to obtain payment url')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=payment_url,
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'bill_id': result.get('bill_id'),
                'order_id': result.get('order_id'),
                'payment_method': result.get('payment_method') or provider_method,
                'sbp_url': result.get('sbp_url') or result.get('transfer_url'),
                'card_url': result.get('card_url'),
                'link_url': result.get('link_url'),
                'link_page_url': result.get('link_page_url'),
                'transfer_url': result.get('transfer_url'),
                'selected_option': option,
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'cryptobot':
        return await create_cryptobot_balance_payment_response(
            db=db,
            user=user,
            amount_kopeks=amount_kopeks,
        )

    if method == 'heleket':
        if not settings.is_heleket_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

        min_amount_kopeks = 100 * 100
        max_amount_kopeks = 100_000 * 100
        if amount_kopeks < min_amount_kopeks:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount is below minimum ({min_amount_kopeks / 100:.2f} RUB)',
            )
        if amount_kopeks > max_amount_kopeks:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount exceeds maximum ({max_amount_kopeks / 100:.2f} RUB)',
            )

        payment_service = PaymentService()
        result = await payment_service.create_heleket_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            language=user.language or settings.DEFAULT_LANGUAGE,
        )

        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'uuid': result.get('uuid'),
                'order_id': result.get('order_id'),
                'payer_amount': result.get('payer_amount'),
                'payer_currency': result.get('payer_currency'),
                'discount_percent': result.get('discount_percent'),
                'exchange_rate': result.get('exchange_rate'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'cloudpayments':
        if not settings.is_cloudpayments_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

        if amount_kopeks < settings.CLOUDPAYMENTS_MIN_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount is below minimum ({settings.CLOUDPAYMENTS_MIN_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )
        if amount_kopeks > settings.CLOUDPAYMENTS_MAX_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount exceeds maximum ({settings.CLOUDPAYMENTS_MAX_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )

        payment_service = PaymentService()
        result = await payment_service.create_cloudpayments_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            telegram_id=user.telegram_id,
            language=user.language or settings.DEFAULT_LANGUAGE,
        )

        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('payment_id'),
                'invoice_id': result.get('invoice_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'freekassa':
        if not settings.is_freekassa_enabled():
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if amount_kopeks is None or amount_kopeks <= 0:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Amount must be positive')

        if amount_kopeks < settings.FREEKASSA_MIN_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount is below minimum ({settings.FREEKASSA_MIN_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )
        if amount_kopeks > settings.FREEKASSA_MAX_AMOUNT_KOPEKS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=f'Amount exceeds maximum ({settings.FREEKASSA_MAX_AMOUNT_KOPEKS / 100:.2f} RUB)',
            )

        payment_service = PaymentService()
        result = await payment_service.create_freekassa_payment(
            db=db,
            user_id=user.id,
            amount_kopeks=amount_kopeks,
            description=settings.get_balance_payment_description(amount_kopeks, telegram_user_id=user.telegram_id),
            email=getattr(user, 'email', None),
            language=user.language or settings.DEFAULT_LANGUAGE,
        )

        if not result or not result.get('payment_url'):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=result['payment_url'],
            amount_kopeks=amount_kopeks,
            extra={
                'local_payment_id': result.get('local_payment_id'),
                'order_id': result.get('order_id'),
                'requested_at': current_request_timestamp(),
            },
        )

    if method == 'tribute':
        if not settings.TRIBUTE_ENABLED:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Payment method is unavailable')
        if not settings.BOT_TOKEN:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Bot token is not configured')

        bot = Bot(token=settings.BOT_TOKEN)
        try:
            tribute_service = TributeService(bot)
            payment_url = await tribute_service.create_payment_link(
                user_id=user.telegram_id,
                amount_kopeks=amount_kopeks or 0,
                description=settings.get_balance_payment_description(amount_kopeks or 0),
            )
        finally:
            await bot.session.close()

        if not payment_url:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail='Failed to create payment')

        return MiniAppPaymentCreateResponse(
            method=method,
            payment_url=payment_url,
            amount_kopeks=amount_kopeks,
            extra={
                'requested_at': current_request_timestamp(),
            },
        )

    raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Unknown payment method')


@router.post(
    '/payments/status',
    response_model=MiniAppPaymentStatusResponse,
)
async def get_payment_statuses(
    payload: MiniAppPaymentStatusRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPaymentStatusResponse:
    user, _ = await resolve_user_from_init_data(db, payload.init_data)

    entries = payload.payments or []
    if not entries:
        return MiniAppPaymentStatusResponse(results=[])

    payment_service = PaymentService()
    results: list[MiniAppPaymentStatusResult] = []

    for entry in entries:
        result = await resolve_payment_status_entry(
            payment_service=payment_service,
            db=db,
            user=user,
            query=entry,
        )
        if result:
            results.append(result)

    return MiniAppPaymentStatusResponse(results=results)


@router.post('/subscription', response_model=MiniAppSubscriptionResponse)
async def get_subscription_details(
    payload: MiniAppSubscriptionRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionResponse:
    # Check maintenance mode first
    if maintenance_service.is_maintenance_active():
        status_info = maintenance_service.get_status_info()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                'code': 'maintenance',
                'message': maintenance_service.get_maintenance_message() or 'Service is under maintenance',
                'reason': status_info.get('reason'),
            },
        )

    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid Telegram user payload',
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Invalid Telegram user identifier',
        ) from None

    # Check required channel subscription
    if settings.CHANNEL_IS_REQUIRED_SUB:
        from app.services.channel_subscription_service import channel_subscription_service

        channels_with_status = await channel_subscription_service.get_channels_with_status(telegram_id)
        is_subscribed = all(ch['is_subscribed'] for ch in channels_with_status) if channels_with_status else True

        if not is_subscribed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    'code': 'channel_subscription_required',
                    'message': 'Please subscribe to the required channels to continue',
                    'channels': channels_with_status,
                },
            )

    user = await get_user_by_telegram_id(db, telegram_id)
    purchase_url = (settings.MINIAPP_PURCHASE_URL or '').strip()

    if not user:
        detail: dict[str, Any] = {
            'code': 'user_not_found',
            'message': 'User not found. Please register in the bot to continue.',
            'title': 'Registration required',
        }
        if purchase_url:
            detail['purchase_url'] = purchase_url
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )

    subscription = getattr(user, 'subscription', None)
    usage_synced = False

    if subscription and is_remnawave_configured():
        service = SubscriptionService()
        try:
            usage_synced = await service.sync_subscription_usage(db, subscription)
        except Exception as error:  # pragma: no cover - defensive logging
            logger.warning(
                'Failed to sync subscription usage for user', getattr=getattr(user, 'id', 'unknown'), error=error
            )

    if usage_synced:
        try:
            await db.refresh(subscription, attribute_names=['traffic_used_gb', 'updated_at'])
        except Exception as refresh_error:  # pragma: no cover - defensive logging
            logger.debug('Failed to refresh subscription after usage sync', refresh_error=refresh_error)

        try:
            await db.refresh(user)
        except Exception as refresh_error:  # pragma: no cover - defensive logging
            logger.debug('Failed to refresh user after usage sync', refresh_error=refresh_error)
            user = await get_user_by_telegram_id(db, telegram_id)

        subscription = getattr(user, 'subscription', subscription)
    lifetime_used = bytes_to_gb(getattr(user, 'lifetime_used_traffic_bytes', 0))

    transactions_query = (
        select(Transaction).where(Transaction.user_id == user.id).order_by(Transaction.created_at.desc()).limit(10)
    )
    transactions_result = await db.execute(transactions_query)
    transactions = list(transactions_result.scalars().all())

    balance_currency = getattr(user, 'balance_currency', None)
    if isinstance(balance_currency, str):
        balance_currency = balance_currency.upper()

    promo_group = getattr(user, 'promo_group', None)
    total_spent_kopeks = await get_user_total_spent_kopeks(db, user.id)
    auto_assign_groups = await get_auto_assign_promo_groups(db)

    auto_promo_levels: list[MiniAppAutoPromoGroupLevel] = []
    for group in auto_assign_groups:
        threshold = group.auto_assign_total_spent_kopeks or 0
        if threshold <= 0:
            continue

        auto_promo_levels.append(
            MiniAppAutoPromoGroupLevel(
                id=group.id,
                name=group.name,
                threshold_kopeks=threshold,
                threshold_rubles=round(threshold / 100, 2),
                threshold_label=settings.format_price(threshold),
                is_reached=total_spent_kopeks >= threshold,
                is_current=bool(promo_group and promo_group.id == group.id),
                **extract_promo_discounts(group),
            )
        )

    active_discount_percent = 0
    try:
        active_discount_percent = int(getattr(user, 'promo_offer_discount_percent', 0) or 0)
    except (TypeError, ValueError):
        active_discount_percent = 0

    active_discount_expires_at = getattr(user, 'promo_offer_discount_expires_at', None)
    now = datetime.now(UTC)
    if active_discount_expires_at and active_discount_expires_at <= now:
        active_discount_expires_at = None
        active_discount_percent = 0

    available_promo_offers = await list_active_discount_offers_for_user(db, user.id)

    promo_offer_source = getattr(user, 'promo_offer_discount_source', None)
    active_offer_contexts: list[ActiveOfferContext] = []
    if promo_offer_source or active_discount_percent > 0:
        active_discount_offer = await get_latest_claimed_offer_for_user(
            db,
            user.id,
            promo_offer_source,
        )
        if active_discount_offer and active_discount_percent > 0:
            active_offer_contexts.append(
                (
                    active_discount_offer,
                    active_discount_percent,
                    active_discount_expires_at,
                )
            )

    if subscription:
        active_offer_contexts.extend(await find_active_test_access_offers(db, subscription))

    promo_offers = await build_promo_offer_models(
        db,
        available_promo_offers,
        active_offer_contexts,
        user=user,
    )

    content_language_preference = user.language or settings.DEFAULT_LANGUAGE or 'ru'

    def _normalize_language_code(language: str | None) -> str:
        base_language = language or settings.DEFAULT_LANGUAGE or 'ru'
        return base_language.split('-')[0].lower()

    faq_payload: MiniAppFaq | None = None
    requested_faq_language = FaqService.normalize_language(content_language_preference)
    faq_pages = await FaqService.get_pages(
        db,
        requested_faq_language,
        include_inactive=False,
        fallback=True,
    )

    if faq_pages:
        faq_setting = await FaqService.get_setting(
            db,
            requested_faq_language,
            fallback=True,
        )
        is_enabled = bool(faq_setting.is_enabled) if faq_setting else True

        if is_enabled:
            ordered_pages = sorted(
                faq_pages,
                key=lambda page: (
                    (page.display_order or 0),
                    page.id,
                ),
            )
            faq_items: list[MiniAppFaqItem] = []
            for page in ordered_pages:
                raw_content = (page.content or '').strip()
                if not raw_content:
                    continue
                if not re.sub(r'<[^>]+>', '', raw_content).strip():
                    continue
                faq_items.append(
                    MiniAppFaqItem(
                        id=page.id,
                        title=page.title or None,
                        content=page.content or '',
                        display_order=getattr(page, 'display_order', None),
                    )
                )

            if faq_items:
                resolved_language = (
                    faq_setting.language if faq_setting and faq_setting.language else ordered_pages[0].language
                )
                faq_payload = MiniAppFaq(
                    requested_language=requested_faq_language,
                    language=resolved_language or requested_faq_language,
                    is_enabled=is_enabled,
                    total=len(faq_items),
                    items=faq_items,
                )

    legal_documents_payload: MiniAppLegalDocuments | None = None

    requested_offer_language = PublicOfferService.normalize_language(content_language_preference)
    public_offer = await PublicOfferService.get_active_offer(
        db,
        requested_offer_language,
    )
    if public_offer and (public_offer.content or '').strip():
        legal_documents_payload = legal_documents_payload or MiniAppLegalDocuments()
        legal_documents_payload.public_offer = MiniAppRichTextDocument(
            requested_language=requested_offer_language,
            language=public_offer.language,
            title=None,
            is_enabled=bool(public_offer.is_enabled),
            content=public_offer.content or '',
            created_at=public_offer.created_at,
            updated_at=public_offer.updated_at,
        )

    requested_policy_language = PrivacyPolicyService.normalize_language(content_language_preference)
    privacy_policy = await PrivacyPolicyService.get_active_policy(
        db,
        requested_policy_language,
    )
    if privacy_policy and (privacy_policy.content or '').strip():
        legal_documents_payload = legal_documents_payload or MiniAppLegalDocuments()
        legal_documents_payload.privacy_policy = MiniAppRichTextDocument(
            requested_language=requested_policy_language,
            language=privacy_policy.language,
            title=None,
            is_enabled=bool(privacy_policy.is_enabled),
            content=privacy_policy.content or '',
            created_at=privacy_policy.created_at,
            updated_at=privacy_policy.updated_at,
        )

    requested_rules_language = _normalize_language_code(content_language_preference)
    default_rules_language = _normalize_language_code(settings.DEFAULT_LANGUAGE)
    service_rules = await get_rules_by_language(db, requested_rules_language)
    if not service_rules and requested_rules_language != default_rules_language:
        service_rules = await get_rules_by_language(db, default_rules_language)

    if service_rules and (service_rules.content or '').strip():
        legal_documents_payload = legal_documents_payload or MiniAppLegalDocuments()
        legal_documents_payload.service_rules = MiniAppRichTextDocument(
            requested_language=requested_rules_language,
            language=service_rules.language,
            title=getattr(service_rules, 'title', None),
            is_enabled=bool(getattr(service_rules, 'is_active', True)),
            content=service_rules.content or '',
            created_at=getattr(service_rules, 'created_at', None),
            updated_at=getattr(service_rules, 'updated_at', None),
        )

    links_payload: dict[str, Any] = {}
    connected_squads: list[str] = []
    connected_servers: list[MiniAppConnectedServer] = []
    links: list[str] = []
    ss_conf_links: dict[str, str] = {}
    subscription_url: str | None = None
    subscription_crypto_link: str | None = None
    happ_redirect_link: str | None = None
    hide_subscription_link: bool = False
    remnawave_short_uuid: str | None = None
    status_actual = 'missing'
    subscription_status_value = 'none'
    traffic_used_value = 0.0
    traffic_limit_value = 0
    device_limit_value: int | None = settings.DEFAULT_DEVICE_LIMIT or None
    autopay_enabled = False

    if subscription:
        traffic_used_value = format_gb(subscription.traffic_used_gb)
        traffic_limit_value = subscription.traffic_limit_gb or 0
        status_actual = subscription.actual_status
        subscription_status_value = subscription.status
        links_payload = await load_subscription_links(subscription)
        # Флаг скрытия ссылки (скрывается только текст, кнопки работают)
        hide_subscription_link = settings.should_hide_subscription_link()
        subscription_url = links_payload.get('subscription_url') or subscription.subscription_url
        subscription_crypto_link = links_payload.get('happ_crypto_link') or subscription.subscription_crypto_link
        happ_redirect_link = get_happ_cryptolink_redirect_link(subscription_crypto_link)
        connected_squads = list(subscription.connected_squads or [])
        connected_servers = await resolve_connected_servers(db, connected_squads)
        links = links_payload.get('links') or connected_squads
        ss_conf_links = links_payload.get('ss_conf_links') or {}
        remnawave_short_uuid = subscription.remnawave_short_uuid
        device_limit_value = subscription.device_limit
        autopay_enabled = bool(subscription.autopay_enabled)

    autopay_payload = _build_autopay_payload(subscription)
    autopay_days_before = getattr(autopay_payload, 'autopay_days_before', None) if autopay_payload else None
    autopay_days_options = list(getattr(autopay_payload, 'autopay_days_options', []) or []) if autopay_payload else []
    autopay_extras = _autopay_response_extras(
        autopay_enabled,
        autopay_days_before,
        autopay_days_options,
        autopay_payload,
    )

    devices_count, devices = await load_devices_info(user)

    # Загружаем данные суточного тарифа
    is_daily_tariff = False
    is_daily_paused = False
    daily_tariff_name = None
    daily_price_kopeks = None
    daily_price_label = None
    daily_next_charge_at = None

    if subscription and getattr(subscription, 'tariff_id', None):
        tariff = await get_tariff_by_id(db, subscription.tariff_id)
        if tariff and getattr(tariff, 'is_daily', False):
            is_daily_tariff = True
            is_daily_paused = getattr(subscription, 'is_daily_paused', False)
            daily_tariff_name = tariff.name
            daily_price_kopeks = getattr(tariff, 'daily_price_kopeks', 0)
            daily_price_label = settings.format_price(daily_price_kopeks) + '/день' if daily_price_kopeks > 0 else None
            # Оставшееся время подписки (показываем даже при паузе)
            if subscription.end_date:
                daily_next_charge_at = subscription.end_date

    response_user = MiniAppSubscriptionUser(
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=resolve_display_name(
            {
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telegram_id': user.telegram_id,
            }
        ),
        language=user.language,
        status=user.status,
        subscription_status=subscription_status_value,
        subscription_actual_status=status_actual,
        status_label=status_label(status_actual),
        expires_at=getattr(subscription, 'end_date', None),
        device_limit=device_limit_value,
        traffic_used_gb=round(traffic_used_value, 2),
        traffic_used_label=format_gb_label(traffic_used_value),
        traffic_limit_gb=traffic_limit_value,
        traffic_limit_label=format_limit_label(traffic_limit_value),
        lifetime_used_traffic_gb=lifetime_used,
        has_active_subscription=status_actual in {'active', 'trial'},
        promo_offer_discount_percent=active_discount_percent,
        promo_offer_discount_expires_at=active_discount_expires_at,
        promo_offer_discount_source=promo_offer_source,
        is_daily_tariff=is_daily_tariff,
        is_daily_paused=is_daily_paused,
        daily_tariff_name=daily_tariff_name,
        daily_price_kopeks=daily_price_kopeks,
        daily_price_label=daily_price_label,
        daily_next_charge_at=daily_next_charge_at,
    )

    referral_info = await build_referral_info(db, user)

    trial_available = is_trial_available_for_user(user)
    trial_duration_days = settings.TRIAL_DURATION_DAYS if settings.TRIAL_DURATION_DAYS > 0 else None
    trial_price_kopeks = settings.get_trial_activation_price()
    trial_payment_required = settings.is_trial_paid_activation_enabled() and trial_price_kopeks > 0
    trial_price_label = settings.format_price(trial_price_kopeks) if trial_payment_required else None

    subscription_missing_reason = None
    if subscription is None:
        if not trial_available and settings.TRIAL_DURATION_DAYS > 0:
            subscription_missing_reason = 'trial_expired'
        else:
            subscription_missing_reason = 'not_found'

    # Получаем докупки трафика
    traffic_purchases_data = []
    if subscription:
        from sqlalchemy import select as sql_select

        from app.database.models import TrafficPurchase

        now = datetime.now(UTC)
        purchases_query = (
            sql_select(TrafficPurchase)
            .where(TrafficPurchase.subscription_id == subscription.id)
            .where(TrafficPurchase.expires_at > now)
            .order_by(TrafficPurchase.expires_at.asc())
        )
        purchases_result = await db.execute(purchases_query)
        purchases = purchases_result.scalars().all()

        for purchase in purchases:
            time_remaining = purchase.expires_at - now
            days_remaining = max(0, int(time_remaining.total_seconds() / 86400))
            total_duration_seconds = (purchase.expires_at - purchase.created_at).total_seconds()
            elapsed_seconds = (now - purchase.created_at).total_seconds()
            progress_percent = min(
                100.0, max(0.0, (elapsed_seconds / total_duration_seconds * 100) if total_duration_seconds > 0 else 0)
            )

            traffic_purchases_data.append(
                {
                    'id': purchase.id,
                    'traffic_gb': purchase.traffic_gb,
                    'expires_at': purchase.expires_at,
                    'created_at': purchase.created_at,
                    'days_remaining': days_remaining,
                    'progress_percent': round(progress_percent, 1),
                }
            )

    return MiniAppSubscriptionResponse(
        traffic_purchases=traffic_purchases_data,
        subscription_id=getattr(subscription, 'id', None),
        remnawave_short_uuid=remnawave_short_uuid,
        user=response_user,
        subscription_url=subscription_url,
        hide_subscription_link=hide_subscription_link,
        subscription_crypto_link=subscription_crypto_link,
        subscription_purchase_url=purchase_url or None,
        links=links,
        ss_conf_links=ss_conf_links,
        connected_squads=connected_squads,
        connected_servers=connected_servers,
        connected_devices_count=devices_count,
        connected_devices=devices,
        happ=links_payload.get('happ') if subscription else None,
        happ_link=links_payload.get('happ_link') if subscription else None,
        happ_crypto_link=subscription_crypto_link,  # Используем уже вычисленное значение с fallback
        happ_cryptolink_redirect_link=happ_redirect_link,
        happ_cryptolink_redirect_template=settings.get_happ_cryptolink_redirect_template(),
        balance_kopeks=user.balance_kopeks,
        balance_rubles=round(user.balance_rubles, 2),
        balance_currency=balance_currency,
        transactions=[serialize_transaction(tx) for tx in transactions],
        promo_offers=promo_offers,
        promo_group=(
            MiniAppPromoGroup(
                id=promo_group.id,
                name=promo_group.name,
                **extract_promo_discounts(promo_group),
            )
            if promo_group
            else None
        ),
        auto_assign_promo_groups=auto_promo_levels,
        total_spent_kopeks=total_spent_kopeks,
        total_spent_rubles=round(total_spent_kopeks / 100, 2),
        total_spent_label=settings.format_price(total_spent_kopeks),
        subscription_type=('trial' if subscription and subscription.is_trial else ('paid' if subscription else 'none')),
        autopay_enabled=autopay_enabled,
        autopay_days_before=autopay_days_before,
        autopay_days_options=autopay_days_options,
        autopay=autopay_payload,
        autopay_settings=autopay_payload,
        branding=settings.get_miniapp_branding(),
        faq=faq_payload,
        legal_documents=legal_documents_payload,
        referral=referral_info,
        subscription_missing=subscription is None,
        subscription_missing_reason=subscription_missing_reason,
        trial_available=trial_available,
        trial_duration_days=trial_duration_days,
        trial_status='available' if trial_available else 'unavailable',
        trial_payment_required=trial_payment_required,
        trial_price_kopeks=trial_price_kopeks if trial_payment_required else None,
        trial_price_label=trial_price_label,
        sales_mode=settings.get_sales_mode(),
        current_tariff=await get_current_tariff_model(db, subscription, user) if subscription else None,
        **autopay_extras,
    )


@router.post(
    '/subscription/autopay',
    response_model=MiniAppSubscriptionAutopayResponse,
)
async def update_subscription_autopay_endpoint(
    payload: MiniAppSubscriptionAutopayRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionAutopayResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(user)
    validate_subscription_id(payload.subscription_id, subscription)

    # Суточные подписки имеют свой механизм продления (DailySubscriptionService),
    # глобальный autopay для них запрещён
    target_enabled = bool(payload.enabled) if payload.enabled is not None else bool(subscription.autopay_enabled)
    if target_enabled:
        try:
            await db.refresh(subscription, ['tariff'])
        except Exception:
            pass
        if subscription.tariff and getattr(subscription.tariff, 'is_daily', False):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'autopay_not_available_for_daily',
                    'message': 'Autopay is not available for daily subscriptions',
                },
            )

    requested_days = payload.days_before
    normalized_days = _normalize_autopay_days(requested_days)
    current_days = _normalize_autopay_days(getattr(subscription, 'autopay_days_before', None))
    if normalized_days is None:
        normalized_days = current_days

    options = _get_autopay_day_options(subscription)
    default_day = _normalize_autopay_days(getattr(settings, 'DEFAULT_AUTOPAY_DAYS_BEFORE', None))
    if default_day is None and options:
        default_day = options[0]

    if target_enabled and normalized_days is None:
        if default_day is None:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={
                    'code': 'autopay_no_days',
                    'message': 'Auto-pay day selection is temporarily unavailable',
                },
            )
        normalized_days = default_day

    if normalized_days is None:
        normalized_days = default_day or (options[0] if options else 1)

    if bool(subscription.autopay_enabled) == target_enabled and current_days == normalized_days:
        autopay_payload = _build_autopay_payload(subscription)
        autopay_days_before = getattr(autopay_payload, 'autopay_days_before', None) if autopay_payload else None
        autopay_days_options = (
            list(getattr(autopay_payload, 'autopay_days_options', []) or []) if autopay_payload else options
        )
        extras = _autopay_response_extras(
            target_enabled,
            autopay_days_before,
            autopay_days_options,
            autopay_payload,
        )
        return MiniAppSubscriptionAutopayResponse(
            subscription_id=subscription.id,
            autopay_enabled=target_enabled,
            autopay_days_before=autopay_days_before,
            autopay_days_options=autopay_days_options,
            autopay=autopay_payload,
            autopay_settings=autopay_payload,
            **extras,
        )

    updated_subscription = await update_subscription_autopay(
        db,
        subscription,
        target_enabled,
        normalized_days,
    )

    autopay_payload = _build_autopay_payload(updated_subscription)
    autopay_days_before = getattr(autopay_payload, 'autopay_days_before', None) if autopay_payload else None
    autopay_days_options = (
        list(getattr(autopay_payload, 'autopay_days_options', []) or [])
        if autopay_payload
        else _get_autopay_day_options(updated_subscription)
    )
    extras = _autopay_response_extras(
        bool(updated_subscription.autopay_enabled),
        autopay_days_before,
        autopay_days_options,
        autopay_payload,
    )

    return MiniAppSubscriptionAutopayResponse(
        subscription_id=updated_subscription.id,
        autopay_enabled=bool(updated_subscription.autopay_enabled),
        autopay_days_before=autopay_days_before,
        autopay_days_options=autopay_days_options,
        autopay=autopay_payload,
        autopay_settings=autopay_payload,
        **extras,
    )


@router.post(
    '/subscription/trial',
    response_model=MiniAppSubscriptionTrialResponse,
)
async def activate_subscription_trial_endpoint(
    payload: MiniAppSubscriptionTrialRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionTrialResponse:
    user = await authorize_miniapp_user(payload.init_data, db)

    existing_subscription = getattr(user, 'subscription', None)
    if existing_subscription is not None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': 'subscription_exists',
                'message': 'Subscription is already active',
            },
        )

    if not is_trial_available_for_user(user):
        error_code = 'trial_unavailable'
        if getattr(user, 'has_had_paid_subscription', False):
            error_code = 'trial_expired'
        elif settings.TRIAL_DURATION_DAYS <= 0:
            error_code = 'trial_disabled'
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={
                'code': error_code,
                'message': 'Trial is not available for this user',
            },
        )

    try:
        preview_trial_activation_charge(user)
    except TrialPaymentInsufficientFunds as error:
        missing = error.missing_amount
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': 'Not enough funds to activate the trial',
                'missing_amount_kopeks': missing,
                'required_amount_kopeks': error.required_amount,
                'balance_kopeks': error.balance_amount,
            },
        ) from error
    forced_devices = None
    if not settings.is_devices_selection_enabled():
        forced_devices = settings.get_disabled_mode_device_limit()

    # Получаем параметры триала для режима тарифов
    trial_traffic_limit = None
    trial_device_limit = forced_devices
    trial_squads = None
    tariff_id_for_trial = None
    trial_duration = None  # None = использовать TRIAL_DURATION_DAYS

    if settings.is_tariffs_mode():
        try:
            from app.database.crud.tariff import get_tariff_by_id, get_trial_tariff

            trial_tariff = await get_trial_tariff(db)

            if not trial_tariff:
                trial_tariff_id = settings.get_trial_tariff_id()
                if trial_tariff_id > 0:
                    trial_tariff = await get_tariff_by_id(db, trial_tariff_id)
                    if trial_tariff and not trial_tariff.is_active:
                        trial_tariff = None

            if trial_tariff:
                trial_traffic_limit = trial_tariff.traffic_limit_gb
                trial_device_limit = trial_tariff.device_limit
                trial_squads = trial_tariff.allowed_squads or []
                tariff_id_for_trial = trial_tariff.id
                tariff_trial_days = getattr(trial_tariff, 'trial_duration_days', None)
                if tariff_trial_days:
                    trial_duration = tariff_trial_days
                logger.info('Miniapp: используем триальный тариф', trial_tariff_name=trial_tariff.name)
        except Exception as e:
            logger.error('Ошибка получения триального тарифа', error=e)

    try:
        subscription = await create_trial_subscription(
            db,
            user.id,
            duration_days=trial_duration,
            device_limit=trial_device_limit,
            traffic_limit_gb=trial_traffic_limit,
            connected_squads=trial_squads,
            tariff_id=tariff_id_for_trial,
        )
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error('Failed to activate trial subscription for user', user_id=user.id, error=error)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'code': 'trial_activation_failed',
                'message': 'Failed to activate trial subscription',
            },
        ) from error

    charged_amount = 0
    try:
        charged_amount = await charge_trial_activation_if_required(db, user)
    except TrialPaymentInsufficientFunds as error:
        rollback_success = await rollback_trial_subscription_activation(db, subscription)
        await db.refresh(user)
        if not rollback_success:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after charge error',
                },
            ) from error

        logger.error('Balance check failed after trial creation for user', user_id=user.id, error=error)
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                'code': 'insufficient_funds',
                'message': 'Not enough funds to activate the trial',
                'missing_amount_kopeks': error.missing_amount,
                'required_amount_kopeks': error.required_amount,
                'balance_kopeks': error.balance_amount,
            },
        ) from error
    except TrialPaymentChargeFailed as error:
        rollback_success = await rollback_trial_subscription_activation(db, subscription)
        await db.refresh(user)
        if not rollback_success:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after charge error',
                },
            ) from error

        logger.error(
            'Failed to charge balance for trial activation after subscription creation',
            subscription_id=subscription.id,
            error=error,
        )
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                'code': 'charge_failed',
                'message': 'Failed to charge balance for trial activation',
            },
        ) from error

    await db.refresh(user)
    await db.refresh(subscription)

    subscription_service = SubscriptionService()
    try:
        await subscription_service.create_remnawave_user(db, subscription)
    except RemnaWaveConfigurationError as error:  # pragma: no cover - configuration issues
        logger.error('RemnaWave update skipped due to configuration error', error=error)
        revert_result = await revert_trial_activation(
            db,
            user,
            subscription,
            charged_amount,
            refund_description='Возврат оплаты за активацию триала в мини-приложении',
        )
        if not revert_result.subscription_rolled_back:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after RemnaWave error',
                },
            ) from error
        if charged_amount > 0 and not revert_result.refunded:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_refund_failed',
                    'message': 'Failed to refund trial activation charge after RemnaWave error',
                },
            ) from error

        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'remnawave_configuration_error',
                'message': 'Trial activation failed due to RemnaWave configuration. Charge refunded.',
            },
        ) from error
    except Exception as error:  # pragma: no cover - defensive logging
        logger.error(
            'Failed to create RemnaWave user for trial subscription', subscription_id=subscription.id, error=error
        )
        revert_result = await revert_trial_activation(
            db,
            user,
            subscription,
            charged_amount,
            refund_description='Возврат оплаты за активацию триала в мини-приложении',
        )
        if not revert_result.subscription_rolled_back:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_rollback_failed',
                    'message': 'Failed to revert trial activation after RemnaWave error',
                },
            ) from error
        if charged_amount > 0 and not revert_result.refunded:
            raise HTTPException(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    'code': 'trial_refund_failed',
                    'message': 'Failed to refund trial activation charge after RemnaWave error',
                },
            ) from error

        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'remnawave_provisioning_failed',
                'message': 'Trial activation failed due to RemnaWave provisioning. Charge refunded.',
            },
        ) from error

    await db.refresh(subscription)

    duration_days: int | None = None
    if subscription.start_date and subscription.end_date:
        try:
            duration_days = max(
                0,
                (subscription.end_date.date() - subscription.start_date.date()).days,
            )
        except Exception:  # pragma: no cover - defensive fallback
            duration_days = None

    if not duration_days and settings.TRIAL_DURATION_DAYS > 0:
        duration_days = settings.TRIAL_DURATION_DAYS

    language_code = _normalize_language_code(user)
    charged_amount_label = settings.format_price(charged_amount) if charged_amount > 0 else None
    if language_code in {'ru', 'fa'}:
        if duration_days:
            message = f'Триал активирован на {duration_days} дн. Приятного пользования!'
        else:
            message = 'Триал активирован. Приятного пользования!'
    elif duration_days:
        message = f'Trial activated for {duration_days} days. Enjoy!'
    else:
        message = 'Trial activated successfully. Enjoy!'

    if charged_amount_label:
        if language_code in {'ru', 'fa'}:
            message = f'{message}\n\n💳 С вашего баланса списано {charged_amount_label}.'
        else:
            message = f'{message}\n\n💳 {charged_amount_label} has been deducted from your balance.'

    await with_admin_notification_service(
        lambda service: service.send_trial_activation_notification(
            db,
            user,
            subscription,
            charged_amount_kopeks=charged_amount,
        )
    )

    return MiniAppSubscriptionTrialResponse(
        message=message,
        subscription_id=getattr(subscription, 'id', None),
        trial_status='activated',
        trial_duration_days=duration_days,
        charged_amount_kopeks=charged_amount if charged_amount > 0 else None,
        charged_amount_label=charged_amount_label,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )


@router.post(
    '/promo-codes/activate',
    response_model=MiniAppPromoCodeActivationResponse,
)
async def activate_promo_code(
    payload: MiniAppPromoCodeActivationRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPromoCodeActivationResponse:
    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    code = (payload.code or '').strip().upper()
    if not code:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid', 'message': 'Promo code must not be empty'},
        )

    result = await promo_code_service.activate_promocode(db, user.id, code)
    if result.get('success'):
        promocode_data = result.get('promocode') or {}

        try:
            balance_bonus = int(promocode_data.get('balance_bonus_kopeks') or 0)
        except (TypeError, ValueError):
            balance_bonus = 0

        try:
            subscription_days = int(promocode_data.get('subscription_days') or 0)
        except (TypeError, ValueError):
            subscription_days = 0

        promo_payload = MiniAppPromoCode(
            code=str(promocode_data.get('code') or code),
            type=promocode_data.get('type'),
            balance_bonus_kopeks=balance_bonus,
            subscription_days=subscription_days,
            max_uses=promocode_data.get('max_uses'),
            current_uses=promocode_data.get('current_uses'),
            valid_until=promocode_data.get('valid_until'),
        )

        return MiniAppPromoCodeActivationResponse(
            success=True,
            description=result.get('description'),
            promocode=promo_payload,
        )

    error_code = str(result.get('error') or 'generic')
    status_map = {
        'user_not_found': status.HTTP_404_NOT_FOUND,
        'not_found': status.HTTP_404_NOT_FOUND,
        'expired': status.HTTP_410_GONE,
        'used': status.HTTP_409_CONFLICT,
        'already_used_by_user': status.HTTP_409_CONFLICT,
        'server_error': status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    message_map = {
        'invalid': 'Promo code must not be empty',
        'not_found': 'Promo code not found',
        'expired': 'Promo code expired',
        'used': 'Promo code already used',
        'already_used_by_user': 'Promo code already used by this user',
        'user_not_found': 'User not found',
        'server_error': 'Failed to activate promo code',
    }

    http_status = status_map.get(error_code, status.HTTP_400_BAD_REQUEST)
    message = message_map.get(error_code, 'Unable to activate promo code')

    raise HTTPException(
        http_status,
        detail={'code': error_code, 'message': message},
    )


@router.post(
    '/promo-offers/{offer_id}/claim',
    response_model=MiniAppPromoOfferClaimResponse,
)
async def claim_promo_offer(
    offer_id: int,
    payload: MiniAppPromoOfferClaimRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppPromoOfferClaimResponse:
    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    offer = await get_offer_by_id(db, offer_id)
    if not offer or offer.user_id != user.id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'offer_not_found', 'message': 'Offer not found'},
        )

    now = datetime.now(UTC)
    if offer.claimed_at is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={'code': 'already_claimed', 'message': 'Offer already claimed'},
        )

    if not offer.is_active or offer.expires_at <= now:
        offer.is_active = False
        await db.commit()
        raise HTTPException(
            status.HTTP_410_GONE,
            detail={'code': 'offer_expired', 'message': 'Offer expired'},
        )

    effect_type = normalize_effect_type(getattr(offer, 'effect_type', None))

    if effect_type == 'test_access':
        success, newly_added, expires_at, error_code = await promo_offer_service.grant_test_access(
            db,
            user,
            offer,
        )

        if not success:
            code = error_code or 'claim_failed'
            message_map = {
                'subscription_missing': 'Active subscription required',
                'squads_missing': 'No squads configured for test access',
                'already_connected': 'Servers already connected',
                'remnawave_sync_failed': 'Failed to apply servers',
            }
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail={'code': code, 'message': message_map.get(code, 'Unable to activate offer')},
            )

        await mark_offer_claimed(
            db,
            offer,
            details={
                'context': 'test_access_claim',
                'new_squads': newly_added,
                'expires_at': expires_at.isoformat() if expires_at else None,
            },
        )

        return MiniAppPromoOfferClaimResponse(success=True, code='test_access_claimed')

    discount_percent = int(getattr(offer, 'discount_percent', 0) or 0)
    if discount_percent <= 0:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_discount', 'message': 'Offer does not contain discount'},
        )

    user.promo_offer_discount_percent = discount_percent
    user.promo_offer_discount_source = offer.notification_type
    user.updated_at = now

    extra_data = extract_offer_extra(offer)
    raw_duration = extra_data.get('active_discount_hours')
    template_id = extra_data.get('template_id')

    if raw_duration in (None, '') and template_id:
        try:
            template = await get_promo_offer_template_by_id(db, int(template_id))
        except (TypeError, ValueError):
            template = None
        if template and template.active_discount_hours:
            raw_duration = template.active_discount_hours
    else:
        template = None

    try:
        duration_hours = int(raw_duration) if raw_duration is not None else None
    except (TypeError, ValueError):
        duration_hours = None

    if duration_hours and duration_hours > 0:
        discount_expires_at = now + timedelta(hours=duration_hours)
    else:
        discount_expires_at = None

    user.promo_offer_discount_expires_at = discount_expires_at

    await mark_offer_claimed(
        db,
        offer,
        details={
            'context': 'discount_claim',
            'discount_percent': discount_percent,
            'discount_expires_at': discount_expires_at.isoformat() if discount_expires_at else None,
        },
    )
    await db.refresh(user)

    return MiniAppPromoOfferClaimResponse(success=True, code='discount_claimed')


@router.post(
    '/devices/remove',
    response_model=MiniAppDeviceRemovalResponse,
)
async def remove_connected_device(
    payload: MiniAppDeviceRemovalRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppDeviceRemovalResponse:
    try:
        webapp_data = parse_webapp_init_data(payload.init_data, settings.BOT_TOKEN)
    except TelegramWebAppAuthError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={'code': 'unauthorized', 'message': str(error)},
        ) from error

    telegram_user = webapp_data.get('user')
    if not isinstance(telegram_user, dict) or 'id' not in telegram_user:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user payload'},
        )

    try:
        telegram_id = int(telegram_user['id'])
    except (TypeError, ValueError):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_user', 'message': 'Invalid Telegram user identifier'},
        ) from None

    user = await get_user_by_telegram_id(db, telegram_id)
    if not user:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail={'code': 'user_not_found', 'message': 'User not found'},
        )

    remnawave_uuid = getattr(user, 'remnawave_uuid', None)
    if not remnawave_uuid:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail={'code': 'remnawave_unavailable', 'message': 'RemnaWave user is not linked'},
        )

    hwid = (payload.hwid or '').strip()
    if not hwid:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': 'invalid_hwid', 'message': 'Device identifier is required'},
        )

    service = RemnaWaveService()
    if not service.is_configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'code': 'service_unavailable', 'message': 'Device management is temporarily unavailable'},
        )

    try:
        async with service.get_api_client() as api:
            success = await api.remove_device(remnawave_uuid, hwid)
    except RemnaWaveConfigurationError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={'code': 'service_unavailable', 'message': str(error)},
        ) from error
    except Exception as error:  # pragma: no cover - defensive
        logger.warning('Failed to remove device for user', hwid=hwid, telegram_id=telegram_id, error=error)
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={'code': 'remnawave_error', 'message': 'Failed to remove device'},
        ) from error

    if not success:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            detail={'code': 'remnawave_error', 'message': 'Failed to remove device'},
        )

    return MiniAppDeviceRemovalResponse(success=True)


@router.post(
    '/subscription/renewal/options',
    response_model=MiniAppSubscriptionRenewalOptionsResponse,
)
async def get_subscription_renewal_options_endpoint(
    payload: MiniAppSubscriptionRenewalOptionsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionRenewalOptionsResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial', 'expired'},
    )
    validate_subscription_id(payload.subscription_id, subscription)

    periods, pricing_map, default_period_id = await prepare_subscription_renewal_options(
        db,
        user,
        subscription,
        renewal_service=renewal_service,
        logger=logger,
    )

    balance_kopeks = getattr(user, 'balance_kopeks', 0)
    currency = (getattr(user, 'balance_currency', None) or 'RUB').upper()

    promo_group = getattr(user, 'promo_group', None)
    promo_group_model = (
        MiniAppPromoGroup(
            id=promo_group.id,
            name=promo_group.name,
            **extract_promo_discounts(promo_group),
        )
        if promo_group
        else None
    )

    promo_offer_payload = build_promo_offer_payload(user)

    missing_amount = None
    if default_period_id and default_period_id in pricing_map:
        selected_pricing = pricing_map[default_period_id]
        final_total = selected_pricing.get('final_total')
        if isinstance(final_total, int) and balance_kopeks < final_total:
            missing_amount = final_total - balance_kopeks

    renewal_autopay_payload = _build_autopay_payload(subscription)
    renewal_autopay_days_before = (
        getattr(renewal_autopay_payload, 'autopay_days_before', None) if renewal_autopay_payload else None
    )
    renewal_autopay_days_options = (
        list(getattr(renewal_autopay_payload, 'autopay_days_options', []) or []) if renewal_autopay_payload else []
    )
    renewal_autopay_extras = _autopay_response_extras(
        bool(subscription.autopay_enabled),
        renewal_autopay_days_before,
        renewal_autopay_days_options,
        renewal_autopay_payload,
    )

    return MiniAppSubscriptionRenewalOptionsResponse(
        subscription_id=subscription.id,
        currency=currency,
        balance_kopeks=balance_kopeks,
        balance_label=settings.format_price(balance_kopeks),
        promo_group=promo_group_model,
        promo_offer=promo_offer_payload,
        periods=periods,
        default_period_id=default_period_id,
        missing_amount_kopeks=missing_amount,
        status_message=build_renewal_status_message(user),
        autopay_enabled=bool(subscription.autopay_enabled),
        autopay_days_before=renewal_autopay_days_before,
        autopay_days_options=renewal_autopay_days_options,
        autopay=renewal_autopay_payload,
        autopay_settings=renewal_autopay_payload,
        is_trial=bool(getattr(subscription, 'is_trial', False)),
        sales_mode=settings.get_sales_mode(),
        **renewal_autopay_extras,
    )


@router.post(
    '/subscription/renewal',
    response_model=MiniAppSubscriptionRenewalResponse,
)
async def submit_subscription_renewal_endpoint(
    payload: MiniAppSubscriptionRenewalRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionRenewalResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial', 'expired'},
    )
    validate_subscription_id(payload.subscription_id, subscription)

    period_days = resolve_renewal_period(payload.period_days, payload.period_id)
    tariff_pricing = await build_tariff_renewal_pricing(
        db,
        user,
        subscription,
        period_days,
    )
    if not tariff_pricing:
        ensure_classic_renewal_period_available(period_days)

    method = resolve_renewal_method(payload.method)

    # Для тарифного режима используем упрощённый расчёт
    if tariff_pricing:
        final_total = tariff_pricing['final_total']
        pricing = tariff_pricing
    else:
        try:
            pricing_model = await renewal_service.calculate_pricing(
                db,
                user,
                subscription,
                period_days,
            )
        except HTTPException:
            raise
        except Exception as error:
            logger.error(
                'Failed to calculate renewal pricing for subscription (period)',
                subscription_id=subscription.id,
                period_days=period_days,
                error=error,
            )
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                detail={'code': 'pricing_failed', 'message': 'Failed to calculate renewal pricing'},
            ) from error

        pricing = pricing_model.to_payload()
        final_total = int(pricing_model.final_total)
    balance_kopeks = getattr(user, 'balance_kopeks', 0)
    missing_amount = calculate_missing_amount(balance_kopeks, final_total)
    description = f'Продление подписки на {period_days} дней'

    if missing_amount <= 0:
        if tariff_pricing:
            updated_subscription = await execute_tariff_renewal(
                db,
                user,
                subscription,
                period_days=period_days,
                final_total=final_total,
                description=description,
                logger=logger,
            )
            new_end_date = updated_subscription.end_date
            lang = getattr(user, 'language', settings.DEFAULT_LANGUAGE)
            if lang == 'ru':
                message = f'Подписка продлена до {new_end_date.strftime("%d.%m.%Y")}'
            else:
                message = f'Subscription extended until {new_end_date.strftime("%Y-%m-%d")}'

            return MiniAppSubscriptionRenewalResponse(
                message=message,
                balance_kopeks=user.balance_kopeks,
                balance_label=settings.format_price(user.balance_kopeks),
                subscription_id=updated_subscription.id,
                renewed_until=new_end_date,
            )
        result = await execute_classic_renewal(
            db,
            renewal_service,
            user,
            subscription,
            pricing_model,
            description=description,
            logger=logger,
        )

        updated_subscription = result.subscription
        message = build_renewal_success_message(
            user,
            updated_subscription,
            result.total_amount_kopeks,
            pricing_model.promo_discount_value,
        )

        return MiniAppSubscriptionRenewalResponse(
            message=message,
            balance_kopeks=user.balance_kopeks,
            balance_label=settings.format_price(user.balance_kopeks),
            subscription_id=updated_subscription.id,
            renewed_until=updated_subscription.end_date,
        )

    supported_methods = {'cryptobot'}
    ensure_renewal_method_or_balance(
        method=method,
        final_total=final_total,
        balance_kopeks=balance_kopeks,
    )
    ensure_renewal_method_supported(method, supported_methods)

    if method == 'cryptobot':
        payment_data = await create_renewal_cryptobot_payment(
            db=db,
            user=user,
            subscription=subscription,
            period_days=period_days,
            final_total=final_total,
            missing_amount=missing_amount,
            description=description,
            pricing_snapshot=pricing,
        )

        message = build_renewal_pending_message(user, missing_amount, method)

        return MiniAppSubscriptionRenewalResponse(
            success=False,
            message=message,
            balance_kopeks=user.balance_kopeks,
            balance_label=settings.format_price(user.balance_kopeks),
            subscription_id=subscription.id,
            requires_payment=True,
            payment_method=method,
            payment_url=payment_data['payment_url'],
            payment_amount_kopeks=missing_amount,
            payment_id=payment_data['payment_id'],
            invoice_id=payment_data['invoice_id'],
            payment_payload=payment_data['payment_payload'],
            payment_extra=payment_data['payment_extra'],
        )

    raise HTTPException(
        status.HTTP_400_BAD_REQUEST,
        detail={'code': 'unsupported_method', 'message': 'Payment method is not supported for renewal'},
    )


@router.post(
    '/subscription/purchase/options',
    response_model=MiniAppSubscriptionPurchaseOptionsResponse,
)
async def get_subscription_purchase_options_endpoint(
    payload: MiniAppSubscriptionPurchaseOptionsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionPurchaseOptionsResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    context = await purchase_service.build_options(db, user)

    data_payload = dict(context.payload)
    data_payload.setdefault('currency', context.currency)
    data_payload.setdefault('balance_kopeks', context.balance_kopeks)
    data_payload.setdefault('balanceKopeks', context.balance_kopeks)
    data_payload.setdefault('balance_label', settings.format_price(context.balance_kopeks))
    data_payload.setdefault('balanceLabel', settings.format_price(context.balance_kopeks))

    return MiniAppSubscriptionPurchaseOptionsResponse(
        currency=context.currency,
        balance_kopeks=context.balance_kopeks,
        balance_label=settings.format_price(context.balance_kopeks),
        subscription_id=data_payload.get('subscription_id') or data_payload.get('subscriptionId'),
        data=data_payload,
    )


@router.post(
    '/subscription/purchase/preview',
    response_model=MiniAppSubscriptionPurchasePreviewResponse,
)
async def subscription_purchase_preview_endpoint(
    payload: MiniAppSubscriptionPurchasePreviewRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionPurchasePreviewResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    context = await purchase_service.build_options(db, user)

    selection_payload = merge_purchase_selection_from_request(payload)
    try:
        selection = purchase_service.parse_selection(context, selection_payload)
    except PurchaseValidationError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': error.code, 'message': str(error)},
        ) from error

    pricing = await purchase_service.calculate_pricing(db, context, selection)
    preview_payload = purchase_service.build_preview_payload(context, pricing)

    balance_label = settings.format_price(getattr(user, 'balance_kopeks', 0))

    return MiniAppSubscriptionPurchasePreviewResponse(
        preview=preview_payload,
        balance_kopeks=user.balance_kopeks,
        balance_label=balance_label,
    )


@router.post(
    '/subscription/purchase',
    response_model=MiniAppSubscriptionPurchaseResponse,
)
async def subscription_purchase_endpoint(
    payload: MiniAppSubscriptionPurchaseRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionPurchaseResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    context = await purchase_service.build_options(db, user)

    selection_payload = merge_purchase_selection_from_request(payload)
    try:
        selection = purchase_service.parse_selection(context, selection_payload)
    except PurchaseValidationError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': error.code, 'message': str(error)},
        ) from error

    pricing = await purchase_service.calculate_pricing(db, context, selection)

    try:
        result = await purchase_service.submit_purchase(db, context, pricing)
    except PurchaseBalanceError as error:
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            detail={'code': 'insufficient_funds', 'message': str(error)},
        ) from error
    except PurchaseValidationError as error:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail={'code': error.code, 'message': str(error)},
        ) from error

    await db.refresh(user)

    subscription = result.get('subscription')
    transaction = result.get('transaction')
    was_trial_conversion = bool(result.get('was_trial_conversion'))
    period_days = getattr(getattr(pricing, 'selection', None), 'period', None)
    period_days = getattr(period_days, 'days', None) if period_days else None

    if subscription is not None:
        try:
            await db.refresh(subscription)
        except Exception:  # pragma: no cover - defensive refresh safeguard
            pass

    if subscription and transaction and period_days:
        await with_admin_notification_service(
            lambda service: service.send_subscription_purchase_notification(
                db,
                user,
                subscription,
                transaction,
                period_days,
                was_trial_conversion=was_trial_conversion,
            )
        )

    balance_label = settings.format_price(getattr(user, 'balance_kopeks', 0))

    return MiniAppSubscriptionPurchaseResponse(
        message=result.get('message'),
        balance_kopeks=user.balance_kopeks,
        balance_label=balance_label,
        subscription_id=getattr(subscription, 'id', None),
    )


@router.post(
    '/subscription/settings',
    response_model=MiniAppSubscriptionSettingsResponse,
)
async def get_subscription_settings_endpoint(
    payload: MiniAppSubscriptionSettingsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionSettingsResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    validate_subscription_id(payload.subscription_id, subscription)

    settings_payload = await build_subscription_settings(db, user, subscription)

    return MiniAppSubscriptionSettingsResponse(settings=settings_payload)


@router.post(
    '/subscription/servers',
    response_model=MiniAppSubscriptionUpdateResponse,
)
async def update_subscription_servers_endpoint(
    payload: MiniAppSubscriptionServersUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionUpdateResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    validate_subscription_id(payload.subscription_id, subscription)
    old_servers = list(getattr(subscription, 'connected_squads', []) or [])

    selected_order = resolve_selected_server_order(payload)
    _, added, removed = resolve_server_changes(subscription, selected_order)

    if not added and not removed:
        return MiniAppSubscriptionUpdateResponse(
            success=True,
            message='No changes',
        )

    plan = await build_servers_update_plan(
        db,
        user,
        subscription,
        selected_order=selected_order,
        added=added,
        removed=removed,
    )
    total_cost = int(plan['total_cost'])
    await apply_servers_update_plan(
        db,
        user,
        subscription,
        selected_order=selected_order,
        added=added,
        total_cost=total_cost,
        charged_months=int(plan['charged_months']),
        catalog=plan['catalog'],
        added_server_ids=plan['added_server_ids'],
        added_server_prices=plan['added_server_prices'],
        removed_server_ids=plan['removed_server_ids'],
        logger=logger,
    )
    await finalize_subscription_update(
        db,
        user,
        subscription,
        change_type='servers',
        old_value=old_servers,
        new_value=subscription.connected_squads or [],
        price_paid=max(total_cost, 0),
        with_admin_notification_service=with_admin_notification_service,
    )

    return MiniAppSubscriptionUpdateResponse(success=True)


@router.post(
    '/subscription/traffic',
    response_model=MiniAppSubscriptionUpdateResponse,
)
async def update_subscription_traffic_endpoint(
    payload: MiniAppSubscriptionTrafficUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionUpdateResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    validate_subscription_id(payload.subscription_id, subscription)
    old_traffic = subscription.traffic_limit_gb

    new_traffic = resolve_new_traffic_value(payload)

    if new_traffic == subscription.traffic_limit_gb:
        return MiniAppSubscriptionUpdateResponse(success=True, message='No changes')

    ensure_traffic_update_allowed(new_traffic)
    total_price_difference, months_remaining = calculate_traffic_upgrade_cost(
        user,
        subscription,
        new_traffic,
    )
    await charge_traffic_upgrade(
        db,
        user,
        subscription,
        new_traffic=new_traffic,
        total_price_difference=total_price_difference,
        months_remaining=months_remaining,
    )

    subscription.traffic_limit_gb = new_traffic
    await finalize_subscription_update(
        db,
        user,
        subscription,
        change_type='traffic',
        old_value=old_traffic,
        new_value=subscription.traffic_limit_gb,
        price_paid=max(total_price_difference, 0),
        with_admin_notification_service=with_admin_notification_service,
    )

    return MiniAppSubscriptionUpdateResponse(success=True)


@router.post(
    '/subscription/devices',
    response_model=MiniAppSubscriptionUpdateResponse,
)
async def update_subscription_devices_endpoint(
    payload: MiniAppSubscriptionDevicesUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppSubscriptionUpdateResponse:
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(
        user,
        allowed_statuses={'active', 'trial'},
    )
    validate_subscription_id(payload.subscription_id, subscription)

    current_devices, new_devices = resolve_device_limits(payload, subscription)
    old_devices = current_devices

    if new_devices == current_devices:
        return MiniAppSubscriptionUpdateResponse(success=True, message='No changes')

    price_to_charge, charged_months = calculate_devices_upgrade_cost(
        user,
        subscription,
        current_devices=current_devices,
        new_devices=new_devices,
    )
    await charge_devices_upgrade(
        db,
        user,
        current_devices=current_devices,
        new_devices=new_devices,
        price_to_charge=price_to_charge,
        charged_months=charged_months,
        subscription_end_date=subscription.end_date,
    )

    subscription.device_limit = new_devices
    await finalize_subscription_update(
        db,
        user,
        subscription,
        change_type='devices',
        old_value=old_devices,
        new_value=subscription.device_limit,
        price_paid=max(price_to_charge, 0),
        with_admin_notification_service=with_admin_notification_service,
    )

    return MiniAppSubscriptionUpdateResponse(success=True)


# =============================================================================
# Тарифы для режима продаж "Тарифы"
# =============================================================================


@router.post('/subscription/tariffs', response_model=MiniAppTariffsResponse)
async def get_tariffs_endpoint(
    payload: MiniAppTariffsRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppTariffsResponse:
    """Возвращает список доступных тарифов для пользователя."""
    user = await authorize_miniapp_user(payload.init_data, db)

    ensure_tariffs_mode_enabled(message='Tariffs mode is not enabled')
    tariff_models, current_tariff_model, promo_group_model = await build_tariffs_payload(db, user)

    return MiniAppTariffsResponse(
        success=True,
        sales_mode='tariffs',
        tariffs=tariff_models,
        current_tariff=current_tariff_model,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
        promo_group=promo_group_model,
    )


@router.post('/subscription/tariff/purchase', response_model=MiniAppTariffPurchaseResponse)
async def purchase_tariff_endpoint(
    payload: MiniAppTariffPurchaseRequest,
    db: AsyncSession = Depends(get_db_session),
) -> MiniAppTariffPurchaseResponse:
    """Покупка или смена тарифа."""
    user = await authorize_miniapp_user(payload.init_data, db)
    purchase_context = await build_tariff_purchase_context(
        db,
        user,
        payload.tariff_id,
        payload.period_days,
    )
    tariff = purchase_context.tariff
    price_kopeks = purchase_context.price_kopeks
    period_days = purchase_context.period_days
    is_daily_tariff = purchase_context.is_daily_tariff
    ensure_tariff_purchase_balance(user, price_kopeks)

    subscription = getattr(user, 'subscription', None)

    # Списываем баланс
    description = purchase_context.description
    success = await subtract_user_balance(db, user, price_kopeks, description)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                'code': 'balance_charge_failed',
                'message': 'Failed to charge balance',
            },
        )

    # Создаём транзакцию
    await create_transaction(
        db=db,
        user_id=user.id,
        type=TransactionType.SUBSCRIPTION_PAYMENT,
        amount_kopeks=price_kopeks,
        description=description,
    )

    squads = await resolve_tariff_squads(db, tariff)

    if subscription:
        # Смена/продление тарифа
        subscription = await extend_subscription(
            db=db,
            subscription=subscription,
            days=period_days,
            tariff_id=tariff.id,
            traffic_limit_gb=tariff.traffic_limit_gb,
            device_limit=tariff.device_limit,
            connected_squads=squads,
        )
    else:
        # Создание новой подписки
        from app.database.crud.subscription import create_paid_subscription

        subscription = await create_paid_subscription(
            db=db,
            user_id=user.id,
            duration_days=period_days,
            traffic_limit_gb=tariff.traffic_limit_gb,
            device_limit=tariff.device_limit,
            connected_squads=squads,
            tariff_id=tariff.id,
        )

    # Инициализация daily полей при покупке суточного тарифа
    is_daily_tariff = getattr(tariff, 'is_daily', False)
    if is_daily_tariff:
        subscription.is_daily_paused = False
        subscription.last_daily_charge_at = datetime.now(UTC)
        # Для суточного тарифа end_date = сейчас + 1 день (первый день уже оплачен)
        subscription.end_date = datetime.now(UTC) + timedelta(days=1)
        await db.commit()
        await db.refresh(subscription)

    # Синхронизируем с RemnaWave
    # При покупке тарифа ВСЕГДА сбрасываем трафик в панели
    service = SubscriptionService()
    await service.update_remnawave_user(
        db,
        subscription,
        reset_traffic=True,
        reset_reason='покупка тарифа (miniapp)',
    )

    # Сохраняем корзину для автопродления
    try:
        from app.services.user_cart_service import user_cart_service

        cart_data = {
            'cart_mode': 'extend',
            'subscription_id': subscription.id,
            'period_days': period_days,
            'total_price': price_kopeks,
            'tariff_id': tariff.id,
            'description': f'Продление тарифа {tariff.name} на {period_days} дней',
        }
        await user_cart_service.save_user_cart(user.id, cart_data)
        user_id_display = user.telegram_id or user.email or f'#{user.id}'
        logger.info(
            'Корзина тарифа сохранена для автопродления (miniapp) пользователя', user_id_display=user_id_display
        )
    except Exception as e:
        logger.error('Ошибка сохранения корзины тарифа (miniapp)', error=e)

    await db.refresh(user)

    return MiniAppTariffPurchaseResponse(
        success=True,
        message=f"Тариф '{tariff.name}' успешно активирован",
        subscription_id=subscription.id,
        tariff_id=tariff.id,
        tariff_name=tariff.name,
        new_end_date=subscription.end_date,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )


@router.post('/subscription/tariff/switch/preview')
async def preview_tariff_switch_endpoint(
    payload: MiniAppTariffSwitchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Предпросмотр переключения тарифа - показывает стоимость."""

    user = await authorize_miniapp_user(payload.init_data, db)

    ensure_tariffs_mode_enabled(message='Tariffs mode is not enabled')

    context = await resolve_tariff_switch_context(
        db,
        user,
        payload.tariff_id,
        unavailable_message='Tariff not available for your promo group',
    )
    current_tariff = context.current_tariff
    new_tariff = context.new_tariff
    promo_group = context.promo_group
    remaining_days = context.remaining_days

    switch_pricing = calculate_switch_pricing(
        current_tariff,
        new_tariff,
        remaining_days,
        promo_group,
        user,
    )
    upgrade_cost = switch_pricing.upgrade_cost
    is_upgrade = switch_pricing.is_upgrade

    balance = user.balance_kopeks or 0
    has_enough = balance >= upgrade_cost
    missing = max(0, upgrade_cost - balance) if not has_enough else 0

    return MiniAppTariffSwitchPreviewResponse(
        can_switch=has_enough,
        current_tariff_id=current_tariff.id if current_tariff else None,
        current_tariff_name=current_tariff.name if current_tariff else None,
        new_tariff_id=new_tariff.id,
        new_tariff_name=new_tariff.name,
        remaining_days=remaining_days,
        upgrade_cost_kopeks=upgrade_cost,
        upgrade_cost_label=settings.format_price(upgrade_cost) if upgrade_cost > 0 else 'Бесплатно',
        balance_kopeks=balance,
        balance_label=settings.format_price(balance),
        has_enough_balance=has_enough,
        missing_amount_kopeks=missing,
        missing_amount_label=settings.format_price(missing) if missing > 0 else '',
        is_upgrade=is_upgrade,
        message=None,
    )


@router.post('/subscription/tariff/switch')
async def switch_tariff_endpoint(
    payload: MiniAppTariffSwitchRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Переключение тарифа без изменения даты окончания."""
    user = await authorize_miniapp_user(payload.init_data, db)

    ensure_tariffs_mode_enabled(message='Tariffs mode is not enabled')

    context = await resolve_tariff_switch_context(
        db,
        user,
        payload.tariff_id,
        unavailable_message='Tariff not available',
    )
    subscription = context.subscription
    current_tariff = context.current_tariff
    new_tariff = context.new_tariff
    promo_group = context.promo_group
    remaining_days = context.remaining_days

    switch_pricing = calculate_switch_pricing(
        current_tariff,
        new_tariff,
        remaining_days,
        promo_group,
        user,
    )
    upgrade_cost = switch_pricing.upgrade_cost
    new_period_days = switch_pricing.new_period_days
    switching_from_daily = switch_pricing.switching_from_daily

    # Списываем доплату если апгрейд
    if upgrade_cost > 0:
        ensure_switch_balance(user, upgrade_cost)
        description = build_switch_charge_description(
            new_tariff_name=new_tariff.name,
            switching_from_daily=switching_from_daily,
            new_period_days=new_period_days,
            remaining_days=remaining_days,
        )
        await execute_switch_charge(
            db=db,
            user=user,
            upgrade_cost=upgrade_cost,
            description=description,
        )

    await apply_tariff_switch_to_subscription(
        db,
        subscription,
        current_tariff,
        new_tariff,
        new_period_days=new_period_days,
        logger=logger,
    )

    await db.commit()
    await db.refresh(subscription)
    await db.refresh(user)

    # Синхронизируем с RemnaWave
    try:
        service = SubscriptionService()
        await service.update_remnawave_user(db, subscription)
    except Exception as e:
        logger.error('Ошибка синхронизации с RemnaWave при смене тарифа', error=e)

    lang = getattr(user, 'language', settings.DEFAULT_LANGUAGE)
    message = build_switch_result_message(lang, new_tariff.name, upgrade_cost)

    return MiniAppTariffSwitchResponse(
        success=True,
        message=message,
        tariff_id=new_tariff.id,
        tariff_name=new_tariff.name,
        charged_kopeks=upgrade_cost,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )


@router.post('/subscription/traffic-topup')
async def purchase_traffic_topup_endpoint(
    payload: MiniAppTrafficTopupRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Докупка трафика для подписки."""
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = ensure_paid_subscription(user)
    validate_subscription_id(payload.subscription_id, subscription)

    ensure_tariffs_mode_enabled(message='Traffic top-up is only available in tariffs mode')

    tariff = await get_tariff_for_topup(db, subscription)
    base_price_kopeks = validate_topup_package(subscription, tariff, payload.gb)
    final_price, traffic_discount_percent = calculate_topup_price(
        user,
        subscription,
        base_price_kopeks,
    )

    ensure_topup_balance(user, final_price)
    traffic_description = build_topup_description(payload.gb, traffic_discount_percent)
    await execute_topup_purchase(
        db,
        user,
        subscription,
        package_gb=payload.gb,
        final_price=final_price,
        description=traffic_description,
        logger=logger,
    )

    await db.refresh(user)
    await db.refresh(subscription)

    return MiniAppTrafficTopupResponse(
        success=True,
        message=f'Добавлено {payload.gb} ГБ трафика',
        new_traffic_limit_gb=subscription.traffic_limit_gb,
        new_balance_kopeks=user.balance_kopeks,
        charged_kopeks=final_price,
    )


@router.post('/subscription/daily/toggle-pause')
async def toggle_daily_subscription_pause_endpoint(
    payload: MiniAppDailySubscriptionToggleRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Переключает паузу/активацию суточной подписки."""
    user = await authorize_miniapp_user(payload.init_data, db)
    subscription = user.subscription

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={'code': 'no_subscription', 'message': 'No subscription found'},
        )

    tariff = await get_daily_tariff_for_subscription(db, subscription)
    new_paused_state = toggle_pause_state(subscription)

    # Если снимаем с паузы, нужно проверить баланс для активации
    if not new_paused_state:
        was_reactivated = ensure_daily_resume_allowed(user, subscription, tariff)
        if was_reactivated:
            logger.info('✅ Суточная подписка восстановлена из DISABLED в ACTIVE', subscription_id=subscription.id)

    await db.commit()
    await db.refresh(subscription)
    await db.refresh(user)

    await sync_daily_resume_if_needed(user, is_paused=new_paused_state, logger=logger)

    lang = getattr(user, 'language', settings.DEFAULT_LANGUAGE)
    message = build_daily_toggle_message(lang, new_paused_state)

    return MiniAppDailySubscriptionToggleResponse(
        success=True,
        message=message,
        is_paused=new_paused_state,
        balance_kopeks=user.balance_kopeks,
        balance_label=settings.format_price(user.balance_kopeks),
    )
