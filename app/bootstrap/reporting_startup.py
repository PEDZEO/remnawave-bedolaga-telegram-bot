from aiogram import Bot

from app.services.reporting_service import reporting_service
from app.utils.startup_timeline import StartupTimeline

from .startup_error_helpers import warn_startup_stage_error
from .types import LoggerLike


async def initialize_reporting_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    bot: Bot,
) -> None:
    async with timeline.stage(
        'Сервис отчетов',
        '📊',
        success_message='Сервис отчетов готов',
    ) as stage:
        try:
            reporting_service.set_bot(bot)
            await reporting_service.start()
        except Exception as error:
            warn_startup_stage_error(
                stage=stage,
                logger=logger,
                stage_error_message='Ошибка запуска сервиса отчетов',
                logger_error_message='❌ Ошибка запуска сервиса отчетов',
                error=error,
            )
