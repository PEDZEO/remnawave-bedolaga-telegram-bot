from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.models import ButtonClickLog
from app.services.menu_layout.stats_service import MenuLayoutStatsService


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


@pytest.mark.asyncio
async def test_log_button_click_retries_without_user_on_integrity_error() -> None:
    db = MagicMock()
    db.execute = AsyncMock(
        side_effect=[
            _ScalarResult(142),
            IntegrityError('stmt', {}, Exception('fk')),
            _ScalarResult(101),
        ]
    )
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    click_obj = MagicMock()
    db.get = AsyncMock(return_value=click_obj)

    result = await MenuLayoutStatsService.log_button_click(
        db,
        button_id='admin_panel',
        user_id=142,
        callback_data='admin_panel',
        button_type='builtin',
        button_text='Admin',
    )

    assert result is click_obj
    assert db.rollback.await_count == 1
    assert db.commit.await_count == 1
    assert db.execute.await_count == 3

    fallback_insert = db.execute.await_args_list[2].args[0]
    assert fallback_insert._values[ButtonClickLog.__table__.c.user_id].value is None
