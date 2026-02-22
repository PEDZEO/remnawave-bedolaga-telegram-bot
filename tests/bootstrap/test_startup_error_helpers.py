from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap import contest_rotation_startup, reporting_startup, startup_error_helpers


class _StageStub:
    def warning(self, _message: str) -> None:
        return None

    def log(self, _message: str, icon: str = '•') -> None:
        return None

    def skip(self, _message: str) -> None:
        return None


class _TimelineStub:
    @asynccontextmanager
    async def stage(self, *_args, **_kwargs):
        yield _StageStub()


def test_warn_startup_stage_error_sets_warning_and_logs_error() -> None:
    stage = MagicMock()
    logger = MagicMock()
    error = RuntimeError('boom')

    startup_error_helpers.warn_startup_stage_error(
        stage=stage,
        logger=logger,
        stage_error_message='Ошибка запуска сервиса отчетов',
        logger_error_message='❌ Ошибка запуска сервиса отчетов',
        error=error,
    )

    stage.warning.assert_called_once_with('Ошибка запуска сервиса отчетов: boom')
    logger.error.assert_called_once_with('❌ Ошибка запуска сервиса отчетов', error=error)


@pytest.mark.asyncio
async def test_initialize_reporting_stage_uses_shared_error_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = _TimelineStub()
    logger = MagicMock()
    bot = MagicMock()
    helper = MagicMock()

    monkeypatch.setattr(reporting_startup, 'warn_startup_stage_error', helper)
    monkeypatch.setattr(reporting_startup.reporting_service, 'set_bot', MagicMock())
    monkeypatch.setattr(reporting_startup.reporting_service, 'start', AsyncMock(side_effect=RuntimeError('boom')))

    await reporting_startup.initialize_reporting_stage(timeline, logger, bot)

    helper.assert_called_once()
    kwargs = helper.call_args.kwargs
    assert kwargs['logger'] is logger
    assert kwargs['stage_error_message'] == 'Ошибка запуска сервиса отчетов'
    assert kwargs['logger_error_message'] == '❌ Ошибка запуска сервиса отчетов'
    assert str(kwargs['error']) == 'boom'


@pytest.mark.asyncio
async def test_initialize_contest_rotation_stage_uses_shared_error_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = _TimelineStub()
    logger = MagicMock()
    bot = MagicMock()
    helper = MagicMock()

    monkeypatch.setattr(contest_rotation_startup, 'warn_startup_stage_error', helper)
    monkeypatch.setattr(contest_rotation_startup.contest_rotation_service, 'set_bot', MagicMock())
    monkeypatch.setattr(
        contest_rotation_startup.contest_rotation_service,
        'start',
        AsyncMock(side_effect=RuntimeError('boom')),
    )

    await contest_rotation_startup.initialize_contest_rotation_stage(timeline, logger, bot)

    helper.assert_called_once()
    kwargs = helper.call_args.kwargs
    assert kwargs['logger'] is logger
    assert kwargs['stage_error_message'] == 'Ошибка запуска ротации игр'
    assert kwargs['logger_error_message'] == '❌ Ошибка запуска ротации игр'
    assert str(kwargs['error']) == 'boom'
