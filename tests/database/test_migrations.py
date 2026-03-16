from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.database import migrations


@pytest.mark.asyncio
async def test_run_alembic_upgrade_applies_legacy_remap(monkeypatch: pytest.MonkeyPatch) -> None:
    remap_mock = AsyncMock(return_value=True)
    fresh_db_mock = AsyncMock(return_value=False)
    current_snapshot_mock = AsyncMock(return_value=False)
    needs_stamp_mock = AsyncMock(return_value=False)
    monkeypatch.setattr(migrations, '_remap_legacy_revision_if_needed', remap_mock)
    monkeypatch.setattr(migrations, '_is_fresh_database', fresh_db_mock)
    monkeypatch.setattr(migrations, '_is_current_schema_snapshot_without_alembic', current_snapshot_mock)
    monkeypatch.setattr(migrations, '_needs_auto_stamp', needs_stamp_mock)

    stamp_mock = AsyncMock()
    bootstrap_mock = AsyncMock()
    monkeypatch.setattr(migrations, '_stamp_alembic_revision', stamp_mock)
    monkeypatch.setattr(migrations, '_bootstrap_current_schema', bootstrap_mock)

    cfg = object()
    monkeypatch.setattr(migrations, '_get_alembic_config', lambda: cfg)

    upgrade_mock = Mock()
    monkeypatch.setattr(migrations.command, 'upgrade', upgrade_mock)

    async def run_in_executor(_executor, fn, *args):
        fn(*args)

    fake_loop = SimpleNamespace(run_in_executor=run_in_executor)
    monkeypatch.setattr('asyncio.get_running_loop', lambda: fake_loop)

    await migrations.run_alembic_upgrade()

    remap_mock.assert_awaited_once()
    fresh_db_mock.assert_awaited_once()
    current_snapshot_mock.assert_awaited_once()
    needs_stamp_mock.assert_awaited_once()
    bootstrap_mock.assert_not_awaited()
    stamp_mock.assert_not_awaited()
    upgrade_mock.assert_called_once_with(cfg, 'heads')


@pytest.mark.asyncio
async def test_run_alembic_upgrade_bootstraps_fresh_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(migrations, '_remap_legacy_revision_if_needed', AsyncMock(return_value=False))
    monkeypatch.setattr(migrations, '_is_fresh_database', AsyncMock(return_value=True))
    current_snapshot_mock = AsyncMock(return_value=False)
    needs_stamp_mock = AsyncMock(return_value=False)
    bootstrap_mock = AsyncMock()
    stamp_mock = AsyncMock()
    upgrade_mock = Mock()

    monkeypatch.setattr(migrations, '_is_current_schema_snapshot_without_alembic', current_snapshot_mock)
    monkeypatch.setattr(migrations, '_needs_auto_stamp', needs_stamp_mock)
    monkeypatch.setattr(migrations, '_bootstrap_current_schema', bootstrap_mock)
    monkeypatch.setattr(migrations, '_stamp_alembic_revision', stamp_mock)
    monkeypatch.setattr(migrations.command, 'upgrade', upgrade_mock)

    await migrations.run_alembic_upgrade()

    bootstrap_mock.assert_awaited_once()
    stamp_mock.assert_awaited_once_with('heads')
    current_snapshot_mock.assert_not_awaited()
    needs_stamp_mock.assert_not_awaited()
    upgrade_mock.assert_not_called()


@pytest.mark.asyncio
async def test_run_alembic_upgrade_stamps_current_schema_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(migrations, '_remap_legacy_revision_if_needed', AsyncMock(return_value=False))
    monkeypatch.setattr(migrations, '_is_fresh_database', AsyncMock(return_value=False))
    monkeypatch.setattr(migrations, '_is_current_schema_snapshot_without_alembic', AsyncMock(return_value=True))
    needs_stamp_mock = AsyncMock(return_value=False)
    bootstrap_mock = AsyncMock()
    stamp_mock = AsyncMock()
    upgrade_mock = Mock()

    monkeypatch.setattr(migrations, '_needs_auto_stamp', needs_stamp_mock)
    monkeypatch.setattr(migrations, '_bootstrap_current_schema', bootstrap_mock)
    monkeypatch.setattr(migrations, '_stamp_alembic_revision', stamp_mock)
    monkeypatch.setattr(migrations.command, 'upgrade', upgrade_mock)

    await migrations.run_alembic_upgrade()

    bootstrap_mock.assert_not_awaited()
    stamp_mock.assert_awaited_once_with('heads')
    needs_stamp_mock.assert_not_awaited()
    upgrade_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stamp_alembic_head_runs_stamp_command(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = object()
    monkeypatch.setattr(migrations, '_get_alembic_config', lambda: cfg)

    stamp_mock = Mock()
    monkeypatch.setattr(migrations.command, 'stamp', stamp_mock)

    async def run_in_executor(_executor, fn, *args):
        fn(*args)

    fake_loop = SimpleNamespace(run_in_executor=run_in_executor)
    monkeypatch.setattr('asyncio.get_running_loop', lambda: fake_loop)

    await migrations.stamp_alembic_head()

    stamp_mock.assert_called_once_with(cfg, 'heads')
