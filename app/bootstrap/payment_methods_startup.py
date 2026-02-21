from app.database.database import AsyncSessionLocal
from app.services.payment_method_config_service import ensure_payment_method_configs
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def initialize_payment_methods_stage(timeline: StartupTimeline, logger: LoggerLike) -> None:
    async with timeline.stage(
        'Инициализация платёжных методов',
        '💳',
        success_message='Платёжные методы инициализированы',
    ) as stage:
        try:
            async with AsyncSessionLocal() as db:
                await ensure_payment_method_configs(db)
        except Exception as error:
            stage.warning(f'Не удалось инициализировать платёжные методы: {error}')
            logger.error('❌ Не удалось инициализировать платёжные методы', error=error)
