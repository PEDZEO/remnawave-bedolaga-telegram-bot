from app.bootstrap.runtime_watchdog import RuntimeTasks, run_runtime_watchdog_loop


async def run_runtime_loop_stage(
    killer,
    logger,
    *,
    monitoring_task,
    maintenance_task,
    version_check_task,
    traffic_monitoring_task,
    daily_subscription_task,
    polling_task,
    auto_verification_active: bool,
):
    runtime_tasks = RuntimeTasks(
        monitoring_task=monitoring_task,
        maintenance_task=maintenance_task,
        version_check_task=version_check_task,
        traffic_monitoring_task=traffic_monitoring_task,
        daily_subscription_task=daily_subscription_task,
        polling_task=polling_task,
    )
    try:
        return await run_runtime_watchdog_loop(
            killer,
            logger,
            runtime_tasks,
            auto_verification_active,
        )
    except Exception as error:
        logger.error('Ошибка в основном цикле', error=error)
        return runtime_tasks, auto_verification_active
