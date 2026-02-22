from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap.runtime_execution import run_runtime_loop_stage
from app.bootstrap.runtime_tasks_startup import start_runtime_tasks_stage
from app.bootstrap.shutdown_pipeline import run_shutdown_pipeline


@pytest.mark.asyncio
async def test_start_runtime_tasks_stage_wires_all_startups(monkeypatch):
    call_order: list[str] = []

    monitoring_task = object()
    maintenance_task = object()
    traffic_task = object()
    daily_task = object()
    version_task = object()
    polling_task = object()

    async def _start_monitoring(*_args, **_kwargs):
        call_order.append('monitoring')
        return monitoring_task

    async def _start_maintenance(*_args, **_kwargs):
        call_order.append('maintenance')
        return maintenance_task

    async def _start_traffic(*_args, **_kwargs):
        call_order.append('traffic')
        return traffic_task

    async def _start_daily(*_args, **_kwargs):
        call_order.append('daily')
        return daily_task

    async def _start_version(*_args, **_kwargs):
        call_order.append('version')
        return version_task

    async def _start_polling(*_args, **_kwargs):
        call_order.append('polling')
        return polling_task

    start_monitoring = AsyncMock(side_effect=_start_monitoring)
    start_maintenance = AsyncMock(side_effect=_start_maintenance)
    start_traffic = AsyncMock(side_effect=_start_traffic)
    start_daily = AsyncMock(side_effect=_start_daily)
    start_version = AsyncMock(side_effect=_start_version)
    start_polling = AsyncMock(side_effect=_start_polling)

    monkeypatch.setattr('app.bootstrap.runtime_tasks_startup.start_monitoring_stage', start_monitoring)
    monkeypatch.setattr('app.bootstrap.runtime_tasks_startup.start_maintenance_stage', start_maintenance)
    monkeypatch.setattr('app.bootstrap.runtime_tasks_startup.start_traffic_monitoring_stage', start_traffic)
    monkeypatch.setattr('app.bootstrap.runtime_tasks_startup.start_daily_subscription_stage', start_daily)
    monkeypatch.setattr('app.bootstrap.runtime_tasks_startup.start_version_check_stage', start_version)
    monkeypatch.setattr('app.bootstrap.runtime_tasks_startup.start_polling_stage', start_polling)

    timeline = MagicMock()
    dp = MagicMock()
    bot = MagicMock()

    result = await start_runtime_tasks_stage(timeline, dp=dp, bot=bot, polling_enabled=False)

    assert result.monitoring_task is monitoring_task
    assert result.maintenance_task is maintenance_task
    assert result.traffic_monitoring_task is traffic_task
    assert result.daily_subscription_task is daily_task
    assert result.version_check_task is version_task
    assert result.polling_task is polling_task

    start_monitoring.assert_awaited_once_with(timeline)
    start_maintenance.assert_awaited_once_with(timeline)
    start_traffic.assert_awaited_once_with(timeline)
    start_daily.assert_awaited_once_with(timeline)
    start_version.assert_awaited_once_with(timeline)
    start_polling.assert_awaited_once_with(timeline, dp, bot, polling_enabled=False)
    assert call_order == ['monitoring', 'maintenance', 'traffic', 'daily', 'version', 'polling']


@pytest.mark.asyncio
async def test_run_runtime_loop_stage_returns_previous_state_on_error(monkeypatch):
    watchdog_mock = AsyncMock(side_effect=RuntimeError('boom'))
    monkeypatch.setattr('app.bootstrap.runtime_execution.run_runtime_watchdog_loop', watchdog_mock)

    logger = MagicMock()
    killer = MagicMock()
    killer.exit = False

    runtime_tasks, auto_verification_active = await run_runtime_loop_stage(
        killer,
        logger,
        monitoring_task=None,
        maintenance_task=None,
        version_check_task=None,
        traffic_monitoring_task=None,
        daily_subscription_task=None,
        polling_task=None,
        auto_verification_active=True,
    )

    assert runtime_tasks.monitoring_task is None
    assert runtime_tasks.polling_task is None
    assert auto_verification_active is True
    logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_run_shutdown_pipeline_calls_shutdown_stages(monkeypatch):
    shutdown_runtime = AsyncMock()
    shutdown_web = AsyncMock()
    monkeypatch.setattr('app.bootstrap.shutdown_pipeline.shutdown_runtime_services', shutdown_runtime)
    monkeypatch.setattr('app.bootstrap.shutdown_pipeline.shutdown_web_runtime', shutdown_web)

    timeline = MagicMock()
    logger = MagicMock()

    result = await run_shutdown_pipeline(
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

    assert result is True
    timeline.log_summary.assert_called_once()
    shutdown_runtime.assert_awaited_once()
    shutdown_web.assert_awaited_once()
