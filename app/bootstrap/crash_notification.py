import traceback

from app.config import settings


async def send_crash_notification_on_error(error: Exception) -> None:
    """Отправляет уведомление о падении бота в админский чат."""
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
