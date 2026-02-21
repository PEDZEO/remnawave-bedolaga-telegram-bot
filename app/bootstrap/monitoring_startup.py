import asyncio

from app.config import settings
from app.services.monitoring_service import monitoring_service
from app.utils.startup_timeline import StartupTimeline


async def start_monitoring_stage(timeline: StartupTimeline) -> asyncio.Task:
    async with timeline.stage(
        'Служба мониторинга',
        '📈',
        success_message='Служба мониторинга запущена',
    ) as stage:
        monitoring_task = asyncio.create_task(monitoring_service.start_monitoring())
        stage.log(f'Интервал опроса: {settings.MONITORING_INTERVAL}с')
        return monitoring_task
