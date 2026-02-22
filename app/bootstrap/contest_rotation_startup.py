from aiogram import Bot

from app.services.contest_rotation_service import contest_rotation_service
from app.utils.startup_timeline import StartupTimeline

from .startup_error_helpers import warn_startup_stage_error
from .types import LoggerLike


async def initialize_contest_rotation_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    bot: Bot,
) -> None:
    async with timeline.stage(
        'Ротация игр',
        '🎲',
        success_message='Мини-игры готовы',
    ) as stage:
        try:
            contest_rotation_service.set_bot(bot)
            await contest_rotation_service.start()
            if contest_rotation_service.is_running():
                stage.log('Ротационные игры запущены')
            else:
                stage.skip('Ротация игр выключена настройками')
        except Exception as error:
            warn_startup_stage_error(
                stage=stage,
                logger=logger,
                stage_error_message='Ошибка запуска ротации игр',
                logger_error_message='❌ Ошибка запуска ротации игр',
                error=error,
            )
