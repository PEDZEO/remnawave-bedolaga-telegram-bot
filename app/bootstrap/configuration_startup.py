from app.services.system_settings_service import bot_configuration_service
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def load_bot_configuration_stage(timeline: StartupTimeline, logger: LoggerLike) -> None:
    async with timeline.stage(
        'Загрузка конфигурации из БД',
        '⚙️',
        success_message='Конфигурация загружена',
    ) as stage:
        try:
            await bot_configuration_service.initialize()
        except Exception as error:
            stage.warning(f'Не удалось загрузить конфигурацию: {error}')
            logger.error('❌ Не удалось загрузить конфигурацию', error=error)
