import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.bootstrap.types import KillerLike, LoggerLike
from app.config import settings
from app.services.daily_subscription_service import daily_subscription_service
from app.services.maintenance_service import maintenance_service
from app.services.monitoring_service import monitoring_service
from app.services.payment_verification_service import auto_payment_verification_service
from app.services.traffic_monitoring_service import traffic_monitoring_scheduler
from app.services.version_service import version_service


@dataclass
class RuntimeTasks:
    monitoring_task: asyncio.Task | None
    maintenance_task: asyncio.Task | None
    version_check_task: asyncio.Task | None
    traffic_monitoring_task: asyncio.Task | None
    daily_subscription_task: asyncio.Task | None
    polling_task: asyncio.Task | None


def _restart_task_on_exception(
    logger: LoggerLike,
    task: asyncio.Task | None,
    *,
    error_message: str,
    restart_factory: Callable[[], Awaitable[None]] | None = None,
    restart_message: str | None = None,
    restart_condition: Callable[[], bool] | None = None,
) -> asyncio.Task | None:
    if task is None or not task.done():
        return task

    exception = task.exception()
    if exception is None:
        return task

    logger.error(error_message, error=exception)
    if restart_factory is None:
        return task

    if restart_condition is not None and not restart_condition():
        return task

    if restart_message is not None:
        logger.info(restart_message)
    return asyncio.create_task(restart_factory())


async def run_runtime_watchdog_loop(
    killer: KillerLike,
    logger: LoggerLike,
    tasks: RuntimeTasks,
    auto_verification_active: bool,
) -> tuple[RuntimeTasks, bool]:
    while not killer.exit:
        await asyncio.sleep(1)

        tasks.monitoring_task = _restart_task_on_exception(
            logger,
            tasks.monitoring_task,
            error_message='Служба мониторинга завершилась с ошибкой',
            restart_factory=monitoring_service.start_monitoring,
        )
        tasks.maintenance_task = _restart_task_on_exception(
            logger,
            tasks.maintenance_task,
            error_message='Служба техработ завершилась с ошибкой',
            restart_factory=maintenance_service.start_monitoring,
        )
        tasks.version_check_task = _restart_task_on_exception(
            logger,
            tasks.version_check_task,
            error_message='Сервис проверки версий завершился с ошибкой',
            restart_factory=version_service.start_periodic_check,
            restart_message='🔄 Перезапуск сервиса проверки версий...',
            restart_condition=settings.is_version_check_enabled,
        )
        tasks.traffic_monitoring_task = _restart_task_on_exception(
            logger,
            tasks.traffic_monitoring_task,
            error_message='Мониторинг трафика завершился с ошибкой',
            restart_factory=traffic_monitoring_scheduler.start_monitoring,
            restart_message='🔄 Перезапуск мониторинга трафика...',
            restart_condition=traffic_monitoring_scheduler.is_enabled,
        )
        tasks.daily_subscription_task = _restart_task_on_exception(
            logger,
            tasks.daily_subscription_task,
            error_message='Сервис суточных подписок завершился с ошибкой',
            restart_factory=daily_subscription_service.start_monitoring,
            restart_message='🔄 Перезапуск сервиса суточных подписок...',
            restart_condition=daily_subscription_service.is_enabled,
        )

        if auto_verification_active and not auto_payment_verification_service.is_running():
            logger.warning('Сервис автопроверки пополнений остановился, пробуем перезапустить...')
            await auto_payment_verification_service.start()
            auto_verification_active = auto_payment_verification_service.is_running()

        if tasks.polling_task and tasks.polling_task.done():
            exception = tasks.polling_task.exception()
            if exception:
                logger.error('Polling завершился с ошибкой', error=exception)
                break

    return tasks, auto_verification_active
