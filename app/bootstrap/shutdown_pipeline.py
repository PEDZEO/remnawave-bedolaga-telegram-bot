import asyncio

from aiogram import Bot, Dispatcher

from app.bootstrap.shutdown_services import shutdown_runtime_services
from app.bootstrap.shutdown_web import shutdown_web_runtime
from app.bootstrap.types import LoggerLike, WebAPIServerLike
from app.utils.startup_timeline import StartupTimeline


async def _run_runtime_shutdown_stage(
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
    await shutdown_runtime_services(
        logger,
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        version_check_task=version_check_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        polling_task=polling_task,
        dp=dp,
    )


async def _run_web_shutdown_stage(
    logger: LoggerLike,
    *,
    bot: Bot | None,
    web_api_server: WebAPIServerLike | None,
    telegram_webhook_enabled: bool,
) -> None:
    await shutdown_web_runtime(
        logger,
        bot=bot,
        web_api_server=web_api_server,
        telegram_webhook_enabled=telegram_webhook_enabled,
    )


def _build_runtime_shutdown_kwargs(
    *,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
    dp: Dispatcher | None,
) -> dict[str, object]:
    return {
        'monitoring_task': monitoring_task,
        'maintenance_task': maintenance_task,
        'version_check_task': version_check_task,
        'traffic_monitoring_task': traffic_monitoring_task,
        'daily_subscription_task': daily_subscription_task,
        'polling_task': polling_task,
        'dp': dp,
    }


def _build_web_shutdown_kwargs(
    *,
    bot: Bot | None,
    web_api_server: WebAPIServerLike | None,
    telegram_webhook_enabled: bool,
) -> dict[str, object]:
    return {
        'bot': bot,
        'web_api_server': web_api_server,
        'telegram_webhook_enabled': telegram_webhook_enabled,
    }


async def run_shutdown_pipeline(
    timeline: StartupTimeline,
    logger: LoggerLike,
    *,
    summary_logged: bool,
    monitoring_task: asyncio.Task | None,
    maintenance_task: asyncio.Task | None,
    version_check_task: asyncio.Task | None,
    traffic_monitoring_task: asyncio.Task | None,
    daily_subscription_task: asyncio.Task | None,
    polling_task: asyncio.Task | None,
    dp: Dispatcher | None,
    bot: Bot | None,
    web_api_server: WebAPIServerLike | None,
    telegram_webhook_enabled: bool,
) -> bool:
    if not summary_logged:
        timeline.log_summary()
        summary_logged = True

    logger.info('🛑 Начинается корректное завершение работы...')

    await _run_runtime_shutdown_stage(
        logger,
        **_build_runtime_shutdown_kwargs(
            monitoring_task=monitoring_task,
            maintenance_task=maintenance_task,
            version_check_task=version_check_task,
            traffic_monitoring_task=traffic_monitoring_task,
            daily_subscription_task=daily_subscription_task,
            polling_task=polling_task,
            dp=dp,
        ),
    )
    await _run_web_shutdown_stage(
        logger,
        **_build_web_shutdown_kwargs(
            bot=bot,
            web_api_server=web_api_server,
            telegram_webhook_enabled=telegram_webhook_enabled,
        ),
    )

    logger.info('✅ Завершение работы бота завершено')
    return summary_logged
