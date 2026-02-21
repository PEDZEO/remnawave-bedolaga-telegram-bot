from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.models import User
from app.services.subscription_auto_purchase_service import auto_purchase_saved_cart_after_topup
from app.services.subscription_purchase_service import (
    PurchaseDevicesConfig,
    PurchaseOptionsContext,
    PurchasePeriodConfig,
    PurchasePricingResult,
    PurchaseSelection,
    PurchaseServersConfig,
    PurchaseTrafficConfig,
)


class DummyTexts:
    def t(self, key: str, default: str):
        return default

    def format_price(self, value: int) -> str:
        return f'{value / 100:.0f} ₽'


pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _mock_recent_transactions(monkeypatch):
    async def get_user_transactions_stub(*args, **kwargs):
        return []

    monkeypatch.setattr(
        'app.database.crud.transaction.get_user_transactions',
        get_user_transactions_stub,
    )


async def test_auto_purchase_saved_cart_after_topup_success(monkeypatch):
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)

    user = SimpleNamespace(
        id=42,
        telegram_id=4242,
        balance_kopeks=200_000,
        language='ru',
        subscription=None,
        get_primary_promo_group=lambda: None,
    )

    cart_data = {
        'period_days': 30,
        'countries': ['ru'],
        'traffic_gb': 0,
        'devices': 1,
    }

    traffic_config = PurchaseTrafficConfig(
        selectable=False,
        mode='fixed',
        options=[],
        default_value=0,
        current_value=0,
    )
    servers_config = PurchaseServersConfig(
        options=[],
        min_selectable=0,
        max_selectable=0,
        default_selection=['ru'],
    )
    devices_config = PurchaseDevicesConfig(
        minimum=1,
        maximum=5,
        default=1,
        current=1,
        price_per_device=0,
        discounted_price_per_device=0,
        price_label='0 ₽',
    )

    period_config = PurchasePeriodConfig(
        id='days:30',
        days=30,
        months=1,
        label='30 дней',
        base_price=100_000,
        base_price_label='1000 ₽',
        base_price_original=100_000,
        base_price_original_label=None,
        discount_percent=0,
        per_month_price=100_000,
        per_month_price_label='1000 ₽',
        traffic=traffic_config,
        servers=servers_config,
        devices=devices_config,
    )

    context = PurchaseOptionsContext(
        user=user,
        subscription=None,
        currency='RUB',
        balance_kopeks=user.balance_kopeks,
        periods=[period_config],
        default_period=period_config,
        period_map={'days:30': period_config},
        server_uuid_to_id={'ru': 1},
        payload={},
    )

    base_pricing = PurchasePricingResult(
        selection=PurchaseSelection(
            period=period_config,
            traffic_value=0,
            servers=['ru'],
            devices=1,
        ),
        server_ids=[1],
        server_prices_for_period=[100_000],
        base_original_total=100_000,
        discounted_total=100_000,
        promo_discount_value=0,
        promo_discount_percent=0,
        final_total=100_000,
        months=1,
        details={'servers_individual_prices': [100_000]},
    )

    class DummyMiniAppService:
        async def build_options(self, db, user):
            return context

        async def calculate_pricing(self, db, ctx, selection):
            return PurchasePricingResult(
                selection=selection,
                server_ids=base_pricing.server_ids,
                server_prices_for_period=base_pricing.server_prices_for_period,
                base_original_total=base_pricing.base_original_total,
                discounted_total=base_pricing.discounted_total,
                promo_discount_value=base_pricing.promo_discount_value,
                promo_discount_percent=base_pricing.promo_discount_percent,
                final_total=base_pricing.final_total,
                months=base_pricing.months,
                details=base_pricing.details,
            )

        async def submit_purchase(self, db, prepared_context, pricing):
            return {
                'subscription': SimpleNamespace(),
                'transaction': SimpleNamespace(),
                'was_trial_conversion': False,
                'message': '🎉 Subscription purchased',
            }

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.MiniAppSubscriptionPurchaseService',
        DummyMiniAppService,
    )
    async def get_user_cart_stub(_user_id):
        return cart_data

    deleted_cart_ids: list[int] = []

    async def delete_user_cart_stub(user_id: int):
        deleted_cart_ids.append(user_id)

    cleared_draft_ids: list[int] = []

    async def clear_subscription_checkout_draft_stub(user_id: int):
        cleared_draft_ids.append(user_id)

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.get_user_cart',
        get_user_cart_stub,
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.delete_user_cart',
        delete_user_cart_stub,
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.clear_subscription_checkout_draft',
        clear_subscription_checkout_draft_stub,
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_texts',
        lambda lang: DummyTexts(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_period_description',
        lambda days, lang: f'{days} дней',
    )

    class _AdminServiceStub:
        def __init__(self):
            self.called = False

        async def send_subscription_purchase_notification(self, *args, **kwargs):
            self.called = True

    admin_service = _AdminServiceStub()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.AdminNotificationService',
        lambda bot: admin_service,
    )
    # Мокаем get_user_by_id чтобы вернуть того же user
    async def get_user_by_id_stub(*args, **kwargs):
        return user

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_user_by_id',
        get_user_by_id_stub,
    )

    class _BotStub:
        def __init__(self):
            self.sent_messages = 0

        async def send_message(self, *args, **kwargs):
            self.sent_messages += 1

    bot = _BotStub()
    db_session = SimpleNamespace()

    result = await auto_purchase_saved_cart_after_topup(db_session, user, bot=bot)

    assert result is True
    assert deleted_cart_ids == [user.id]
    assert cleared_draft_ids == [user.id]
    assert bot.sent_messages >= 1
    assert admin_service.called is True


async def test_auto_purchase_saved_cart_after_topup_extension(monkeypatch):
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)

    subscription = SimpleNamespace(
        id=99,
        is_trial=False,
        status='active',
        end_date=datetime.now(UTC),
        device_limit=1,
        traffic_limit_gb=100,
        connected_squads=['squad-a'],
        tariff_id=None,
    )

    user = SimpleNamespace(
        id=7,
        telegram_id=7007,
        balance_kopeks=200_000,
        language='ru',
        subscription=subscription,
        get_primary_promo_group=lambda: None,
    )

    cart_data = {
        'cart_mode': 'extend',
        'subscription_id': subscription.id,
        'period_days': 30,
        'total_price': 31_000,
        'description': 'Продление подписки на 30 дней',
        'device_limit': 2,
        'traffic_limit_gb': 500,
        'squad_uuid': 'squad-b',
        'consume_promo_offer': True,
    }

    subtract_calls: list[tuple] = []

    async def subtract_stub(*args, **kwargs):
        subtract_calls.append((args, kwargs))
        return True

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.subtract_user_balance',
        subtract_stub,
    )

    async def extend_stub(db, current_subscription, days, **kwargs):
        current_subscription.end_date = current_subscription.end_date + timedelta(days=days)
        return current_subscription

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.extend_subscription',
        extend_stub,
    )

    create_transaction_calls = {'count': 0}

    async def create_transaction_stub(*args, **kwargs):
        create_transaction_calls['count'] += 1
        return SimpleNamespace()

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.create_transaction',
        create_transaction_stub,
    )

    class _SubscriptionServiceStub:
        def __init__(self):
            self.update_called = False

        async def update_remnawave_user(self, *args, **kwargs):
            self.update_called = True

    service_stub = _SubscriptionServiceStub()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.SubscriptionService',
        lambda: service_stub,
    )

    async def get_user_cart_stub(_user_id):
        return cart_data

    deleted_cart_ids: list[int] = []

    async def delete_user_cart_stub(user_id: int):
        deleted_cart_ids.append(user_id)

    cleared_draft_ids: list[int] = []

    async def clear_checkout_draft_stub(user_id: int):
        cleared_draft_ids.append(user_id)

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.get_user_cart',
        get_user_cart_stub,
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.delete_user_cart',
        delete_user_cart_stub,
    )
    monkeypatch.setattr('app.services.subscription_auto_purchase_service.clear_subscription_checkout_draft', clear_checkout_draft_stub)

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_texts',
        lambda lang: DummyTexts(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_period_description',
        lambda days, lang: f'{days} дней',
    )

    class _AdminServiceStub:
        def __init__(self):
            self.called = False

        async def send_subscription_extension_notification(self, *args, **kwargs):
            self.called = True

    admin_service = _AdminServiceStub()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.AdminNotificationService',
        lambda bot: admin_service,
    )

    # Мок для get_subscription_by_user_id
    async def get_subscription_by_user_id_stub(*args, **kwargs):
        return subscription

    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        get_subscription_by_user_id_stub,
    )

    class _BotStub:
        def __init__(self):
            self.sent = 0

        async def send_message(self, *args, **kwargs):
            self.sent += 1

    bot = _BotStub()
    db_session = SimpleNamespace()

    result = await auto_purchase_saved_cart_after_topup(db_session, user, bot=bot)

    assert result is True
    assert len(subtract_calls) == 1
    assert subscription.device_limit == 2
    assert subscription.traffic_limit_gb == 500
    assert 'squad-b' in subscription.connected_squads
    assert deleted_cart_ids == [user.id]
    assert cleared_draft_ids == [user.id]
    assert admin_service.called is True
    assert bot.sent >= 1
    assert service_stub.update_called is True
    assert create_transaction_calls['count'] == 1


async def test_auto_purchase_trial_preserved_on_insufficient_balance(monkeypatch):
    """Тест: триал сохраняется, если не хватает денег для автопокупки"""
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)

    subscription = SimpleNamespace(
        id=123,
        is_trial=True,
        status='active',
        end_date=datetime.now(UTC) + timedelta(days=2),
        device_limit=1,
        traffic_limit_gb=10,
        connected_squads=[],
        tariff_id=None,
    )

    user = SimpleNamespace(
        id=99,
        telegram_id=9999,
        balance_kopeks=60_000,
        language='ru',
        subscription=subscription,
        get_primary_promo_group=lambda: None,
    )

    cart_data = {
        'cart_mode': 'extend',
        'subscription_id': subscription.id,
        'period_days': 30,
        'total_price': 50_000,
        'description': 'Продление на 30 дней',
        'device_limit': 1,
        'traffic_limit_gb': 100,
        'squad_uuid': None,
        'consume_promo_offer': False,
    }

    # Mock: недостаточно денег, списание не удалось
    subtract_calls = {'count': 0}

    async def subtract_stub(*args, **kwargs):
        subtract_calls['count'] += 1
        return False

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.subtract_user_balance',
        subtract_stub,
    )

    async def get_user_cart_stub(_user_id):
        return cart_data

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.get_user_cart',
        get_user_cart_stub,
    )

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_texts',
        lambda lang: DummyTexts(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_period_description',
        lambda days, lang: f'{days} дней',
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_local_datetime',
        lambda dt, fmt: dt.strftime(fmt) if dt else '',
    )

    class _AdminServiceStub:
        async def send_subscription_extension_notification(self, *args, **kwargs):
            return None

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.AdminNotificationService',
        lambda bot: _AdminServiceStub(),
    )

    # Мок для get_subscription_by_user_id
    async def get_subscription_by_user_id_stub(*args, **kwargs):
        return subscription

    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        get_subscription_by_user_id_stub,
    )

    db_session = SimpleNamespace()
    bot = None

    result = await auto_purchase_saved_cart_after_topup(db_session, user, bot=bot)

    # Проверки
    assert result is False  # Автопокупка не удалась
    assert subscription.is_trial is True  # ТРИАЛ СОХРАНЁН!
    assert subtract_calls['count'] == 1


async def test_auto_purchase_trial_converted_after_successful_extension(monkeypatch):
    """Тест: триал конвертируется в платную подписку ТОЛЬКО после успешного продления"""
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)

    subscription = MagicMock()
    subscription.id = 456
    subscription.is_trial = True  # Триальная подписка!
    subscription.status = 'active'
    subscription.end_date = datetime.now(UTC) + timedelta(days=1)
    subscription.device_limit = 1
    subscription.traffic_limit_gb = 10
    subscription.connected_squads = []

    user = MagicMock(spec=User)
    user.id = 88
    user.telegram_id = 8888
    user.balance_kopeks = 200_000  # Достаточно денег
    user.language = 'ru'
    user.subscription = subscription
    user.get_primary_promo_group = MagicMock(return_value=None)

    cart_data = {
        'cart_mode': 'extend',
        'subscription_id': subscription.id,
        'period_days': 30,
        'total_price': 100_000,
        'description': 'Продление на 30 дней',
        'device_limit': 2,
        'traffic_limit_gb': 500,
        'squad_uuid': None,
        'consume_promo_offer': False,
    }

    # Mock: деньги списались успешно
    subtract_called = {'value': False}

    async def subtract_stub(*args, **kwargs):
        subtract_called['value'] = True
        return True

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.subtract_user_balance',
        subtract_stub,
    )

    # Mock: продление успешно
    async def extend_stub(db, current_subscription, days, **kwargs):
        current_subscription.end_date = current_subscription.end_date + timedelta(days=days)
        return current_subscription

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.extend_subscription',
        extend_stub,
    )

    create_transaction_mock = AsyncMock(return_value=MagicMock())
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.create_transaction',
        create_transaction_mock,
    )

    service_mock = MagicMock()
    service_mock.update_remnawave_user = AsyncMock()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.SubscriptionService',
        lambda: service_mock,
    )

    async def get_user_cart_stub(_user_id):
        return cart_data

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.get_user_cart',
        get_user_cart_stub,
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.delete_user_cart',
        AsyncMock(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.clear_subscription_checkout_draft',
        AsyncMock(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_texts',
        lambda lang: DummyTexts(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_period_description',
        lambda days, lang: f'{days} дней',
    )
    # ИСПРАВЛЕНО: Добавлен мок для format_local_datetime
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_local_datetime',
        lambda dt, fmt: dt.strftime(fmt) if dt else '',
    )

    admin_service_mock = MagicMock()
    admin_service_mock.send_subscription_extension_notification = AsyncMock()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.AdminNotificationService',
        lambda bot: admin_service_mock,
    )

    # Мок для get_subscription_by_user_id
    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        AsyncMock(return_value=subscription),
    )

    db_session = AsyncMock(spec=AsyncSession)
    db_session.commit = AsyncMock()  # Важно! Отслеживаем commit
    db_session.refresh = AsyncMock()  # ИСПРАВЛЕНО: Добавлен мок для refresh
    bot = AsyncMock()

    result = await auto_purchase_saved_cart_after_topup(db_session, user, bot=bot)

    # Проверки
    assert result is True  # Автопокупка успешна
    assert subscription.is_trial is False  # ТРИАЛ КОНВЕРТИРОВАН!
    assert subscription.status == 'active'
    db_session.commit.assert_awaited()  # Commit был вызван


async def test_auto_purchase_trial_preserved_on_extension_failure(monkeypatch):
    """Тест: триал НЕ конвертируется и вызывается rollback при ошибке в extend_subscription"""
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)

    subscription = SimpleNamespace(
        id=789,
        is_trial=True,
        status='active',
        end_date=datetime.now(UTC) + timedelta(days=3),
        tariff_id=None,
        device_limit=1,
        traffic_limit_gb=10,
        connected_squads=[],
    )

    user = SimpleNamespace(
        id=77,
        telegram_id=7777,
        balance_kopeks=200_000,
        language='ru',
        subscription=subscription,
        get_primary_promo_group=lambda: None,
    )

    cart_data = {
        'cart_mode': 'extend',
        'subscription_id': subscription.id,
        'period_days': 30,
        'total_price': 100_000,
        'description': 'Продление на 30 дней',
        'device_limit': 1,
        'traffic_limit_gb': 100,
        'squad_uuid': None,
        'consume_promo_offer': False,
    }

    # Mock: деньги списались успешно
    subtract_called = {'value': False}

    async def subtract_stub(*args, **kwargs):
        subtract_called['value'] = True
        return True

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.subtract_user_balance',
        subtract_stub,
    )

    # Mock: extend_subscription выбрасывает ошибку!
    async def extend_error(db, current_subscription, days, **kwargs):
        raise Exception('Database connection error')

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.extend_subscription',
        extend_error,
    )

    async def get_user_cart_stub(_user_id):
        return cart_data

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.get_user_cart',
        get_user_cart_stub,
    )

    # ИСПРАВЛЕНО: Добавлены недостающие моки
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_texts',
        lambda lang: DummyTexts(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_period_description',
        lambda days, lang: f'{days} дней',
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_local_datetime',
        lambda dt, fmt: dt.strftime(fmt) if dt else '',
    )

    class _AdminServiceStub:
        async def send_subscription_extension_notification(self, *args, **kwargs):
            return None

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.AdminNotificationService',
        lambda bot: _AdminServiceStub(),
    )

    # Мок для get_subscription_by_user_id
    async def get_subscription_by_user_id_stub(*args, **kwargs):
        return subscription

    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        get_subscription_by_user_id_stub,
    )

    class DummyDbSession:
        def __init__(self):
            self.rollback_called = False

        async def rollback(self):
            self.rollback_called = True

        async def refresh(self, *_args, **_kwargs):
            return None

    db_session = DummyDbSession()
    bot = None

    result = await auto_purchase_saved_cart_after_topup(db_session, user, bot=bot)

    # Проверки
    assert result is False  # Автопокупка не удалась
    assert subscription.is_trial is True  # ТРИАЛ СОХРАНЁН!
    assert subtract_called['value'] is True
    assert db_session.rollback_called is True  # ROLLBACK БЫЛ ВЫЗВАН!


async def test_auto_purchase_trial_remaining_days_transferred(monkeypatch):
    """Тест: остаток триала переносится на платную подписку при TRIAL_ADD_REMAINING_DAYS_TO_PAID=True"""
    monkeypatch.setattr(settings, 'AUTO_PURCHASE_AFTER_TOPUP_ENABLED', True)
    monkeypatch.setattr(settings, 'TRIAL_ADD_REMAINING_DAYS_TO_PAID', True)  # Включено!

    now = datetime.now(UTC)
    trial_end = now + timedelta(days=2)  # Осталось 2 дня триала

    subscription = MagicMock()
    subscription.id = 321
    subscription.is_trial = True
    subscription.status = 'active'
    subscription.end_date = trial_end
    subscription.start_date = now - timedelta(days=1)  # Триал начался вчера
    subscription.device_limit = 1
    subscription.traffic_limit_gb = 10
    subscription.connected_squads = []
    subscription.tariff_id = None  # Триал без тарифа

    user = MagicMock(spec=User)
    user.id = 66
    user.telegram_id = 6666
    user.balance_kopeks = 200_000
    user.language = 'ru'
    user.subscription = subscription
    user.get_primary_promo_group = MagicMock(return_value=None)

    cart_data = {
        'cart_mode': 'extend',
        'subscription_id': subscription.id,
        'period_days': 30,  # Покупает 30 дней
        'total_price': 100_000,
        'description': 'Продление на 30 дней',
        'device_limit': 1,
        'traffic_limit_gb': 100,
        'squad_uuid': None,
        'consume_promo_offer': False,
    }

    subtract_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.subtract_user_balance',
        subtract_mock,
    )

    # Mock: extend_subscription с логикой сохранения остатка подписки
    # Имитируем логику из extend_subscription() — ветка is_tariff_change
    async def extend_with_bonus(db, current_subscription, days, **kwargs):
        tariff_id = kwargs.get('tariff_id')
        is_tariff_change = tariff_id is not None and (
            current_subscription.tariff_id is None or tariff_id != current_subscription.tariff_id
        )

        if is_tariff_change:
            remaining_seconds = 0
            if current_subscription.end_date and current_subscription.end_date > now:
                if not current_subscription.is_trial or settings.TRIAL_ADD_REMAINING_DAYS_TO_PAID:
                    remaining = current_subscription.end_date - now
                    remaining_seconds = max(0, remaining.total_seconds())
            current_subscription.end_date = now + timedelta(days=days, seconds=remaining_seconds)
            current_subscription.start_date = now
        elif current_subscription.end_date and current_subscription.end_date > now:
            current_subscription.end_date = current_subscription.end_date + timedelta(days=days)
        else:
            current_subscription.end_date = now + timedelta(days=days)

        if tariff_id is not None:
            current_subscription.tariff_id = tariff_id
        return current_subscription

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.extend_subscription',
        extend_with_bonus,
    )

    create_transaction_mock = AsyncMock(return_value=MagicMock())
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.create_transaction',
        create_transaction_mock,
    )

    service_mock = MagicMock()
    service_mock.update_remnawave_user = AsyncMock()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.SubscriptionService',
        lambda: service_mock,
    )

    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.get_user_cart',
        AsyncMock(return_value=cart_data),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.user_cart_service.delete_user_cart',
        AsyncMock(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.clear_subscription_checkout_draft',
        AsyncMock(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.get_texts',
        lambda lang: DummyTexts(),
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_period_description',
        lambda days, lang: f'{days} дней',
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.format_local_datetime',
        lambda dt, fmt: dt.strftime(fmt),
    )

    admin_service_mock = MagicMock()
    admin_service_mock.send_subscription_extension_notification = AsyncMock()
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.AdminNotificationService',
        lambda bot: admin_service_mock,
    )

    # Мок для get_subscription_by_user_id
    monkeypatch.setattr(
        'app.database.crud.subscription.get_subscription_by_user_id',
        AsyncMock(return_value=subscription),
    )

    db_session = AsyncMock(spec=AsyncSession)
    db_session.commit = AsyncMock()
    db_session.refresh = AsyncMock()  # ИСПРАВЛЕНО: Добавлен мок для refresh
    bot = AsyncMock()

    result = await auto_purchase_saved_cart_after_topup(db_session, user, bot=bot)

    # Проверки
    assert result is True
    assert subscription.is_trial is False  # Триал конвертирован

    # Проверяем, что подписка продлена на 30 дней + 2 оставшихся дня триала = 32 от now
    # end_date = trial_end + 30 = (now + 2) + 30 = now + 32
    actual_total_days = (subscription.end_date - now).days
    assert actual_total_days == 32, (
        f'Expected 32 days from now (30 purchased + 2 remaining trial), got {actual_total_days}'
    )
