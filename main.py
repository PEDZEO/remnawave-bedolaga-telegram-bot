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
from app.bootstrap.runtime_state import RuntimeState
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
    state = RuntimeState()

    try:
        runtime_context = await start_core_runtime_stage(timeline, logger, telegram_notifier)
        state.apply_core_runtime(runtime_context)

        runtime_startup_tasks = await start_runtime_tasks_stage(
            timeline,
            dp=state.dp,
            bot=state.bot,
            polling_enabled=state.polling_enabled,
        )
        state.apply_runtime_tasks(runtime_startup_tasks)

        await finalize_startup_stage(
            timeline,
            logger,
            bot=state.bot,
            telegram_webhook_enabled=state.telegram_webhook_enabled,
            monitoring_task=state.monitoring_task,
            maintenance_task=state.maintenance_task,
            traffic_monitoring_task=state.traffic_monitoring_task,
            daily_subscription_task=state.daily_subscription_task,
            version_check_task=state.version_check_task,
            verification_providers=state.verification_providers,
        )
        state.summary_logged = True

        runtime_tasks, state.auto_verification_active = await run_runtime_loop_stage(
            killer,
            logger,
            monitoring_task=state.monitoring_task,
            maintenance_task=state.maintenance_task,
            version_check_task=state.version_check_task,
            traffic_monitoring_task=state.traffic_monitoring_task,
            daily_subscription_task=state.daily_subscription_task,
            polling_task=state.polling_task,
            auto_verification_active=state.auto_verification_active,
        )
        state.apply_runtime_tasks(runtime_tasks)

    except Exception as e:
        logger.error('❌ Критическая ошибка при запуске', error=e)
        raise

    finally:
        state.summary_logged = await run_shutdown_pipeline(
            timeline,
            logger,
            summary_logged=state.summary_logged,
            monitoring_task=state.monitoring_task,
            maintenance_task=state.maintenance_task,
            version_check_task=state.version_check_task,
            traffic_monitoring_task=state.traffic_monitoring_task,
            daily_subscription_task=state.daily_subscription_task,
            polling_task=state.polling_task,
            bot=state.bot,
            web_api_server=state.web_api_server,
            telegram_webhook_enabled=state.telegram_webhook_enabled,
        )


if __name__ == '__main__':
    run_main_entrypoint(main, send_crash_notification_on_error)
