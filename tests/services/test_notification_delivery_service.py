from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.services.notification_delivery_service import NotificationDeliveryService, NotificationType


pytestmark = pytest.mark.asyncio


async def test_send_notification_suppresses_unexpected_errors(monkeypatch):
    service = NotificationDeliveryService()
    user = SimpleNamespace(
        id=123,
        status='active',
        telegram_id=999111222,
        email=None,
        email_verified=False,
    )

    async def _raise_unexpected(*args, **kwargs):
        _ = args, kwargs
        raise RuntimeError('unexpected notification failure')

    monkeypatch.setattr(service, '_send_telegram_notification', _raise_unexpected)

    result = await service.send_notification(
        user=user,
        notification_type=NotificationType.BALANCE_TOPUP,
        context={},
        bot=AsyncMock(),
        telegram_message='test',
    )

    assert result is False
