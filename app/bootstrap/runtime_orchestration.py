from app.bootstrap.core_runtime_startup import start_core_runtime_stage
from app.bootstrap.runtime_execution import run_runtime_loop_stage
from app.bootstrap.runtime_state import RuntimeState
from app.bootstrap.runtime_tasks_startup import start_runtime_tasks_stage
from app.bootstrap.startup_finalize import finalize_startup_stage


async def run_startup_and_runtime_loop(
    timeline,
    logger,
    killer,
    state: RuntimeState,
    telegram_notifier,
) -> None:
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
