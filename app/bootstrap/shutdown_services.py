import asyncio
from typing import Any

from app.config import settings
from app.services.backup_service import backup_service
from app.services.contest_rotation_service import contest_rotation_service
from app.services.daily_subscription_service import daily_subscription_service
from app.services.log_rotation_service import log_rotation_service
from app.services.maintenance_service import maintenance_service
from app.services.monitoring_service import monitoring_service
from app.services.nalogo_queue_service import nalogo_queue_service
from app.services.payment_verification_service import auto_payment_verification_service
from app.services.referral_contest_service import referral_contest_service
from app.services.remnawave_sync_service import remnawave_sync_service
from app.services.reporting_service import reporting_service
from app.services.traffic_monitoring_service import traffic_monitoring_scheduler


async def _cancel_task_if_running(task: asyncio.Task | None) -> None:
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def shutdown_runtime_services(
    logger: Any,
    *,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
) -> None:
    logger.info('ℹ️ Остановка сервиса автопроверки пополнений...')
    try:
        await auto_payment_verification_service.stop()
    except Exception as error:
        logger.error('Ошибка остановки сервиса автопроверки пополнений', error=error)

    if monitoring_task and not monitoring_task.done():
        logger.info('ℹ️ Остановка службы мониторинга...')
        monitoring_service.stop_monitoring()
    await _cancel_task_if_running(monitoring_task)

    if maintenance_task and not maintenance_task.done():
        logger.info('ℹ️ Остановка службы техработ...')
        await maintenance_service.stop_monitoring()
    await _cancel_task_if_running(maintenance_task)

    if version_check_task and not version_check_task.done():
        logger.info('ℹ️ Остановка сервиса проверки версий...')
    await _cancel_task_if_running(version_check_task)

    if traffic_monitoring_task and not traffic_monitoring_task.done():
        logger.info('ℹ️ Остановка мониторинга трафика...')
        traffic_monitoring_scheduler.stop_monitoring()
    await _cancel_task_if_running(traffic_monitoring_task)

    if daily_subscription_task and not daily_subscription_task.done():
        logger.info('ℹ️ Остановка сервиса суточных подписок...')
        daily_subscription_service.stop_monitoring()
    await _cancel_task_if_running(daily_subscription_task)

    logger.info('ℹ️ Остановка сервиса отчетов...')
    try:
        await reporting_service.stop()
    except Exception as error:
        logger.error('Ошибка остановки сервиса отчетов', error=error)

    logger.info('ℹ️ Остановка сервиса конкурсов...')
    try:
        await referral_contest_service.stop()
    except Exception as error:
        logger.error('Ошибка остановки сервиса конкурсов', error=error)

    logger.info('ℹ️ Остановка сервиса автосинхронизации RemnaWave...')
    try:
        await remnawave_sync_service.stop()
    except Exception as error:
        logger.error('Ошибка остановки автосинхронизации RemnaWave', error=error)

    logger.info('ℹ️ Остановка ротации игр...')
    try:
        await contest_rotation_service.stop()
    except Exception as error:
        logger.error('Ошибка остановки ротации игр', error=error)

    if settings.is_log_rotation_enabled():
        logger.info('ℹ️ Остановка сервиса ротации логов...')
        try:
            await log_rotation_service.stop()
        except Exception as error:
            logger.error('Ошибка остановки сервиса ротации логов', error=error)

    logger.info('ℹ️ Остановка очереди чеков NaloGO...')
    try:
        await nalogo_queue_service.stop()
    except Exception as error:
        logger.error('Ошибка остановки очереди чеков NaloGO', error=error)

    logger.info('ℹ️ Остановка сервиса бекапов...')
    try:
        await backup_service.stop_auto_backup()
    except Exception as error:
        logger.error('Ошибка остановки сервиса бекапов', error=error)

    if polling_task and not polling_task.done():
        logger.info('ℹ️ Остановка polling...')
    await _cancel_task_if_running(polling_task)
