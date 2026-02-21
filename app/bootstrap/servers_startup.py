from app.database.crud.server_squad import ensure_servers_synced
from app.database.database import AsyncSessionLocal


async def sync_servers_stage(timeline, logger):
    async with timeline.stage(
        'Синхронизация серверов из RemnaWave',
        '🖥️',
        success_message='Серверы синхронизированы',
    ) as stage:
        try:
            async with AsyncSessionLocal() as db:
                await ensure_servers_synced(db)
        except Exception as error:
            stage.warning(f'Не удалось синхронизировать серверы: {error}')
            logger.error('❌ Не удалось синхронизировать серверы', error=error)
