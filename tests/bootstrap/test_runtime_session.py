from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


# Prevent heavy import chain through runtime_orchestration -> core_runtime_startup -> aiogram redis storage.
if 'app.bootstrap.runtime_orchestration' not in sys.modules:
    runtime_orchestration_stub = types.ModuleType('app.bootstrap.runtime_orchestration')

    async def _run_startup_and_runtime_loop(*_args, **_kwargs):
        return None

    runtime_orchestration_stub.run_startup_and_runtime_loop = _run_startup_and_runtime_loop
    sys.modules['app.bootstrap.runtime_orchestration'] = runtime_orchestration_stub

from app.bootstrap import runtime_session


@pytest.mark.asyncio
async def test_run_runtime_session_always_runs_shutdown_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = MagicMock()
    timeline = MagicMock()
    preflight = SimpleNamespace(
        logger=logger,
        timeline=timeline,
        telegram_notifier=MagicMock(),
    )
    fake_killer = MagicMock()
    fake_state = MagicMock()
    fake_state.summary_logged = False
    fake_state.build_shutdown_payload.return_value = {
        'monitoring_task': None,
        'maintenance_task': None,
        'version_check_task': None,
        'traffic_monitoring_task': None,
        'daily_subscription_task': None,
        'polling_task': None,
        'dp': None,
        'bot': None,
        'web_api_server': None,
        'telegram_webhook_enabled': False,
    }

    monkeypatch.setattr(runtime_session, 'install_signal_handlers', lambda: fake_killer)
    monkeypatch.setattr(runtime_session, 'RuntimeState', lambda: fake_state)
    monkeypatch.setattr(
        runtime_session,
        'run_startup_and_runtime_loop',
        AsyncMock(side_effect=RuntimeError('boom')),
    )
    run_shutdown_pipeline_mock = AsyncMock(return_value=True)
    monkeypatch.setattr(runtime_session, 'run_shutdown_pipeline', run_shutdown_pipeline_mock)

    with pytest.raises(RuntimeError, match='boom'):
        await runtime_session.run_runtime_session(preflight)

    logger.error.assert_called_once()
    run_shutdown_pipeline_mock.assert_awaited_once_with(
        timeline,
        logger,
        summary_logged=False,
        monitoring_task=None,
        maintenance_task=None,
        version_check_task=None,
        traffic_monitoring_task=None,
        daily_subscription_task=None,
        polling_task=None,
        dp=None,
        bot=None,
        web_api_server=None,
        telegram_webhook_enabled=False,
    )
    assert fake_state.summary_logged is True
