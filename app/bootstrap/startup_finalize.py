import asyncio
from typing import TypedDict

from aiogram import Bot

from app.bootstrap.startup_notification import send_startup_notification_safe
from app.bootstrap.startup_summary import log_startup_summary
from app.bootstrap.types import LoggerLike
from app.utils.startup_timeline import StartupTimeline


class StartupSummaryPayload(TypedDict):
    telegram_webhook_enabled: bool
    monitoring_task: asyncio.Task | None
    maintenance_task: asyncio.Task | None
    traffic_monitoring_task: asyncio.Task | None
    daily_subscription_task: asyncio.Task | None
    version_check_task: asyncio.Task | None
    verification_providers: list[str]


def _build_startup_summary_payload(
    *,
    telegram_webhook_enabled: bool,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    verification_providers: list[str],
) -> StartupSummaryPayload:
    return {
        'telegram_webhook_enabled': telegram_webhook_enabled,
        'monitoring_task': monitoring_task,
        'maintenance_task': maintenance_task,
        'traffic_monitoring_task': traffic_monitoring_task,
        'daily_subscription_task': daily_subscription_task,
        'version_check_task': version_check_task,
        'verification_providers': verification_providers,
    }


async def finalize_startup_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    *,
    bot: Bot,
    telegram_webhook_enabled: bool,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    verification_providers: list[str],
) -> None:
    summary_payload = _build_startup_summary_payload(
        telegram_webhook_enabled=telegram_webhook_enabled,
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        version_check_task=version_check_task,
        verification_providers=verification_providers,
    )
    log_startup_summary(timeline, **summary_payload)
    await send_startup_notification_safe(logger, bot)
