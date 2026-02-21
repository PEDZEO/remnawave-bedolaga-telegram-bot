from app.database.crud.tariff import ensure_tariffs_synced
from app.database.database import AsyncSessionLocal


async def sync_tariffs_stage(timeline, logger):
    async with timeline.stage(
        'Синхронизация тарифов из конфига',
        '💰',
        success_message='Тарифы синхронизированы',
    ) as stage:
        try:
            async with AsyncSessionLocal() as db:
                await ensure_tariffs_synced(db)
        except Exception as error:
            stage.warning(f'Не удалось синхронизировать тарифы: {error}')
            logger.error('❌ Не удалось синхронизировать тарифы', error=error)
