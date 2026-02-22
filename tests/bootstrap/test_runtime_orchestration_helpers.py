from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


# Avoid importing heavy startup graph for this isolated helper test.
if 'app.bootstrap.core_runtime_startup' not in sys.modules:
    core_runtime_stub = types.ModuleType('app.bootstrap.core_runtime_startup')

    async def _start_core_runtime_stage(*_args, **_kwargs):
        return SimpleNamespace()

    core_runtime_stub.start_core_runtime_stage = _start_core_runtime_stage
    sys.modules['app.bootstrap.core_runtime_startup'] = core_runtime_stub

from app.bootstrap import runtime_orchestration


@pytest.mark.asyncio
async def test_start_and_apply_runtime_tasks_calls_startup_and_updates_state(monkeypatch: pytest.MonkeyPatch) -> None:
    timeline = MagicMock()
    runtime_tasks = SimpleNamespace(
        monitoring_task=object(),
        maintenance_task=object(),
        version_check_task=object(),
        traffic_monitoring_task=object(),
        daily_subscription_task=object(),
        polling_task=object(),
    )
    start_runtime_tasks = AsyncMock(return_value=runtime_tasks)
    monkeypatch.setattr(runtime_orchestration, 'start_runtime_tasks_stage', start_runtime_tasks)

    state = MagicMock()
    state.dp = object()
    state.bot = object()
    state.polling_enabled = False

    await runtime_orchestration._start_and_apply_runtime_tasks(timeline, state)

    start_runtime_tasks.assert_awaited_once_with(
        timeline,
        dp=state.dp,
        bot=state.bot,
        polling_enabled=False,
    )
    state.apply_runtime_tasks.assert_called_once_with(runtime_tasks)


@pytest.mark.asyncio
async def test_run_runtime_loop_and_apply_results_updates_state(monkeypatch: pytest.MonkeyPatch) -> None:
    killer = MagicMock()
    logger = MagicMock()
    runtime_tasks = SimpleNamespace(
        monitoring_task=object(),
        maintenance_task=object(),
        version_check_task=object(),
        traffic_monitoring_task=object(),
        daily_subscription_task=object(),
        polling_task=object(),
    )
    run_runtime_loop = AsyncMock(return_value=(runtime_tasks, False))
    monkeypatch.setattr(runtime_orchestration, 'run_runtime_loop_stage', run_runtime_loop)

    state = MagicMock()
    state.monitoring_task = object()
    state.maintenance_task = object()
    state.version_check_task = object()
    state.traffic_monitoring_task = object()
    state.daily_subscription_task = object()
    state.polling_task = object()
    state.auto_verification_active = True

    await runtime_orchestration._run_runtime_loop_and_apply_results(killer, logger, state)

    run_runtime_loop.assert_awaited_once_with(
        killer,
        logger,
        monitoring_task=state.monitoring_task,
        maintenance_task=state.maintenance_task,
        version_check_task=state.version_check_task,
        traffic_monitoring_task=state.traffic_monitoring_task,
        daily_subscription_task=state.daily_subscription_task,
        polling_task=state.polling_task,
        auto_verification_active=True,
    )
    assert state.auto_verification_active is False
    state.apply_runtime_tasks.assert_called_once_with(runtime_tasks)


def test_build_startup_finalize_kwargs_maps_runtime_state_fields() -> None:
    state = MagicMock()
    state.bot = object()
    state.telegram_webhook_enabled = True
    state.monitoring_task = object()
    state.maintenance_task = object()
    state.traffic_monitoring_task = object()
    state.daily_subscription_task = object()
    state.version_check_task = object()
    state.verification_providers = ['provider-a']

    kwargs = runtime_orchestration._build_startup_finalize_kwargs(state)

    assert kwargs == {
        'bot': state.bot,
        'telegram_webhook_enabled': True,
        'monitoring_task': state.monitoring_task,
        'maintenance_task': state.maintenance_task,
        'traffic_monitoring_task': state.traffic_monitoring_task,
        'daily_subscription_task': state.daily_subscription_task,
        'version_check_task': state.version_check_task,
        'verification_providers': ['provider-a'],
    }
