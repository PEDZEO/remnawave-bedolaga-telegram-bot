import asyncio

from app.config import settings
from app.services.version_service import version_service
from app.utils.startup_timeline import StartupTimeline


async def start_version_check_stage(timeline: StartupTimeline) -> asyncio.Task | None:
    async with timeline.stage(
        'Сервис проверки версий',
        '📄',
        success_message='Проверка версий запущена',
    ) as stage:
        if settings.is_version_check_enabled():
            version_check_task = asyncio.create_task(version_service.start_periodic_check())
            stage.log(f'Интервал проверки: {settings.VERSION_CHECK_INTERVAL_HOURS}ч')
            return version_check_task

        stage.skip('Проверка версий отключена настройками')
        return None
