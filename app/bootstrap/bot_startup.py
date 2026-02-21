from aiogram import Bot, Dispatcher

from app.bot import setup_bot
from app.utils.startup_timeline import StartupTimeline


async def setup_bot_stage(timeline: StartupTimeline) -> tuple[Bot, Dispatcher]:
    async with timeline.stage('Настройка бота', '🤖', success_message='Бот настроен') as stage:
        bot, dp = await setup_bot()
        stage.log('Кеш и FSM подготовлены')
        return bot, dp
