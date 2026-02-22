import asyncio

from app.services.daily_subscription_service import daily_subscription_service
from app.utils.startup_timeline import StartupTimeline


async def start_daily_subscription_stage(timeline: StartupTimeline) -> asyncio.Task | None:
    async with timeline.stage(
        'Суточные подписки',
        '💳',
        success_message='Сервис суточных подписок запущен',
    ) as stage:
        if daily_subscription_service.is_enabled():
            daily_subscription_task = asyncio.create_task(daily_subscription_service.start_monitoring())
            interval_minutes = daily_subscription_service.get_check_interval_minutes()
            stage.log(f'Интервал проверки: {interval_minutes} мин')
            return daily_subscription_task

        stage.skip('Суточные подписки отключены настройками')
        return None
