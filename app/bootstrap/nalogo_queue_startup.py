from app.config import settings
from app.services.nalogo_queue_service import nalogo_queue_service
from app.services.payment_service import PaymentService
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def start_nalogo_queue_stage(
    timeline: StartupTimeline,
    logger: LoggerLike,
    payment_service: PaymentService,
) -> None:
    async with timeline.stage(
        'Очередь чеков NaloGO',
        '🧾',
        success_message='Сервис очереди чеков запущен',
    ) as stage:
        if settings.is_nalogo_enabled():
            try:
                await nalogo_queue_service.start()
                if nalogo_queue_service.is_running():
                    queue_len = await payment_service.nalogo_service.get_queue_length()
                    if queue_len > 0:
                        stage.log(f'В очереди ожидает {queue_len} чек(ов)')
                    stage.success('Фоновая обработка чеков активна')
                else:
                    stage.skip('Сервис не запущен')
            except Exception as error:
                stage.warning(f'Ошибка запуска очереди чеков: {error}')
                logger.error('❌ Ошибка запуска очереди чеков NaloGO', error=error)
        else:
            stage.skip('NaloGO отключен настройками')
