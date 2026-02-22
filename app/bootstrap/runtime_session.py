from app.bootstrap.runtime_orchestration import run_startup_and_runtime_loop
from app.bootstrap.runtime_preflight import RuntimePreflightContext
from app.bootstrap.runtime_state import RuntimeState
from app.bootstrap.shutdown_pipeline import run_shutdown_pipeline
from app.bootstrap.signals import install_signal_handlers


async def _finalize_runtime_session_shutdown(state: RuntimeState, timeline, logger) -> None:
    state.summary_logged = await run_shutdown_pipeline(
        timeline,
        logger,
        summary_logged=state.summary_logged,
        **state.build_shutdown_payload(),
    )


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
        await _finalize_runtime_session_shutdown(state, timeline, logger)
