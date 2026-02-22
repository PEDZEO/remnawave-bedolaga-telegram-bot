from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.bootstrap.startup_finalize import finalize_startup_stage


@pytest.mark.asyncio
async def test_finalize_startup_stage_logs_summary_and_sends_notification(monkeypatch: pytest.MonkeyPatch) -> None:
    log_summary = MagicMock()
    send_startup_notification = AsyncMock()
    monkeypatch.setattr('app.bootstrap.startup_finalize.log_startup_summary', log_summary)
    monkeypatch.setattr(
        'app.bootstrap.startup_finalize.send_startup_notification_safe',
        send_startup_notification,
    )

    timeline = MagicMock()
    logger = MagicMock()
    bot = MagicMock()
    monitoring_task = MagicMock()
    maintenance_task = MagicMock()
    traffic_monitoring_task = MagicMock()
    daily_subscription_task = MagicMock()
    version_check_task = MagicMock()
    verification_providers = ['provider-a']

    await finalize_startup_stage(
        timeline,
        logger,
        bot=bot,
        telegram_webhook_enabled=True,
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        version_check_task=version_check_task,
        verification_providers=verification_providers,
    )

    log_summary.assert_called_once_with(
        timeline,
        telegram_webhook_enabled=True,
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        version_check_task=version_check_task,
        verification_providers=verification_providers,
    )
    send_startup_notification.assert_awaited_once_with(logger, bot)
