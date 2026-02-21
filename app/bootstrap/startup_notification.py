async def send_startup_notification_safe(logger, bot):
    try:
        from app.services.startup_notification_service import send_bot_startup_notification

        await send_bot_startup_notification(bot)
    except Exception as startup_notify_error:
        logger.warning('Не удалось отправить стартовое уведомление', startup_notify_error=startup_notify_error)
