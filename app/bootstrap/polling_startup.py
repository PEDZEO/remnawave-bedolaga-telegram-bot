import asyncio

from aiogram import Bot, Dispatcher

from app.utils.startup_timeline import StartupTimeline


async def start_polling_stage(
    timeline: StartupTimeline,
    dp: Dispatcher,
    bot: Bot,
    polling_enabled: bool,
) -> asyncio.Task | None:
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
