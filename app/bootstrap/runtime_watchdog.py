import asyncio
from dataclasses import dataclass

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


async def run_runtime_watchdog_loop(killer, logger, tasks: RuntimeTasks, auto_verification_active: bool):
    while not killer.exit:
        await asyncio.sleep(1)

        if tasks.monitoring_task and tasks.monitoring_task.done():
            exception = tasks.monitoring_task.exception()
            if exception:
                logger.error('Служба мониторинга завершилась с ошибкой', error=exception)
                tasks.monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())

        if tasks.maintenance_task and tasks.maintenance_task.done():
            exception = tasks.maintenance_task.exception()
            if exception:
                logger.error('Служба техработ завершилась с ошибкой', error=exception)
                tasks.maintenance_task = asyncio.create_task(maintenance_service.start_monitoring())

        if tasks.version_check_task and tasks.version_check_task.done():
            exception = tasks.version_check_task.exception()
            if exception:
                logger.error('Сервис проверки версий завершился с ошибкой', error=exception)
                if settings.is_version_check_enabled():
                    logger.info('🔄 Перезапуск сервиса проверки версий...')
                    tasks.version_check_task = asyncio.create_task(version_service.start_periodic_check())

        if tasks.traffic_monitoring_task and tasks.traffic_monitoring_task.done():
            exception = tasks.traffic_monitoring_task.exception()
            if exception:
                logger.error('Мониторинг трафика завершился с ошибкой', error=exception)
                if traffic_monitoring_scheduler.is_enabled():
                    logger.info('🔄 Перезапуск мониторинга трафика...')
                    tasks.traffic_monitoring_task = asyncio.create_task(traffic_monitoring_scheduler.start_monitoring())

        if tasks.daily_subscription_task and tasks.daily_subscription_task.done():
            exception = tasks.daily_subscription_task.exception()
            if exception:
                logger.error('Сервис суточных подписок завершился с ошибкой', error=exception)
                if daily_subscription_service.is_enabled():
                    logger.info('🔄 Перезапуск сервиса суточных подписок...')
                    tasks.daily_subscription_task = asyncio.create_task(daily_subscription_service.start_monitoring())

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
