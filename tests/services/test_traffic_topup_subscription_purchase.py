from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.database.crud import subscription as subscription_crud
from app.database.crud.subscription import (
    extend_subscription,
    get_subscription_base_traffic_limit,
    get_subscription_total_with_purchased_traffic,
)
from app.database.models import SubscriptionStatus


class _FakeSession:
    def __init__(self) -> None:
        self.commit = AsyncMock()
        self.flush = AsyncMock()
        self.refresh = AsyncMock()


def test_subscription_base_traffic_excludes_active_topups() -> None:
    subscription = SimpleNamespace(
        id=1,
        traffic_limit_gb=120,
        purchased_traffic_gb=20,
    )

    assert get_subscription_base_traffic_limit(subscription) == 100
    assert get_subscription_total_with_purchased_traffic(100, subscription) == 120


def test_subscription_base_traffic_falls_back_for_inconsistent_topups() -> None:
    subscription = SimpleNamespace(
        id=2,
        traffic_limit_gb=20,
        purchased_traffic_gb=25,
    )

    assert get_subscription_base_traffic_limit(subscription) == 20


@pytest.mark.asyncio
async def test_extending_subscription_does_not_make_topup_permanent(monkeypatch: pytest.MonkeyPatch) -> None:
    async def clear_notifications_stub(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(subscription_crud, 'clear_notifications', clear_notifications_stub)

    now = datetime.now(UTC)
    subscription = SimpleNamespace(
        id=3,
        user_id=30,
        status=SubscriptionStatus.ACTIVE.value,
        start_date=now - timedelta(days=10),
        end_date=now + timedelta(days=20),
        tariff_id=10,
        is_trial=False,
        traffic_limit_gb=120,
        purchased_traffic_gb=20,
        traffic_reset_at=now + timedelta(days=30),
        traffic_used_gb=5.0,
        device_limit=2,
        connected_squads=[],
        updated_at=None,
    )
    db = _FakeSession()

    await extend_subscription(
        db,
        subscription,
        30,
        tariff_id=10,
        traffic_limit_gb=100,
    )

    assert subscription.traffic_limit_gb == 120
    assert subscription.purchased_traffic_gb == 20
    assert subscription.traffic_reset_at is not None
    db.commit.assert_awaited()
    db.refresh.assert_awaited()
