import asyncio

from app.config import settings
from app.services.maintenance_service import maintenance_service
from app.utils.startup_timeline import StartupTimeline


async def start_maintenance_stage(timeline: StartupTimeline) -> asyncio.Task | None:
    async with timeline.stage(
        'Служба техработ',
        '🛡️',
        success_message='Служба техработ запущена',
    ) as stage:
        if not settings.is_maintenance_monitoring_enabled():
            stage.skip('Мониторинг техработ отключен настройками')
            return None
        if not maintenance_service._check_task or maintenance_service._check_task.done():
            maintenance_task = asyncio.create_task(maintenance_service.start_monitoring())
            stage.log(f'Интервал проверки: {settings.MAINTENANCE_CHECK_INTERVAL}с')
            stage.log(f'Повторных попыток проверки: {settings.get_maintenance_retry_attempts()}')
            return maintenance_task

        stage.skip('Служба техработ уже активна')
        return None
