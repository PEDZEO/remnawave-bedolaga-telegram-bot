import asyncio

from app.services.traffic_monitoring_service import traffic_monitoring_scheduler


async def start_traffic_monitoring_stage(timeline):
    async with timeline.stage(
        'Мониторинг трафика',
        '📊',
        success_message='Мониторинг трафика запущен',
    ) as stage:
        if traffic_monitoring_scheduler.is_enabled():
            traffic_monitoring_task = asyncio.create_task(traffic_monitoring_scheduler.start_monitoring())
            status_info = traffic_monitoring_scheduler.get_status_info()
            stage.log(status_info)
            return traffic_monitoring_task

        stage.skip('Мониторинг трафика отключен настройками')
        return None
