import asyncio


async def start_polling_stage(timeline, dp, bot, polling_enabled: bool):
    async with timeline.stage(
        'Запуск polling',
        '🤖',
        success_message='Aiogram polling запущен',
    ) as stage:
        if polling_enabled:
            polling_task = asyncio.create_task(dp.start_polling(bot, skip_updates=False))
            stage.log('skip_updates=False — накопившиеся обновления будут обработаны')
            return polling_task

        stage.skip('Polling отключен режимом работы')
        return None
