from app.config import settings


async def configure_telegram_webhook_stage(timeline, bot, dp, telegram_webhook_enabled: bool):
    async with timeline.stage(
        'Telegram webhook',
        '🤖',
        success_message='Telegram webhook настроен',
    ) as stage:
        if telegram_webhook_enabled:
            webhook_url = settings.get_telegram_webhook_url()
            if not webhook_url:
                stage.warning('WEBHOOK_URL не задан, пропускаем настройку webhook')
            else:
                allowed_updates = dp.resolve_used_update_types()
                await bot.set_webhook(
                    url=webhook_url,
                    secret_token=settings.WEBHOOK_SECRET_TOKEN,
                    drop_pending_updates=False,  # Обрабатываем накопившиеся обновления
                    allowed_updates=allowed_updates,
                )
                stage.log(f'Webhook установлен: {webhook_url}')
                stage.log(f'Allowed updates: {", ".join(sorted(allowed_updates)) if allowed_updates else "all"}')
                stage.success('Telegram webhook активен')
        else:
            stage.skip('Режим webhook отключен')
