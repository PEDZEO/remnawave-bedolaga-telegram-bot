from aiogram import Bot

from app.services.external_admin_service import ensure_external_admin_token
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def initialize_external_admin_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    bot: Bot,
) -> None:
    async with timeline.stage(
        'Внешняя админка',
        '🛡️',
        success_message='Токен внешней админки готов',
    ) as stage:
        try:
            bot_user = await bot.get_me()
            token = await ensure_external_admin_token(
                bot_user.username,
                bot_user.id,
            )
            if token:
                stage.log('Токен синхронизирован')
            else:
                stage.warning('Не удалось получить токен внешней админки')
        except Exception as error:  # pragma: no cover - защитный блок
            stage.warning(f'Ошибка подготовки внешней админки: {error}')
            logger.error('❌ Ошибка подготовки внешней админки', error=error)
