from aiogram import Bot

from app.services.backup_service import backup_service
from app.utils.startup_timeline import StartupTimeline

from .startup_error_helpers import warn_startup_stage_error
from .types import LoggerLike


async def initialize_backup_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    bot: Bot,
) -> None:
    async with timeline.stage(
        'Сервис бекапов',
        '🗄️',
        success_message='Сервис бекапов инициализирован',
    ) as stage:
        try:
            backup_service.bot = bot
            settings_obj = await backup_service.get_backup_settings()
            if settings_obj.auto_backup_enabled:
                await backup_service.start_auto_backup()
                stage.log(
                    'Автобекапы включены: интервал '
                    f'{settings_obj.backup_interval_hours}ч, запуск {settings_obj.backup_time}'
                )
            else:
                stage.log('Автобекапы отключены настройками')
            stage.success('Сервис бекапов инициализирован')
        except Exception as error:
            warn_startup_stage_error(
                stage=stage,
                logger=logger,
                stage_error_message='Ошибка инициализации сервиса бекапов',
                logger_error_message='❌ Ошибка инициализации сервиса бекапов',
                error=error,
            )
