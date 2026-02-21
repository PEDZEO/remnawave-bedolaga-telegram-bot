import sys
from pathlib import Path

import structlog


sys.path.append(str(Path(__file__).parent))

from app.bootstrap.core_runtime_startup import start_core_runtime_stage
from app.bootstrap.crash_notification import send_crash_notification_on_error
from app.bootstrap.entrypoint import run_main_entrypoint
from app.bootstrap.localization_startup import prepare_localizations
from app.bootstrap.runtime_execution import run_runtime_loop_stage
from app.bootstrap.runtime_logging import configure_runtime_logging
from app.bootstrap.runtime_tasks_startup import start_runtime_tasks_stage
from app.bootstrap.shutdown_pipeline import run_shutdown_pipeline
from app.bootstrap.signals import install_signal_handlers
from app.bootstrap.startup_finalize import finalize_startup_stage
from app.config import settings
from app.logging_config import setup_logging
from app.utils.startup_timeline import StartupTimeline


async def main():
    file_formatter, console_formatter, telegram_notifier = setup_logging()
    await configure_runtime_logging(file_formatter, console_formatter)

    # NOTE: TelegramNotifierProcessor and noisy logger suppression are
    # handled inside setup_logging() / logging_config.py.

    logger = structlog.get_logger(__name__)
    timeline = StartupTimeline(logger, 'Bedolaga Remnawave Bot')
    timeline.log_banner(
        [
            ('Уровень логирования', settings.LOG_LEVEL),
            ('Режим БД', settings.DATABASE_MODE),
        ]
    )

    await prepare_localizations(timeline, logger)

    killer = install_signal_handlers()

    bot = None
    dp = None
    monitoring_task = None
    maintenance_task = None
    version_check_task = None
    traffic_monitoring_task = None
    daily_subscription_task = None
    polling_task = None
    web_api_server = None
    telegram_webhook_enabled = False
    polling_enabled = True

    summary_logged = False

    try:
        runtime_context = await start_core_runtime_stage(timeline, logger, telegram_notifier)
        bot = runtime_context.bot
        dp = runtime_context.dp
        verification_providers = runtime_context.verification_providers
        auto_verification_active = runtime_context.auto_verification_active
        polling_enabled = runtime_context.polling_enabled
        telegram_webhook_enabled = runtime_context.telegram_webhook_enabled
        web_api_server = runtime_context.web_api_server

        runtime_startup_tasks = await start_runtime_tasks_stage(
            timeline,
            dp=dp,
            bot=bot,
            polling_enabled=polling_enabled,
        )
        monitoring_task = runtime_startup_tasks.monitoring_task
        maintenance_task = runtime_startup_tasks.maintenance_task
        traffic_monitoring_task = runtime_startup_tasks.traffic_monitoring_task
        daily_subscription_task = runtime_startup_tasks.daily_subscription_task
        version_check_task = runtime_startup_tasks.version_check_task
        polling_task = runtime_startup_tasks.polling_task

        await finalize_startup_stage(
            timeline,
            logger,
            bot=bot,
            telegram_webhook_enabled=telegram_webhook_enabled,
            monitoring_task=monitoring_task,
            maintenance_task=maintenance_task,
            traffic_monitoring_task=traffic_monitoring_task,
            daily_subscription_task=daily_subscription_task,
            version_check_task=version_check_task,
            verification_providers=verification_providers,
        )
        summary_logged = True

        runtime_tasks, auto_verification_active = await run_runtime_loop_stage(
            killer,
            logger,
            monitoring_task=monitoring_task,
            maintenance_task=maintenance_task,
            version_check_task=version_check_task,
            traffic_monitoring_task=traffic_monitoring_task,
            daily_subscription_task=daily_subscription_task,
            polling_task=polling_task,
            auto_verification_active=auto_verification_active,
        )
        monitoring_task = runtime_tasks.monitoring_task
        maintenance_task = runtime_tasks.maintenance_task
        version_check_task = runtime_tasks.version_check_task
        traffic_monitoring_task = runtime_tasks.traffic_monitoring_task
        daily_subscription_task = runtime_tasks.daily_subscription_task
        polling_task = runtime_tasks.polling_task

    except Exception as e:
        logger.error('❌ Критическая ошибка при запуске', error=e)
        raise

    finally:
        summary_logged = await run_shutdown_pipeline(
            timeline,
            logger,
            summary_logged=summary_logged,
            monitoring_task=monitoring_task,
            maintenance_task=maintenance_task,
            version_check_task=version_check_task,
            traffic_monitoring_task=traffic_monitoring_task,
            daily_subscription_task=daily_subscription_task,
            polling_task=polling_task,
            bot=bot,
            web_api_server=web_api_server,
            telegram_webhook_enabled=telegram_webhook_enabled,
        )


if __name__ == '__main__':
    run_main_entrypoint(main, send_crash_notification_on_error)
