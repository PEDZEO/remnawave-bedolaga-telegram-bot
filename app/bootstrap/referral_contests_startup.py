from app.services.referral_contest_service import referral_contest_service
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def initialize_referral_contests_stage(timeline: StartupTimeline, logger: LoggerLike) -> None:
    async with timeline.stage(
        'Реферальные конкурсы',
        '🏆',
        success_message='Сервис конкурсов готов',
    ) as stage:
        try:
            await referral_contest_service.start()
            if referral_contest_service.is_running():
                stage.log('Автосводки по конкурсам запущены')
            else:
                stage.skip('Сервис конкурсов выключен настройками')
        except Exception as error:
            stage.warning(f'Ошибка запуска сервиса конкурсов: {error}')
            logger.error('❌ Ошибка запуска сервиса конкурсов', error=error)
