from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap.database_startup import run_database_migration_stage


class _StageRecorder:
    def __init__(self) -> None:
        self.success_calls: list[str] = []
        self.warning_calls: list[str] = []

    def success(self, message: str) -> None:
        self.success_calls.append(message)

    def warning(self, message: str) -> None:
        self.warning_calls.append(message)


class _TimelineRecorder:
    def __init__(self) -> None:
        self.manual_steps: list[tuple[str, str, str, str]] = []
        self.last_stage: _StageRecorder | None = None

    def add_manual_step(self, title: str, icon: str, status_label: str, message: str) -> None:
        self.manual_steps.append((title, icon, status_label, message))

    @asynccontextmanager
    async def stage(self, *_args, **_kwargs):
        stage = _StageRecorder()
        self.last_stage = stage
        yield stage


@pytest.mark.asyncio
async def test_database_migration_stage_skips_when_flag_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = _TimelineRecorder()
    logger = MagicMock()
    run_upgrade = AsyncMock()

    monkeypatch.setenv('SKIP_MIGRATION', 'true')
    monkeypatch.setattr('app.bootstrap.database_startup.run_alembic_upgrade', run_upgrade)

    await run_database_migration_stage(timeline, logger)

    run_upgrade.assert_not_awaited()
    assert timeline.manual_steps == [
        ('Миграция базы данных (Alembic)', '⏭️', 'Пропущено', 'SKIP_MIGRATION=true'),
    ]


@pytest.mark.asyncio
async def test_database_migration_stage_marks_success(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = _TimelineRecorder()
    logger = MagicMock()
    run_upgrade = AsyncMock()

    monkeypatch.delenv('SKIP_MIGRATION', raising=False)
    monkeypatch.delenv('ALLOW_MIGRATION_FAILURE', raising=False)
    monkeypatch.setattr('app.bootstrap.database_startup.run_alembic_upgrade', run_upgrade)

    await run_database_migration_stage(timeline, logger)

    run_upgrade.assert_awaited_once()
    assert timeline.last_stage is not None
    assert timeline.last_stage.success_calls == ['Миграция завершена успешно']
    assert timeline.last_stage.warning_calls == []


@pytest.mark.asyncio
async def test_database_migration_stage_raises_when_failures_not_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = _TimelineRecorder()
    logger = MagicMock()
    run_upgrade = AsyncMock(side_effect=RuntimeError('boom'))

    monkeypatch.delenv('SKIP_MIGRATION', raising=False)
    monkeypatch.setenv('ALLOW_MIGRATION_FAILURE', 'false')
    monkeypatch.setattr('app.bootstrap.database_startup.run_alembic_upgrade', run_upgrade)

    with pytest.raises(RuntimeError, match='boom'):
        await run_database_migration_stage(timeline, logger)

    logger.error.assert_called_once()
    assert timeline.last_stage is not None
    assert timeline.last_stage.warning_calls == []


@pytest.mark.asyncio
async def test_database_migration_stage_warns_when_failure_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = _TimelineRecorder()
    logger = MagicMock()
    run_upgrade = AsyncMock(side_effect=RuntimeError('boom'))

    monkeypatch.delenv('SKIP_MIGRATION', raising=False)
    monkeypatch.setenv('ALLOW_MIGRATION_FAILURE', 'true')
    monkeypatch.setattr('app.bootstrap.database_startup.run_alembic_upgrade', run_upgrade)

    await run_database_migration_stage(timeline, logger)

    logger.error.assert_called_once()
    assert timeline.last_stage is not None
    assert timeline.last_stage.warning_calls == ['Ошибка миграции: boom (ALLOW_MIGRATION_FAILURE=true)']
