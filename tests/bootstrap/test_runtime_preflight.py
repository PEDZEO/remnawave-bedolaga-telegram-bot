from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap import runtime_preflight


def test_build_preflight_banner_metadata_uses_settings_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        runtime_preflight,
        'settings',
        SimpleNamespace(LOG_LEVEL='DEBUG', DATABASE_MODE='sqlite'),
    )

    metadata = runtime_preflight._build_preflight_banner_metadata()

    assert metadata == [
        ('Уровень логирования', 'DEBUG'),
        ('Режим БД', 'sqlite'),
    ]


@pytest.mark.asyncio
async def test_prepare_runtime_preflight_logs_banner_from_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    timeline = MagicMock()
    telegram_notifier = object()

    monkeypatch.setattr(
        runtime_preflight,
        'setup_logging',
        lambda: ('file_formatter', 'console_formatter', telegram_notifier),
    )
    configure_runtime_logging = AsyncMock()
    monkeypatch.setattr(runtime_preflight, 'configure_runtime_logging', configure_runtime_logging)
    monkeypatch.setattr(runtime_preflight.structlog, 'get_logger', lambda _name: logger)
    monkeypatch.setattr(runtime_preflight, 'StartupTimeline', lambda _logger, _title: timeline)
    prepare_localizations = AsyncMock()
    monkeypatch.setattr(runtime_preflight, 'prepare_localizations', prepare_localizations)
    metadata = [('k', 'v')]
    monkeypatch.setattr(runtime_preflight, '_build_preflight_banner_metadata', lambda: metadata)

    result = await runtime_preflight.prepare_runtime_preflight()

    configure_runtime_logging.assert_awaited_once_with('file_formatter', 'console_formatter')
    timeline.log_banner.assert_called_once_with(metadata)
    prepare_localizations.assert_awaited_once_with(timeline, logger)
    assert result.logger is logger
    assert result.timeline is timeline
    assert result.telegram_notifier is telegram_notifier
