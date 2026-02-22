import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from aiogram import Bot, Dispatcher

from app.bootstrap.daily_subscription_startup import start_daily_subscription_stage
from app.bootstrap.maintenance_startup import start_maintenance_stage
from app.bootstrap.monitoring_startup import start_monitoring_stage
from app.bootstrap.polling_startup import start_polling_stage
from app.bootstrap.traffic_monitoring_startup import start_traffic_monitoring_stage
from app.bootstrap.version_check_startup import start_version_check_stage
from app.utils.startup_timeline import StartupTimeline


@dataclass
class RuntimeStartupTasks:
    monitoring_task: asyncio.Task | None
    maintenance_task: asyncio.Task | None
    traffic_monitoring_task: asyncio.Task | None
    daily_subscription_task: asyncio.Task | None
    version_check_task: asyncio.Task | None
    polling_task: asyncio.Task | None


async def _start_stage_task(
    stage_startup: Callable[..., Awaitable[asyncio.Task | None]],
    *args: Any,
    **kwargs: Any,
) -> asyncio.Task | None:
    return await stage_startup(*args, **kwargs)


async def start_runtime_tasks_stage(
    timeline: StartupTimeline,
    *,
    dp: Dispatcher,
    bot: Bot,
    polling_enabled: bool,
) -> RuntimeStartupTasks:
    monitoring_task = await _start_stage_task(start_monitoring_stage, timeline)
    maintenance_task = await _start_stage_task(start_maintenance_stage, timeline)
    traffic_monitoring_task = await _start_stage_task(start_traffic_monitoring_stage, timeline)
    daily_subscription_task = await _start_stage_task(start_daily_subscription_stage, timeline)
    version_check_task = await _start_stage_task(start_version_check_stage, timeline)
    polling_task = await _start_stage_task(start_polling_stage, timeline, dp, bot, polling_enabled=polling_enabled)

    return RuntimeStartupTasks(
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        version_check_task=version_check_task,
        polling_task=polling_task,
    )
