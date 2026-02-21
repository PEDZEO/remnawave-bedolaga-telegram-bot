from app.bootstrap.runtime_orchestration import run_startup_and_runtime_loop
from app.bootstrap.runtime_preflight import RuntimePreflightContext
from app.bootstrap.runtime_state import RuntimeState
from app.bootstrap.shutdown_pipeline import run_shutdown_pipeline
from app.bootstrap.signals import install_signal_handlers


async def run_runtime_session(preflight: RuntimePreflightContext) -> None:
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
    except Exception as error:
        logger.error('❌ Критическая ошибка при запуске', error=error)
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
