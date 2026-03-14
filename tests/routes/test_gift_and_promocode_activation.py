from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.database.models import GuestPurchaseStatus
from app.services import guest_purchase_service as gift_service
from app.services.guest_purchase_service import GuestPurchaseError
from app.webapi.routes import miniapp
from app.webapi.schemas.miniapp import MiniAppPromoCodeActivationRequest


pytestmark = pytest.mark.asyncio


class _ExecuteResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return self

    def first(self):
        return self._value


def _build_user(user_id: int = 10):
    return SimpleNamespace(
        id=user_id,
        username='testuser',
        telegram_id=123456789,
        remnawave_uuid='uuid-1',
    )


def _build_purchase(
    *,
    status: str,
    token: str | None = None,
    buyer_user_id: int = 99,
    user_id: int | None = None,
):
    token_value = token or 'gift_token_1234567890'
    return SimpleNamespace(
        id=1,
        token=token_value,
        status=status,
        buyer_user_id=buyer_user_id,
        user_id=user_id,
        tariff_id=1,
        tariff=SimpleNamespace(name='Обычный'),
        period_days=14,
        is_gift=True,
    )


async def test_gift_activate_returns_existing_purchase_when_already_delivered(monkeypatch):
    user = _build_user()
    purchase = _build_purchase(status=GuestPurchaseStatus.DELIVERED.value, user_id=user.id)
    db = SimpleNamespace(execute=AsyncMock(return_value=_ExecuteResult(purchase)), commit=AsyncMock(), refresh=AsyncMock())

    monkeypatch.setattr(gift_service, 'get_tariff_by_id', AsyncMock(return_value=SimpleNamespace(id=1, is_active=True)))
    monkeypatch.setattr(gift_service, '_apply_purchase_subscription', AsyncMock())

    result = await gift_service.activate_purchase(db, purchase.token, skip_notification=True)

    assert result.status == GuestPurchaseStatus.DELIVERED.value
    db.commit.assert_not_awaited()


async def test_gift_activate_marks_delivered(monkeypatch):
    user = _build_user()
    purchase = _build_purchase(status=GuestPurchaseStatus.PENDING_ACTIVATION.value, user_id=user.id)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_ExecuteResult(purchase)),
        commit=AsyncMock(),
        refresh=AsyncMock(),
    )
    monkeypatch.setattr(gift_service, 'get_tariff_by_id', AsyncMock(return_value=SimpleNamespace(id=1, is_active=True)))
    monkeypatch.setattr(
        gift_service,
        '_apply_purchase_subscription',
        AsyncMock(),
    )

    async def _fake_execute(query):
        _ = query
        return _ExecuteResult(user)

    db.execute = AsyncMock(side_effect=[_ExecuteResult(purchase), _ExecuteResult(user)])

    response = await gift_service.activate_purchase(db, purchase.token, skip_notification=True)

    assert response.status == GuestPurchaseStatus.DELIVERED.value
    assert purchase.delivered_at is not None
    db.commit.assert_awaited()


async def test_gift_activate_rejects_invalid_status():
    purchase = _build_purchase(status=GuestPurchaseStatus.PAID.value, user_id=10)
    db = SimpleNamespace(execute=AsyncMock(return_value=_ExecuteResult(purchase)))

    with pytest.raises(GuestPurchaseError) as exc_info:
        await gift_service.activate_purchase(db, purchase.token, skip_notification=True)

    assert exc_info.value.status_code == 400
    assert exc_info.value.message == 'Purchase is not pending activation'


async def test_gift_activate_raises_not_found_for_missing_purchase():
    db = SimpleNamespace(execute=AsyncMock(return_value=_ExecuteResult(None)))

    with pytest.raises(GuestPurchaseError) as exc_info:
        await gift_service.activate_purchase(db, 'unknown-token', skip_notification=True)

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == 'Purchase not found'


async def test_miniapp_promocode_returns_locale_ready_used_error(monkeypatch):
    user = SimpleNamespace(id=5)

    monkeypatch.setattr(miniapp, 'parse_webapp_init_data', lambda init_data, token: {'user': {'id': 555}})
    monkeypatch.setattr(miniapp, 'get_user_by_telegram_id', AsyncMock(return_value=user))
    monkeypatch.setattr(
        miniapp.promo_code_service,
        'activate_promocode',
        AsyncMock(return_value={'success': False, 'error': 'already_used_by_user'}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await miniapp.activate_promo_code(
            MiniAppPromoCodeActivationRequest(initData='ok', code='GIFTCODE'),
            db=SimpleNamespace(),
        )

    assert exc_info.value.status_code == 409
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail.get('code') == 'already_used_by_user'
    assert exc_info.value.detail.get('message') == 'Promo code already used by this user'


async def test_miniapp_promocode_returns_locale_ready_server_error(monkeypatch):
    user = SimpleNamespace(id=5)

    monkeypatch.setattr(miniapp, 'parse_webapp_init_data', lambda init_data, token: {'user': {'id': 555}})
    monkeypatch.setattr(miniapp, 'get_user_by_telegram_id', AsyncMock(return_value=user))
    monkeypatch.setattr(
        miniapp.promo_code_service,
        'activate_promocode',
        AsyncMock(return_value={'success': False, 'error': 'server_error'}),
    )

    with pytest.raises(HTTPException) as exc_info:
        await miniapp.activate_promo_code(
            MiniAppPromoCodeActivationRequest(initData='ok', code='GIFTCODE'),
            db=SimpleNamespace(),
        )

    assert exc_info.value.status_code == 500
    assert isinstance(exc_info.value.detail, dict)
    assert exc_info.value.detail.get('code') == 'server_error'
    assert exc_info.value.detail.get('message') == 'Failed to activate promo code'
