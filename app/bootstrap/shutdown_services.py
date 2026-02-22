import asyncio
import inspect
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import Dispatcher

from app.bootstrap.types import LoggerLike
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


async def _safe_shutdown_call(
    logger: LoggerLike,
    *,
    info_message: str,
    error_message: str,
    shutdown_call: Callable[[], Awaitable[Any] | Any],
) -> None:
    logger.info(info_message)
    try:
        result = shutdown_call()
        if inspect.isawaitable(result):
            await result
    except Exception as error:
        logger.error(error_message, error=error)


async def shutdown_runtime_services(
    logger: LoggerLike,
    *,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
    dp: Dispatcher | None,
) -> None:
    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка сервиса автопроверки пополнений...',
        error_message='Ошибка остановки сервиса автопроверки пополнений',
        shutdown_call=auto_payment_verification_service.stop,
    )

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

    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка сервиса отчетов...',
        error_message='Ошибка остановки сервиса отчетов',
        shutdown_call=reporting_service.stop,
    )
    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка сервиса конкурсов...',
        error_message='Ошибка остановки сервиса конкурсов',
        shutdown_call=referral_contest_service.stop,
    )
    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка сервиса автосинхронизации RemnaWave...',
        error_message='Ошибка остановки автосинхронизации RemnaWave',
        shutdown_call=remnawave_sync_service.stop,
    )
    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка ротации игр...',
        error_message='Ошибка остановки ротации игр',
        shutdown_call=contest_rotation_service.stop,
    )

    if settings.is_log_rotation_enabled():
        await _safe_shutdown_call(
            logger,
            info_message='ℹ️ Остановка сервиса ротации логов...',
            error_message='Ошибка остановки сервиса ротации логов',
            shutdown_call=log_rotation_service.stop,
        )

    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка очереди чеков NaloGO...',
        error_message='Ошибка остановки очереди чеков NaloGO',
        shutdown_call=nalogo_queue_service.stop,
    )
    await _safe_shutdown_call(
        logger,
        info_message='ℹ️ Остановка сервиса бекапов...',
        error_message='Ошибка остановки сервиса бекапов',
        shutdown_call=backup_service.stop_auto_backup,
    )

    if polling_task and not polling_task.done():
        logger.info('ℹ️ Остановка polling...')
        if dp is not None:
            try:
                await dp.stop_polling()
            except Exception as error:
                logger.error('Ошибка корректной остановки polling', error=error)
    await _cancel_task_if_running(polling_task)
