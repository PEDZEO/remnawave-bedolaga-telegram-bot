from app.bootstrap.shutdown_services import shutdown_runtime_services
from app.bootstrap.shutdown_web import shutdown_web_runtime


async def run_shutdown_pipeline(
    timeline,
    logger,
    *,
    summary_logged: bool,
    monitoring_task,
    maintenance_task,
    version_check_task,
    traffic_monitoring_task,
    daily_subscription_task,
    polling_task,
    bot,
    web_api_server,
    telegram_webhook_enabled: bool,
) -> bool:
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
        bot=bot,
        web_api_server=web_api_server,
        telegram_webhook_enabled=telegram_webhook_enabled,
    )

    logger.info('✅ Завершение работы бота завершено')
    return summary_logged
