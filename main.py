import asyncio
import sys
from pathlib import Path

import structlog


sys.path.append(str(Path(__file__).parent))

from app.bootstrap.backup_startup import initialize_backup_stage
from app.bootstrap.bot_startup import setup_bot_stage
from app.bootstrap.configuration_startup import load_bot_configuration_stage
from app.bootstrap.contest_rotation_startup import initialize_contest_rotation_stage
from app.bootstrap.daily_subscription_startup import start_daily_subscription_stage
from app.bootstrap.database_initialization import initialize_database_stage
from app.bootstrap.database_startup import run_database_migration_stage
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
from app.bootstrap.runtime_logging import configure_runtime_logging
from app.bootstrap.runtime_mode import resolve_runtime_mode
from app.bootstrap.runtime_watchdog import RuntimeTasks, run_runtime_watchdog_loop
from app.bootstrap.servers_startup import sync_servers_stage
from app.bootstrap.services_startup import connect_integration_services_stage, wire_core_services
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
from app.services.backup_service import backup_service
from app.services.contest_rotation_service import contest_rotation_service
from app.services.daily_subscription_service import daily_subscription_service
from app.services.log_rotation_service import log_rotation_service
from app.services.maintenance_service import maintenance_service
from app.services.monitoring_service import monitoring_service
from app.services.nalogo_queue_service import nalogo_queue_service
from app.services.payment_verification_service import (
    auto_payment_verification_service,
)
from app.services.referral_contest_service import referral_contest_service
from app.services.remnawave_sync_service import remnawave_sync_service
from app.services.reporting_service import reporting_service
from app.services.traffic_monitoring_service import traffic_monitoring_scheduler
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

        try:
            runtime_tasks = RuntimeTasks(
                monitoring_task=monitoring_task,
                maintenance_task=maintenance_task,
                version_check_task=version_check_task,
                traffic_monitoring_task=traffic_monitoring_task,
                daily_subscription_task=daily_subscription_task,
                polling_task=polling_task,
            )
            runtime_tasks, auto_verification_active = await run_runtime_watchdog_loop(
                killer,
                logger,
                runtime_tasks,
                auto_verification_active,
            )
            monitoring_task = runtime_tasks.monitoring_task
            maintenance_task = runtime_tasks.maintenance_task
            version_check_task = runtime_tasks.version_check_task
            traffic_monitoring_task = runtime_tasks.traffic_monitoring_task
            daily_subscription_task = runtime_tasks.daily_subscription_task
            polling_task = runtime_tasks.polling_task
        except Exception as e:
            logger.error('Ошибка в основном цикле', error=e)

    except Exception as e:
        logger.error('❌ Критическая ошибка при запуске', error=e)
        raise

    finally:
        if not summary_logged:
            timeline.log_summary()
            summary_logged = True
        logger.info('🛑 Начинается корректное завершение работы...')

        logger.info('ℹ️ Остановка сервиса автопроверки пополнений...')
        try:
            await auto_payment_verification_service.stop()
        except Exception as error:
            logger.error('Ошибка остановки сервиса автопроверки пополнений', error=error)

        if monitoring_task and not monitoring_task.done():
            logger.info('ℹ️ Остановка службы мониторинга...')
            monitoring_service.stop_monitoring()
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

        if maintenance_task and not maintenance_task.done():
            logger.info('ℹ️ Остановка службы техработ...')
            await maintenance_service.stop_monitoring()
            maintenance_task.cancel()
            try:
                await maintenance_task
            except asyncio.CancelledError:
                pass

        if version_check_task and not version_check_task.done():
            logger.info('ℹ️ Остановка сервиса проверки версий...')
            version_check_task.cancel()
            try:
                await version_check_task
            except asyncio.CancelledError:
                pass

        if traffic_monitoring_task and not traffic_monitoring_task.done():
            logger.info('ℹ️ Остановка мониторинга трафика...')
            traffic_monitoring_scheduler.stop_monitoring()
            traffic_monitoring_task.cancel()
            try:
                await traffic_monitoring_task
            except asyncio.CancelledError:
                pass

        if daily_subscription_task and not daily_subscription_task.done():
            logger.info('ℹ️ Остановка сервиса суточных подписок...')
            daily_subscription_service.stop_monitoring()
            daily_subscription_task.cancel()
            try:
                await daily_subscription_task
            except asyncio.CancelledError:
                pass

        logger.info('ℹ️ Остановка сервиса отчетов...')
        try:
            await reporting_service.stop()
        except Exception as e:
            logger.error('Ошибка остановки сервиса отчетов', error=e)

        logger.info('ℹ️ Остановка сервиса конкурсов...')
        try:
            await referral_contest_service.stop()
        except Exception as e:
            logger.error('Ошибка остановки сервиса конкурсов', error=e)

        logger.info('ℹ️ Остановка сервиса автосинхронизации RemnaWave...')
        try:
            await remnawave_sync_service.stop()
        except Exception as e:
            logger.error('Ошибка остановки автосинхронизации RemnaWave', error=e)

        logger.info('ℹ️ Остановка ротации игр...')
        try:
            await contest_rotation_service.stop()
        except Exception as e:
            logger.error('Ошибка остановки ротации игр', error=e)

        if settings.is_log_rotation_enabled():
            logger.info('ℹ️ Остановка сервиса ротации логов...')
            try:
                await log_rotation_service.stop()
            except Exception as e:
                logger.error('Ошибка остановки сервиса ротации логов', error=e)

        logger.info('ℹ️ Остановка очереди чеков NaloGO...')
        try:
            await nalogo_queue_service.stop()
        except Exception as e:
            logger.error('Ошибка остановки очереди чеков NaloGO', error=e)

        logger.info('ℹ️ Остановка сервиса бекапов...')
        try:
            await backup_service.stop_auto_backup()
        except Exception as e:
            logger.error('Ошибка остановки сервиса бекапов', error=e)

        if polling_task and not polling_task.done():
            logger.info('ℹ️ Остановка polling...')
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass

        if telegram_webhook_enabled and 'bot' in locals():
            logger.info('ℹ️ Снятие Telegram webhook...')
            try:
                await bot.delete_webhook(drop_pending_updates=False)
                logger.info('✅ Telegram webhook удалён')
            except Exception as error:
                logger.error('Ошибка удаления Telegram webhook', error=error)

        if web_api_server:
            try:
                await web_api_server.stop()
                logger.info('✅ Административное веб-API остановлено')
            except Exception as error:
                logger.error('Ошибка остановки веб-API', error=error)

        if 'bot' in locals():
            try:
                await bot.session.close()
                logger.info('✅ Сессия бота закрыта')
            except Exception as e:
                logger.error('Ошибка закрытия сессии бота', error=e)

        logger.info('✅ Завершение работы бота завершено')


async def _send_crash_notification_on_error(error: Exception) -> None:
    """Отправляет уведомление о падении бота в админский чат."""
    import traceback

    from app.config import settings

    if not getattr(settings, 'BOT_TOKEN', None):
        return

    try:
        from aiogram import Bot

        from app.services.startup_notification_service import send_crash_notification

        bot = Bot(token=settings.BOT_TOKEN)
        try:
            traceback_str = traceback.format_exc()
            await send_crash_notification(bot, error, traceback_str)
        finally:
            await bot.session.close()
    except Exception as notify_error:
        print(f'⚠️ Не удалось отправить уведомление о падении: {notify_error}')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n🛑 Бот остановлен пользователем')
    except Exception as e:
        print(f'❌ Критическая ошибка: {e}')
        import traceback

        traceback.print_exc()
        # Пытаемся отправить уведомление о падении
        try:
            asyncio.run(_send_crash_notification_on_error(e))
        except Exception:
            pass
        sys.exit(1)
