"""Агрегирующий сервис, собирающий все платёжные модули."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from importlib import import_module
from typing import Any, Final

import structlog
from aiogram import Bot

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
from app.utils.currency_converter import currency_converter  # noqa: F401


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
    'get_cloudpayments_payment_by_invoice_id': ('app.database.crud.cloudpayments', 'get_cloudpayments_payment_by_invoice_id'),
    'get_cloudpayments_payment_by_id': ('app.database.crud.cloudpayments', 'get_cloudpayments_payment_by_id'),
    'update_cloudpayments_payment': ('app.database.crud.cloudpayments', 'update_cloudpayments_payment'),
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
