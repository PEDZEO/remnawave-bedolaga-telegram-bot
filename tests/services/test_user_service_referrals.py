import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services import user_service as user_service_module
from app.services.user_service import UserService


pytestmark = pytest.mark.asyncio


class _ScalarResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values

    def scalar_one_or_none(self):
        return self._values[0] if self._values else None


async def test_update_user_referrals_rejects_missing_users(monkeypatch):
    user = SimpleNamespace(id=1, referred_by_id=None)
    db = SimpleNamespace(
        execute=AsyncMock(return_value=_ScalarResult([2])),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    monkeypatch.setattr(user_service_module, 'get_user_by_id', AsyncMock(return_value=user))
    monkeypatch.setattr(user_service_module, 'get_referrals', AsyncMock(return_value=[]))

    success, details = await UserService().update_user_referrals(db, 1, [2, 3], admin_id=99)

    assert success is False
    assert details == {'error': 'referral_users_not_found', 'missing_ids': [3]}
    db.commit.assert_not_awaited()


async def test_update_user_referrals_rejects_referrer_cycle(monkeypatch):
    user = SimpleNamespace(id=1, referred_by_id=5)
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_ScalarResult([5]), _ScalarResult([])]),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    monkeypatch.setattr(user_service_module, 'get_user_by_id', AsyncMock(return_value=user))
    monkeypatch.setattr(user_service_module, 'get_referrals', AsyncMock(return_value=[]))

    success, details = await UserService().update_user_referrals(db, 1, [5], admin_id=99)

    assert success is False
    assert details == {'error': 'referral_cycle', 'cyclic_ids': [5]}
    db.commit.assert_not_awaited()


async def test_update_user_referrals_adds_and_removes(monkeypatch):
    user = SimpleNamespace(id=1, referred_by_id=None)
    current_referral = SimpleNamespace(id=3)
    db = SimpleNamespace(
        execute=AsyncMock(side_effect=[_ScalarResult([2, 4]), _ScalarResult([]), _ScalarResult([])]),
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )

    monkeypatch.setattr(user_service_module, 'get_user_by_id', AsyncMock(return_value=user))
    monkeypatch.setattr(user_service_module, 'get_referrals', AsyncMock(return_value=[current_referral]))

    success, details = await UserService().update_user_referrals(db, 1, [2, 4], admin_id=99)

    assert success is True
    assert details == {'added': 2, 'removed': 1, 'total': 2}
    assert db.execute.await_count == 3
    db.commit.assert_awaited_once()
