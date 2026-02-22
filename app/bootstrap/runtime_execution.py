import asyncio

from app.bootstrap.runtime_watchdog import RuntimeTasks, run_runtime_watchdog_loop
from app.bootstrap.types import KillerLike, LoggerLike


def _build_runtime_tasks(
    *,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
) -> RuntimeTasks:
    return RuntimeTasks(
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        version_check_task=version_check_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        polling_task=polling_task,
    )


async def run_runtime_loop_stage(
    killer: KillerLike,
    logger: LoggerLike,
    *,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
    auto_verification_active: bool,
) -> tuple[RuntimeTasks, bool]:
    runtime_tasks = _build_runtime_tasks(
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        version_check_task=version_check_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        polling_task=polling_task,
    )
    try:
        return await run_runtime_watchdog_loop(
            killer,
            logger,
            runtime_tasks,
            auto_verification_active,
        )
    except Exception as error:
        logger.error('Ошибка в основном цикле', error=error)
        return runtime_tasks, auto_verification_active
