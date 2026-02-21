async def shutdown_web_runtime(logger, *, bot, web_api_server, telegram_webhook_enabled: bool):
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
