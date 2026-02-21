from app.bootstrap.startup_notification import send_startup_notification_safe
from app.bootstrap.startup_summary import log_startup_summary


async def finalize_startup_stage(
    timeline,
    logger,
    *,
    bot,
    telegram_webhook_enabled: bool,
    monitoring_task,
    maintenance_task,
    traffic_monitoring_task,
    daily_subscription_task,
    version_check_task,
    verification_providers: list[str],
) -> None:
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
    await send_startup_notification_safe(logger, bot)
