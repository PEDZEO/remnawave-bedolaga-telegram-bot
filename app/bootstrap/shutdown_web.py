from aiogram import Bot

from app.bootstrap.types import LoggerLike, WebAPIServerLike


async def _safe_web_shutdown_call(
    logger: LoggerLike,
    *,
    success_message: str,
    error_message: str,
    shutdown_call,
) -> None:
    try:
        await shutdown_call()
        logger.info(success_message)
    except Exception as error:
        logger.error(error_message, error=error)


async def shutdown_web_runtime(
    logger: LoggerLike,
    *,
    bot: Bot | None,
    web_api_server: WebAPIServerLike | None,
    telegram_webhook_enabled: bool,
) -> None:
    if telegram_webhook_enabled and bot is not None:
        logger.info('ℹ️ Снятие Telegram webhook...')
        await _safe_web_shutdown_call(
            logger,
            success_message='✅ Telegram webhook удалён',
            error_message='Ошибка удаления Telegram webhook',
            shutdown_call=lambda: bot.delete_webhook(drop_pending_updates=False),
        )

    if web_api_server:
        await _safe_web_shutdown_call(
            logger,
            success_message='✅ Административное веб-API остановлено',
            error_message='Ошибка остановки веб-API',
            shutdown_call=web_api_server.stop,
        )

    if bot is not None:
        await _safe_web_shutdown_call(
            logger,
            success_message='✅ Сессия бота закрыта',
            error_message='Ошибка закрытия сессии бота',
            shutdown_call=bot.session.close,
        )
