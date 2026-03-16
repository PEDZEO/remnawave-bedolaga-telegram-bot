from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.exc import MissingGreenlet


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.payment.common import PaymentCommonMixin, send_cart_notification_after_topup


class _FakeBot:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_message(self, **kwargs):  # type: ignore[no-untyped-def]
        self.messages.append(kwargs)


class _LazyUser:
    id = 99
    telegram_id = 555
    language = 'ru'

    @property
    def subscription(self):  # type: ignore[no-untyped-def]
        raise MissingGreenlet('lazy load is not available')


class _PaymentServiceStub(PaymentCommonMixin):
    def __init__(self) -> None:
        self.bot = _FakeBot()
        self.keyboard_user: SimpleNamespace | None = None

    async def build_topup_success_keyboard(self, user):  # type: ignore[no-untyped-def]
        self.keyboard_user = user
        return InlineKeyboardMarkup(inline_keyboard=[])


@pytest.mark.asyncio
async def test_send_payment_success_notification_recovers_missing_greenlet(monkeypatch: pytest.MonkeyPatch) -> None:
    service = _PaymentServiceStub()
    lazy_user = _LazyUser()

    reloaded_user = SimpleNamespace(
        id=lazy_user.id,
        telegram_id=lazy_user.telegram_id,
        language=lazy_user.language,
        subscription=SimpleNamespace(
            is_trial=False,
            is_active=True,
            actual_status='active',
        ),
    )

    sentinel_db = object()

    async def fake_get_user_by_telegram_id(db, telegram_id):  # type: ignore[no-untyped-def]
        assert db is sentinel_db
        assert telegram_id == lazy_user.telegram_id
        return reloaded_user

    async def fake_get_db():  # type: ignore[no-untyped-def]
        yield object()

    monkeypatch.setattr(
        'app.services.payment.common.get_user_by_telegram_id',
        fake_get_user_by_telegram_id,
    )
    monkeypatch.setattr(
        'app.services.payment.common.get_db',
        fake_get_db,
    )
    websocket_module = ModuleType('app.cabinet.routes.websocket')

    async def notify_user_balance_topup_stub(*args, **kwargs):  # type: ignore[no-untyped-def]
        return None

    websocket_module.notify_user_balance_topup = notify_user_balance_topup_stub  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, 'app.cabinet.routes.websocket', websocket_module)
    await service._send_payment_success_notification(
        lazy_user.telegram_id,
        12300,
        user=lazy_user,
        db=sentinel_db,
        payment_method_title='Тестовый метод',
    )

    assert service.bot.messages, 'Ожидалось, что уведомление будет отправлено'
    message = service.bot.messages[0]
    assert 'Тестовый метод' in message['text']
    assert service.keyboard_user is not None
    assert isinstance(service.keyboard_user, SimpleNamespace)


@pytest.mark.asyncio
async def test_send_cart_notification_after_topup_still_attempts_auto_purchase_in_ultima(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auto_purchase_calls: list[tuple[object, object]] = []

    async def auto_purchase_stub(db, user, *, bot=None):  # type: ignore[no-untyped-def]
        auto_purchase_calls.append((db, user))
        return False

    async def is_ultima_enabled_stub() -> bool:
        return True

    async def has_user_cart_stub(_user_id: int) -> bool:
        return True

    async def get_user_cart_stub(_user_id: int):  # type: ignore[no-untyped-def]
        return {'total_price': 5_000}

    monkeypatch.setattr(
        'app.services.payment.common.is_ultima_mode_enabled_cached',
        is_ultima_enabled_stub,
    )
    monkeypatch.setattr(
        'app.services.subscription_auto_purchase_service.auto_purchase_saved_cart_after_topup',
        auto_purchase_stub,
    )
    monkeypatch.setattr(
        'app.services.user_cart_service.user_cart_service.has_user_cart',
        has_user_cart_stub,
    )
    monkeypatch.setattr(
        'app.services.user_cart_service.user_cart_service.get_user_cart',
        get_user_cart_stub,
    )

    user = SimpleNamespace(id=17, telegram_id=7017, language='ru')
    db = object()
    bot = _FakeBot()

    result = await send_cart_notification_after_topup(
        user=user,
        amount_kopeks=1_000,
        db=db,
        bot=bot,
    )

    assert result is False
    assert auto_purchase_calls == [(db, user)]
    assert bot.messages == []
