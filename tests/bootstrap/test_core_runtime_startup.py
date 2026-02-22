from __future__ import annotations

import sys
import types
from unittest.mock import AsyncMock, MagicMock

import pytest


# Prevent heavy aiogram/redis import chain from app.bootstrap.bot_startup during module import.
if 'app.bootstrap.bot_startup' not in sys.modules:
    bot_startup_stub = types.ModuleType('app.bootstrap.bot_startup')

    async def _setup_bot_stage(*_args, **_kwargs):
        return MagicMock(), MagicMock()

    bot_startup_stub.setup_bot_stage = _setup_bot_stage
    sys.modules['app.bootstrap.bot_startup'] = bot_startup_stub


@pytest.mark.asyncio
async def test_start_core_runtime_stage_propagates_runtime_mode_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.bootstrap import core_runtime_startup as startup

    timeline = MagicMock()
    logger = MagicMock()
    telegram_notifier = MagicMock()
    bot = MagicMock()
    dp = MagicMock()
    payment_service = MagicMock()
    web_api_server = MagicMock()

    monkeypatch.setattr(startup, 'run_database_migration_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_database_stage', AsyncMock())
    monkeypatch.setattr(startup, 'sync_tariffs_stage', AsyncMock())
    monkeypatch.setattr(startup, 'sync_servers_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_payment_methods_stage', AsyncMock())
    monkeypatch.setattr(startup, 'load_bot_configuration_stage', AsyncMock())
    monkeypatch.setattr(startup, 'setup_bot_stage', AsyncMock(return_value=(bot, dp)))
    monkeypatch.setattr(startup, 'wire_core_services', MagicMock())
    monkeypatch.setattr(startup, 'connect_integration_services_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_backup_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_reporting_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_referral_contests_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_contest_rotation_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_log_rotation_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_remnawave_sync_stage', AsyncMock())
    monkeypatch.setattr(startup, 'setup_payment_runtime', lambda _bot: payment_service)
    monkeypatch.setattr(
        startup,
        'initialize_payment_verification_stage',
        AsyncMock(return_value=(['provider-1'], True)),
    )
    monkeypatch.setattr(startup, 'start_nalogo_queue_stage', AsyncMock())
    monkeypatch.setattr(startup, 'initialize_external_admin_stage', AsyncMock())
    monkeypatch.setattr(
        startup,
        'resolve_runtime_mode',
        lambda: (False, True, False),
    )
    start_web_server_stage = AsyncMock(return_value=(None, web_api_server))
    monkeypatch.setattr(startup, 'start_web_server_stage', start_web_server_stage)
    configure_telegram_webhook_stage = AsyncMock()
    monkeypatch.setattr(startup, 'configure_telegram_webhook_stage', configure_telegram_webhook_stage)
    monkeypatch.setattr(startup, 'settings', types.SimpleNamespace(is_log_rotation_enabled=lambda: True))

    result = await startup.start_core_runtime_stage(timeline, logger, telegram_notifier)

    assert result.bot is bot
    assert result.dp is dp
    assert result.payment_service is payment_service
    assert result.verification_providers == ['provider-1']
    assert result.auto_verification_active is True
    assert result.polling_enabled is False
    assert result.telegram_webhook_enabled is True
    assert result.web_api_server is web_api_server

    start_web_server_stage.assert_awaited_once_with(
        timeline,
        bot,
        dp,
        payment_service,
        telegram_webhook_enabled=True,
        payment_webhooks_enabled=False,
    )
    configure_telegram_webhook_stage.assert_awaited_once_with(
        timeline,
        bot,
        dp,
        telegram_webhook_enabled=True,
    )
