from aiogram import Bot

from app.bootstrap.types import LoggerLike, WebAPIServerLike


async def shutdown_web_runtime(
    logger: LoggerLike,
    *,
    bot: Bot | None,
    web_api_server: WebAPIServerLike | None,
    telegram_webhook_enabled: bool,
) -> None:
    if telegram_webhook_enabled and bot is not None:
        logger.info('ℹ️ Снятие Telegram webhook...')
        try:
            await bot.delete_webhook(drop_pending_updates=False)
            logger.info('✅ Telegram webhook удалён')
        except Exception as error:
            logger.error('Ошибка удаления Telegram webhook', error=error)

    if web_api_server:
        try:
            await web_api_server.stop()
            logger.info('✅ Административное веб-API остановлено')
        except Exception as error:
            logger.error('Ошибка остановки веб-API', error=error)

    if bot is not None:
        try:
            await bot.session.close()
            logger.info('✅ Сессия бота закрыта')
        except Exception as error:
            logger.error('Ошибка закрытия сессии бота', error=error)
