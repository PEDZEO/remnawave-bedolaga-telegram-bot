import sys
from pathlib import Path

import structlog


sys.path.append(str(Path(__file__).parent))

from app.bootstrap.backup_startup import initialize_backup_stage
from app.bootstrap.bot_startup import setup_bot_stage
from app.bootstrap.configuration_startup import load_bot_configuration_stage
from app.bootstrap.contest_rotation_startup import initialize_contest_rotation_stage
from app.bootstrap.crash_notification import send_crash_notification_on_error
from app.bootstrap.daily_subscription_startup import start_daily_subscription_stage
from app.bootstrap.database_initialization import initialize_database_stage
from app.bootstrap.database_startup import run_database_migration_stage
from app.bootstrap.entrypoint import run_main_entrypoint
from app.bootstrap.external_admin_startup import initialize_external_admin_stage
from app.bootstrap.localization_startup import prepare_localizations
from app.bootstrap.log_rotation_startup import initialize_log_rotation_stage
from app.bootstrap.maintenance_startup import start_maintenance_stage
from app.bootstrap.monitoring_startup import start_monitoring_stage
from app.bootstrap.nalogo_queue_startup import start_nalogo_queue_stage
from app.bootstrap.payment_methods_startup import initialize_payment_methods_stage
from app.bootstrap.payment_runtime import setup_payment_runtime
from app.bootstrap.payment_verification_startup import initialize_payment_verification_stage
from app.bootstrap.polling_startup import start_polling_stage
from app.bootstrap.referral_contests_startup import initialize_referral_contests_stage
from app.bootstrap.remnawave_sync_startup import initialize_remnawave_sync_stage
from app.bootstrap.reporting_startup import initialize_reporting_stage
from app.bootstrap.runtime_execution import run_runtime_loop_stage
from app.bootstrap.runtime_logging import configure_runtime_logging
from app.bootstrap.runtime_mode import resolve_runtime_mode
from app.bootstrap.servers_startup import sync_servers_stage
from app.bootstrap.services_startup import connect_integration_services_stage, wire_core_services
from app.bootstrap.shutdown_services import shutdown_runtime_services
from app.bootstrap.shutdown_web import shutdown_web_runtime
from app.bootstrap.signals import install_signal_handlers
from app.bootstrap.startup_notification import send_startup_notification_safe
from app.bootstrap.startup_summary import log_startup_summary
from app.bootstrap.tariffs_startup import sync_tariffs_stage
from app.bootstrap.telegram_webhook_startup import configure_telegram_webhook_stage
from app.bootstrap.traffic_monitoring_startup import start_traffic_monitoring_stage
from app.bootstrap.version_check_startup import start_version_check_stage
from app.bootstrap.web_server_startup import start_web_server_stage
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

    web_app = None
    monitoring_task = None
    maintenance_task = None
    version_check_task = None
    traffic_monitoring_task = None
    daily_subscription_task = None
    polling_task = None
    web_api_server = None
    telegram_webhook_enabled = False
    polling_enabled = True
    payment_webhooks_enabled = False

    summary_logged = False

    try:
        await run_database_migration_stage(timeline, logger)
        await initialize_database_stage(timeline)

        await sync_tariffs_stage(timeline, logger)

        await sync_servers_stage(timeline, logger)

        await initialize_payment_methods_stage(timeline, logger)

        await load_bot_configuration_stage(timeline, logger)

        bot = None
        dp = None
        bot, dp = await setup_bot_stage(timeline)

        wire_core_services(bot, telegram_notifier)
        await connect_integration_services_stage(timeline, bot)

        await initialize_backup_stage(timeline, logger, bot)

        await initialize_reporting_stage(timeline, logger, bot)

        await initialize_referral_contests_stage(timeline, logger)

        await initialize_contest_rotation_stage(timeline, logger, bot)

        if settings.is_log_rotation_enabled():
            await initialize_log_rotation_stage(timeline, logger, bot)

        await initialize_remnawave_sync_stage(timeline, logger)

        payment_service = setup_payment_runtime(bot)

        verification_providers, auto_verification_active = await initialize_payment_verification_stage(timeline)

        await start_nalogo_queue_stage(timeline, logger, payment_service)

        await initialize_external_admin_stage(timeline, logger, bot)

        polling_enabled, telegram_webhook_enabled, payment_webhooks_enabled = resolve_runtime_mode()

        web_app, web_api_server = await start_web_server_stage(
            timeline,
            bot,
            dp,
            payment_service,
            telegram_webhook_enabled=telegram_webhook_enabled,
            payment_webhooks_enabled=payment_webhooks_enabled,
        )

        await configure_telegram_webhook_stage(
            timeline,
            bot,
            dp,
            telegram_webhook_enabled=telegram_webhook_enabled,
        )

        monitoring_task = await start_monitoring_stage(timeline)

        maintenance_task = await start_maintenance_stage(timeline)

        traffic_monitoring_task = await start_traffic_monitoring_stage(timeline)

        daily_subscription_task = await start_daily_subscription_stage(timeline)

        version_check_task = await start_version_check_stage(timeline)

        polling_task = await start_polling_stage(timeline, dp, bot, polling_enabled=polling_enabled)

        log_startup_summary(
            timeline,
            telegram_webhook_enabled=telegram_webhook_enabled,
            monitoring_task=monitoring_task,
            maintenance_task=maintenance_task,
            traffic_monitoring_task=traffic_monitoring_task,
            daily_subscription_task=daily_subscription_task,
            version_check_task=version_check_task,
            verification_providers=verification_providers,
        )
        summary_logged = True

        await send_startup_notification_safe(logger, bot)

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
        if not summary_logged:
            timeline.log_summary()
            summary_logged = True
        logger.info('🛑 Начинается корректное завершение работы...')

        await shutdown_runtime_services(
            logger,
            monitoring_task=monitoring_task,
            maintenance_task=maintenance_task,
            version_check_task=version_check_task,
            traffic_monitoring_task=traffic_monitoring_task,
            daily_subscription_task=daily_subscription_task,
            polling_task=polling_task,
        )

        await shutdown_web_runtime(
            logger,
            bot=bot if 'bot' in locals() else None,
            web_api_server=web_api_server,
            telegram_webhook_enabled=telegram_webhook_enabled,
        )

        logger.info('✅ Завершение работы бота завершено')


if __name__ == '__main__':
    run_main_entrypoint(main, send_crash_notification_on_error)
