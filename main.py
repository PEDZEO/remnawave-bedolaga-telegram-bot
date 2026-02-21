import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent))

from app.bootstrap.crash_notification import send_crash_notification_on_error
from app.bootstrap.entrypoint import run_main_entrypoint
from app.bootstrap.runtime_orchestration import run_startup_and_runtime_loop
from app.bootstrap.runtime_preflight import prepare_runtime_preflight
from app.bootstrap.runtime_state import RuntimeState
from app.bootstrap.shutdown_pipeline import run_shutdown_pipeline
from app.bootstrap.signals import install_signal_handlers


async def main():
    preflight = await prepare_runtime_preflight()
    logger = preflight.logger
    timeline = preflight.timeline

    killer = install_signal_handlers()
    state = RuntimeState()

    try:
        await run_startup_and_runtime_loop(
            timeline,
            logger,
            killer,
            state,
            preflight.telegram_notifier,
        )

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
