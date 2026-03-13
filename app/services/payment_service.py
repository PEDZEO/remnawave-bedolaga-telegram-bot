"""Агрегирующий сервис, собирающий все платёжные модули."""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from importlib import import_module
from typing import Any, Final

import structlog
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.external.cryptobot import CryptoBotService
from app.external.heleket import HeleketService
from app.external.telegram_stars import TelegramStarsService
from app.services.cloudpayments_service import CloudPaymentsService
from app.services.mulenpay_service import MulenPayService
from app.services.nalogo_service import NaloGoService
from app.services.pal24_service import Pal24Service
from app.services.payment import (
    CryptoBotPaymentMixin,
    HeleketPaymentMixin,
    MulenPayPaymentMixin,
    Pal24PaymentMixin,
    PaymentCommonMixin,
    PlategaPaymentMixin,
    TelegramStarsMixin,
    TributePaymentMixin,
    WataPaymentMixin,
    YooKassaPaymentMixin,
)
from app.services.payment.cloudpayments import CloudPaymentsPaymentMixin
from app.services.payment.freekassa import FreekassaPaymentMixin
from app.services.payment.kassa_ai import KassaAiPaymentMixin
from app.services.platega_service import PlategaService
from app.services.wata_service import WataService
from app.services.yookassa_service import YooKassaService
from app.utils.currency_converter import currency_converter


logger = structlog.get_logger(__name__)


# --- Совместимость: экспортируем функции, которые активно мокаются в тестах ---
async def _call_crud(module_path: str, function_name: str, *args, **kwargs):
    crud_module = import_module(module_path)
    crud_function = getattr(crud_module, function_name)
    return await crud_function(*args, **kwargs)


CrudWrapper = Callable[..., Awaitable[Any]]
CrudFunctionRef = tuple[str, str]

_CRUD_FUNCTIONS: Final[dict[str, CrudFunctionRef]] = {
    'create_yookassa_payment': ('app.database.crud.yookassa', 'create_yookassa_payment'),
    'update_yookassa_payment_status': ('app.database.crud.yookassa', 'update_yookassa_payment_status'),
    'link_yookassa_payment_to_transaction': ('app.database.crud.yookassa', 'link_yookassa_payment_to_transaction'),
    'get_yookassa_payment_by_id': ('app.database.crud.yookassa', 'get_yookassa_payment_by_id'),
    'get_yookassa_payment_by_local_id': ('app.database.crud.yookassa', 'get_yookassa_payment_by_local_id'),
    'create_transaction': ('app.database.crud.transaction', 'create_transaction'),
    'get_transaction_by_external_id': ('app.database.crud.transaction', 'get_transaction_by_external_id'),
    'add_user_balance': ('app.database.crud.user', 'add_user_balance'),
    'get_user_by_id': ('app.database.crud.user', 'get_user_by_id'),
    'get_user_by_telegram_id': ('app.database.crud.user', 'get_user_by_telegram_id'),
    'create_mulenpay_payment': ('app.database.crud.mulenpay', 'create_mulenpay_payment'),
    'get_mulenpay_payment_by_uuid': ('app.database.crud.mulenpay', 'get_mulenpay_payment_by_uuid'),
    'get_mulenpay_payment_by_mulen_id': ('app.database.crud.mulenpay', 'get_mulenpay_payment_by_mulen_id'),
    'get_mulenpay_payment_by_local_id': ('app.database.crud.mulenpay', 'get_mulenpay_payment_by_local_id'),
    'update_mulenpay_payment_status': ('app.database.crud.mulenpay', 'update_mulenpay_payment_status'),
    'update_mulenpay_payment_metadata': ('app.database.crud.mulenpay', 'update_mulenpay_payment_metadata'),
    'link_mulenpay_payment_to_transaction': ('app.database.crud.mulenpay', 'link_mulenpay_payment_to_transaction'),
    'create_pal24_payment': ('app.database.crud.pal24', 'create_pal24_payment'),
    'get_pal24_payment_by_bill_id': ('app.database.crud.pal24', 'get_pal24_payment_by_bill_id'),
    'get_pal24_payment_by_order_id': ('app.database.crud.pal24', 'get_pal24_payment_by_order_id'),
    'get_pal24_payment_by_id': ('app.database.crud.pal24', 'get_pal24_payment_by_id'),
    'update_pal24_payment_status': ('app.database.crud.pal24', 'update_pal24_payment_status'),
    'link_pal24_payment_to_transaction': ('app.database.crud.pal24', 'link_pal24_payment_to_transaction'),
    'create_wata_payment': ('app.database.crud.wata', 'create_wata_payment'),
    'get_wata_payment_by_link_id': ('app.database.crud.wata', 'get_wata_payment_by_link_id'),
    'get_wata_payment_by_id': ('app.database.crud.wata', 'get_wata_payment_by_id'),
    'get_wata_payment_by_order_id': ('app.database.crud.wata', 'get_wata_payment_by_order_id'),
    'update_wata_payment_status': ('app.database.crud.wata', 'update_wata_payment_status'),
    'link_wata_payment_to_transaction': ('app.database.crud.wata', 'link_wata_payment_to_transaction'),
    'create_platega_payment': ('app.database.crud.platega', 'create_platega_payment'),
    'get_platega_payment_by_id': ('app.database.crud.platega', 'get_platega_payment_by_id'),
    'get_platega_payment_by_id_for_update': ('app.database.crud.platega', 'get_platega_payment_by_id_for_update'),
    'get_platega_payment_by_transaction_id': ('app.database.crud.platega', 'get_platega_payment_by_transaction_id'),
    'get_platega_payment_by_correlation_id': ('app.database.crud.platega', 'get_platega_payment_by_correlation_id'),
    'update_platega_payment': ('app.database.crud.platega', 'update_platega_payment'),
    'link_platega_payment_to_transaction': ('app.database.crud.platega', 'link_platega_payment_to_transaction'),
    'create_cryptobot_payment': ('app.database.crud.cryptobot', 'create_cryptobot_payment'),
    'get_cryptobot_payment_by_invoice_id': ('app.database.crud.cryptobot', 'get_cryptobot_payment_by_invoice_id'),
    'update_cryptobot_payment_status': ('app.database.crud.cryptobot', 'update_cryptobot_payment_status'),
    'link_cryptobot_payment_to_transaction': ('app.database.crud.cryptobot', 'link_cryptobot_payment_to_transaction'),
    'create_heleket_payment': ('app.database.crud.heleket', 'create_heleket_payment'),
    'get_heleket_payment_by_uuid': ('app.database.crud.heleket', 'get_heleket_payment_by_uuid'),
    'get_heleket_payment_by_id': ('app.database.crud.heleket', 'get_heleket_payment_by_id'),
    'update_heleket_payment': ('app.database.crud.heleket', 'update_heleket_payment'),
    'link_heleket_payment_to_transaction': ('app.database.crud.heleket', 'link_heleket_payment_to_transaction'),
    'create_cloudpayments_payment': ('app.database.crud.cloudpayments', 'create_cloudpayments_payment'),
    'get_cloudpayments_payment_by_invoice_id': (
        'app.database.crud.cloudpayments',
        'get_cloudpayments_payment_by_invoice_id',
    ),
    'get_cloudpayments_payment_by_id': ('app.database.crud.cloudpayments', 'get_cloudpayments_payment_by_id'),
    'update_cloudpayments_payment': ('app.database.crud.cloudpayments', 'update_cloudpayments_payment'),
}

_GETTER_OVERRIDES: Final[dict[str, str]] = {
    'cryptobot': 'get_cryptobot_payment_by_invoice_id',
    'cloudpayments': 'get_cloudpayments_payment_by_invoice_id',
}


def _make_crud_wrapper(module_path: str, function_name: str) -> CrudWrapper:
    async def _wrapper(*args, **kwargs):
        return await _call_crud(module_path, function_name, *args, **kwargs)

    _wrapper.__name__ = function_name
    _wrapper.__qualname__ = function_name
    _wrapper.__module__ = __name__
    return _wrapper


for _public_name, (_module_path, _function_name) in _CRUD_FUNCTIONS.items():
    globals()[_public_name] = _make_crud_wrapper(_module_path, _function_name)


# Алиас для совместимости с хендлерами
async def get_wata_payment_by_local_id(*args, **kwargs):
    return await get_wata_payment_by_id(*args, **kwargs)


class PaymentService(
    PaymentCommonMixin,
    TelegramStarsMixin,
    YooKassaPaymentMixin,
    TributePaymentMixin,
    CryptoBotPaymentMixin,
    HeleketPaymentMixin,
    MulenPayPaymentMixin,
    Pal24PaymentMixin,
    PlategaPaymentMixin,
    WataPaymentMixin,
    CloudPaymentsPaymentMixin,
    FreekassaPaymentMixin,
    KassaAiPaymentMixin,
):
    """Основной интерфейс платежей, делегирующий работу специализированным mixin-ам."""

    def __init__(self, bot: Bot | None = None) -> None:
        # Бот нужен для отправки уведомлений и создания звёздных инвойсов.
        self.bot = bot
        # Ниже инициализируем службы-обёртки только если соответствующий провайдер включён.
        self.yookassa_service = YooKassaService() if settings.is_yookassa_enabled() else None
        self.stars_service = TelegramStarsService(bot) if bot else None
        self.cryptobot_service = CryptoBotService() if settings.is_cryptobot_enabled() else None
        self.heleket_service = HeleketService() if settings.is_heleket_enabled() else None
        self.mulenpay_service = MulenPayService() if settings.is_mulenpay_enabled() else None
        self.pal24_service = Pal24Service() if settings.is_pal24_enabled() else None
        self.platega_service = PlategaService() if settings.is_platega_enabled() else None
        self.wata_service = WataService() if settings.is_wata_enabled() else None
        self.cloudpayments_service = CloudPaymentsService() if settings.is_cloudpayments_enabled() else None
        self.nalogo_service = NaloGoService() if settings.is_nalogo_enabled() else None

        mulenpay_name = settings.get_mulenpay_display_name()
        logger.debug(
            'PaymentService инициализирован (YooKassa Stars CryptoBot Heleket Pal24 Platega Wata CloudPayments=)',
            yookassa_service=bool(self.yookassa_service),
            stars_service=bool(self.stars_service),
            cryptobot_service=bool(self.cryptobot_service),
            heleket_service=bool(self.heleket_service),
            mulenpay_name=mulenpay_name,
            mulenpay_service=bool(self.mulenpay_service),
            pal24_service=bool(self.pal24_service),
            platega_service=bool(self.platega_service),
            wata_service=bool(self.wata_service),
            cloudpayments_service=bool(self.cloudpayments_service),
        )

    # ------------------------------------------------------------------
    # Guest (landing page) payments
    # ------------------------------------------------------------------
    # Supported providers for guest payments (to be extended per-provider):
    #   - yookassa (card, sbp)
    #   - cryptobot
    #   - heleket
    #   - mulenpay
    #   - pal24
    #   - platega
    #   - wata
    #   - cloudpayments
    #   - freekassa
    #   - kassa_ai
    #   - telegram_stars
    #   - tribute
    # Each provider returns a different result dict; the caller must
    # extract the payment URL from the provider-specific key.
    # ------------------------------------------------------------------

    async def create_guest_payment(
        self,
        db: AsyncSession,
        *,
        amount_kopeks: int,
        payment_method: str,
        description: str,
        purchase_token: str,
        return_url: str,
    ) -> dict[str, Any] | None:
        """Create a payment for a guest (unauthenticated) landing-page purchase.

        Stores ``purchase_token`` in payment metadata so that webhook handlers
        can match the completed payment back to the corresponding
        :class:`GuestPurchase` record.

        Returns a provider-specific dict with at least ``payment_url`` on
        success, or ``None`` when the requested provider is unavailable or
        the creation call fails.
        """
        guest_metadata: dict[str, Any] = {
            'purpose': 'guest_purchase',
            'purchase_token': purchase_token,
            'source': 'landing',
        }

        async def _patch_guest_metadata(local_payment_id: int, model_name: str) -> None:
            """Merge guest_metadata into the local payment record's metadata_json."""
            try:
                crud_module = import_module(f'app.database.crud.{model_name}')
                getter_name = _GETTER_OVERRIDES.get(model_name, f'get_{model_name}_payment_by_id')
                getter = getattr(crud_module, getter_name, None)
                if getter is None:
                    logger.warning(
                        'No getter found for patching guest metadata', model_name=model_name, getter_name=getter_name
                    )
                    return
                payment_record = await getter(db, local_payment_id)
                if payment_record is None:
                    return
                existing_meta = dict(getattr(payment_record, 'metadata_json', None) or {})
                existing_meta.update(guest_metadata)
                payment_record.metadata_json = existing_meta
                await db.commit()
            except Exception as patch_error:
                logger.warning(
                    'Failed to patch guest metadata into payment record',
                    model_name=model_name,
                    local_payment_id=local_payment_id,
                    error=patch_error,
                )

        # --- YooKassa (card / sbp) -------------------------------------------
        if payment_method in ('yookassa', 'yookassa_card', 'yookassa_sbp'):
            if self.yookassa_service is None:
                logger.warning('YooKassa is not enabled, cannot create guest payment')
                return None

            option = 'sbp' if payment_method == 'yookassa_sbp' else 'card'

            if option == 'sbp':
                result = await self.create_yookassa_sbp_payment(
                    db=db,
                    user_id=None,
                    amount_kopeks=amount_kopeks,
                    description=description,
                    metadata=guest_metadata,
                    return_url=return_url,
                )
            else:
                result = await self.create_yookassa_payment(
                    db=db,
                    user_id=None,
                    amount_kopeks=amount_kopeks,
                    description=description,
                    metadata=guest_metadata,
                    return_url=return_url,
                )

            if result:
                return {
                    'payment_url': result.get('confirmation_url'),
                    'payment_id': result.get('yookassa_payment_id'),
                    'provider': 'yookassa',
                }
            return None

        # --- CryptoBot --------------------------------------------------------
        if payment_method == 'cryptobot':
            if self.cryptobot_service is None:
                logger.warning('CryptoBot is not enabled, cannot create guest payment')
                return None

            amount_rubles = amount_kopeks / 100
            try:
                amount_usd = await currency_converter.rub_to_usd(amount_rubles)
            except Exception as conv_error:
                logger.error('Currency conversion failed for CryptoBot guest payment', error=conv_error)
                return None

            # Encode guest metadata into the payload string (CryptoBot uses payload, not metadata dict)
            payload_str = json.dumps(guest_metadata, ensure_ascii=False)

            result = await self.create_cryptobot_payment(
                db=db,
                user_id=None,
                amount_usd=amount_usd,
                asset='USDT',
                description=description,
                payload=payload_str,
            )
            if result:
                # CryptoBot stores guest_metadata in the payload field (no metadata_json column)
                payment_url = result.get('bot_invoice_url') or result.get('mini_app_invoice_url')
                return {
                    'payment_url': payment_url,
                    'payment_id': result.get('invoice_id'),
                    'provider': 'cryptobot',
                }
            return None

        # --- Heleket ----------------------------------------------------------
        if payment_method == 'heleket':
            if self.heleket_service is None:
                logger.warning('Heleket is not enabled, cannot create guest payment')
                return None

            result = await self.create_heleket_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
                return_url=return_url,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'heleket')
                return {
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('uuid'),
                    'provider': 'heleket',
                }
            return None

        # --- MulenPay ---------------------------------------------------------
        if payment_method == 'mulenpay':
            if self.mulenpay_service is None:
                logger.warning('MulenPay is not enabled, cannot create guest payment')
                return None

            result = await self.create_mulenpay_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'mulenpay')
                return {
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('uuid'),
                    'provider': 'mulenpay',
                }
            return None

        # --- Pal24 (PayPalych) ------------------------------------------------
        if payment_method in ('pal24', 'pal24_sbp', 'pal24_card'):
            if self.pal24_service is None:
                logger.warning('Pal24 is not enabled, cannot create guest payment')
                return None

            pal24_method = (
                'sbp' if payment_method == 'pal24_sbp' else ('card' if payment_method == 'pal24_card' else None)
            )

            result = await self.create_pal24_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
                language=settings.DEFAULT_LANGUAGE,
                payment_method=pal24_method,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'pal24')
                return {
                    'payment_url': result.get('payment_url') or result.get('primary_url'),
                    'payment_id': result.get('bill_id'),
                    'provider': 'pal24',
                }
            return None

        # --- Platega ----------------------------------------------------------
        if payment_method.startswith('platega'):
            if self.platega_service is None:
                logger.warning('Platega is not enabled, cannot create guest payment')
                return None

            # Extract method code: "platega_2" -> 2, "platega" -> first active method
            method_code: int | None = None
            if '_' in payment_method:
                suffix = payment_method.split('_', 1)[1]
                try:
                    method_code = int(suffix)
                except ValueError:
                    pass

            if method_code is None:
                active_methods = settings.get_platega_active_methods()
                method_code = active_methods[0] if active_methods else 2

            result = await self.create_platega_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
                language=settings.DEFAULT_LANGUAGE,
                payment_method_code=method_code,
                return_url=return_url,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'platega')
                return {
                    'payment_url': result.get('redirect_url'),
                    'payment_id': result.get('correlation_id'),
                    'provider': 'platega',
                }
            return None

        # --- WATA -------------------------------------------------------------
        if payment_method == 'wata':
            if self.wata_service is None:
                logger.warning('WATA is not enabled, cannot create guest payment')
                return None

            result = await self.create_wata_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
                return_url=return_url,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'wata')
                return {
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('payment_link_id'),
                    'provider': 'wata',
                }
            return None

        # --- CloudPayments ----------------------------------------------------
        if payment_method == 'cloudpayments':
            if self.cloudpayments_service is None:
                logger.warning('CloudPayments is not enabled, cannot create guest payment')
                return None

            result = await self.create_cloudpayments_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
                return_url=return_url,
            )
            if result:
                await _patch_guest_metadata(result['payment_id'], 'cloudpayments')
                return {
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('invoice_id'),
                    'provider': 'cloudpayments',
                }
            return None

        # --- Freekassa --------------------------------------------------------
        if payment_method in ('freekassa', 'freekassa_sbp', 'freekassa_card'):
            if not settings.is_freekassa_enabled():
                logger.warning('Freekassa is not enabled, cannot create guest payment')
                return None

            result = await self.create_freekassa_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
                payment_method=payment_method,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'freekassa')
                return {
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('order_id'),
                    'provider': 'freekassa',
                }
            return None

        # --- KassaAI ----------------------------------------------------------
        if payment_method == 'kassa_ai':
            if not settings.is_kassa_ai_enabled():
                logger.warning('KassaAI is not enabled, cannot create guest payment')
                return None

            result = await self.create_kassa_ai_payment(
                db=db,
                user_id=None,
                amount_kopeks=amount_kopeks,
                description=description,
            )
            if result:
                await _patch_guest_metadata(result['local_payment_id'], 'kassa_ai')
                return {
                    'payment_url': result.get('payment_url'),
                    'payment_id': result.get('order_id'),
                    'provider': 'kassa_ai',
                }
            return None

        # --- Telegram Stars ---------------------------------------------------
        if payment_method == 'telegram_stars':
            if not settings.TELEGRAM_STARS_ENABLED:
                logger.warning('Telegram Stars is not enabled, cannot create guest payment')
                return None

            if self.bot is None:
                logger.warning('Bot instance required for Stars guest payment')
                return None

            from aiogram.types import LabeledPrice

            rate = settings.get_stars_rate()
            if rate <= 0:
                logger.error('TELEGRAM_STARS_RATE_RUB is not positive, cannot create Stars invoice')
                return None

            amount_rubles = amount_kopeks / 100
            stars_amount = max(1, round(amount_rubles / rate))

            payload = f'guest_purchase_{purchase_token}'

            try:
                invoice_url = await self.bot.create_invoice_link(
                    title='Подарочная подписка VPN',
                    description=f'{description} ({stars_amount} ⭐)',
                    payload=payload,
                    provider_token='',
                    currency='XTR',
                    prices=[LabeledPrice(label='Подарочная подписка', amount=stars_amount)],
                )

                logger.info(
                    'Created Stars invoice for guest purchase',
                    stars_amount=stars_amount,
                    purchase_token_prefix=purchase_token[:5],
                )
                return {
                    'payment_url': invoice_url,
                    'payment_id': f'stars_{purchase_token[:12]}',
                    'provider': 'telegram_stars',
                }

            except Exception as stars_error:
                logger.error('Error creating Stars invoice for guest payment', error=stars_error)
                return None

        # --- Unsupported provider ---------------------------------------------
        logger.warning(
            'Guest payment requested for unsupported provider',
            payment_method=payment_method,
            purchase_token_prefix=purchase_token[:5],
        )
        return None
