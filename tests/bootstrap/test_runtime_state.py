from __future__ import annotations

from types import SimpleNamespace

from app.bootstrap.runtime_state import RuntimeState


def test_runtime_state_build_shutdown_payload_contains_expected_fields() -> None:
    state = RuntimeState()
    monitoring_task = object()
    maintenance_task = object()
    version_check_task = object()
    traffic_monitoring_task = object()
    daily_subscription_task = object()
    polling_task = object()
    dp = object()
    bot = object()
    web_api_server = object()

    state.monitoring_task = monitoring_task
    state.maintenance_task = maintenance_task
    state.version_check_task = version_check_task
    state.traffic_monitoring_task = traffic_monitoring_task
    state.daily_subscription_task = daily_subscription_task
    state.polling_task = polling_task
    state.dp = dp
    state.bot = bot
    state.web_api_server = web_api_server
    state.telegram_webhook_enabled = True

    payload = state.build_shutdown_payload()

    assert payload == {
        'monitoring_task': monitoring_task,
        'maintenance_task': maintenance_task,
        'version_check_task': version_check_task,
        'traffic_monitoring_task': traffic_monitoring_task,
        'daily_subscription_task': daily_subscription_task,
        'polling_task': polling_task,
        'dp': dp,
        'bot': bot,
        'web_api_server': web_api_server,
        'telegram_webhook_enabled': True,
    }


def test_runtime_state_apply_methods_update_state_fields() -> None:
    state = RuntimeState()
    core_runtime = SimpleNamespace(
        bot='bot',
        dp='dp',
        verification_providers=['p1'],
        auto_verification_active=True,
        polling_enabled=False,
        telegram_webhook_enabled=True,
        web_api_server='api',
    )
    runtime_tasks = SimpleNamespace(
        monitoring_task='m',
        maintenance_task='maint',
        traffic_monitoring_task='traffic',
        daily_subscription_task='daily',
        version_check_task='version',
        polling_task='polling',
    )

    state.apply_core_runtime(core_runtime)
    state.apply_runtime_tasks(runtime_tasks)

    assert state.bot == 'bot'
    assert state.dp == 'dp'
    assert state.verification_providers == ['p1']
    assert state.auto_verification_active is True
    assert state.polling_enabled is False
    assert state.telegram_webhook_enabled is True
    assert state.web_api_server == 'api'
    assert state.monitoring_task == 'm'
    assert state.maintenance_task == 'maint'
    assert state.traffic_monitoring_task == 'traffic'
    assert state.daily_subscription_task == 'daily'
    assert state.version_check_task == 'version'
    assert state.polling_task == 'polling'
