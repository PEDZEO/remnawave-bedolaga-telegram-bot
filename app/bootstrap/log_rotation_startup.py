from datetime import datetime

from aiogram import Bot

from app.services.log_rotation_service import log_rotation_service
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def initialize_log_rotation_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    bot: Bot,
) -> None:
    async with timeline.stage(
        'Ротация логов',
        '📋',
        success_message='Сервис ротации логов готов',
    ) as stage:
        try:
            log_rotation_service.set_bot(bot)
            await log_rotation_service.start()
            status = log_rotation_service.get_status()
            stage.log(f'Время ротации: {status.rotation_time}')
            stage.log(f'Хранение архивов: {status.keep_days} дней')
            if status.send_to_telegram:
                stage.log('Отправка в Telegram: включена')
            if status.next_rotation:
                next_dt = datetime.fromisoformat(status.next_rotation)
                stage.log(f'Следующая ротация: {next_dt.strftime("%d.%m.%Y %H:%M")}')
        except Exception as error:
            stage.warning(f'Ошибка запуска сервиса ротации логов: {error}')
            logger.error('❌ Ошибка запуска сервиса ротации логов', error=error)
