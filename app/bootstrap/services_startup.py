from aiogram import Bot

from app.services.ban_notification_service import ban_notification_service
from app.services.broadcast_service import broadcast_service
from app.services.daily_subscription_service import daily_subscription_service
from app.services.maintenance_service import maintenance_service
from app.services.monitoring_service import monitoring_service
from app.services.referral_contest_service import referral_contest_service
from app.services.traffic_monitoring_service import traffic_monitoring_scheduler
from app.services.version_service import version_service
from app.utils.startup_timeline import StartupTimeline

from .types import TelegramNotifierLike


def wire_core_services(bot: Bot, telegram_notifier: TelegramNotifierLike) -> None:
    monitoring_service.bot = bot
    maintenance_service.set_bot(bot)
    broadcast_service.set_bot(bot)
    ban_notification_service.set_bot(bot)
    traffic_monitoring_scheduler.set_bot(bot)
    daily_subscription_service.set_bot(bot)
    telegram_notifier.set_bot(bot)

    from app.cabinet.services.email_service import email_service
    from app.services.broadcast_service import email_broadcast_service

    email_broadcast_service.set_email_service(email_service)


async def connect_integration_services_stage(timeline: StartupTimeline, bot: Bot) -> None:
    from app.services.admin_notification_service import AdminNotificationService

    async with timeline.stage(
        'Интеграция сервисов',
        '🔗',
        success_message='Сервисы подключены',
    ) as stage:
        admin_notification_service = AdminNotificationService(bot)
        version_service.bot = bot
        version_service.set_notification_service(admin_notification_service)
        referral_contest_service.set_bot(bot)
        stage.log(f'Репозиторий версий: {version_service.repo}')
        stage.log(f'Текущая версия: {version_service.current_version}')
        stage.success('Мониторинг, уведомления и рассылки подключены')
