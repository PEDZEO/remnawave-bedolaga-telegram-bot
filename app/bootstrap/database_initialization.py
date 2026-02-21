from app.database.database import sync_postgres_sequences
from app.services.web_api_token_service import ensure_default_web_api_token


async def initialize_database_stage(timeline):
    async with timeline.stage(
        'Инициализация базы данных',
        '🗄️',
        success_message='База данных готова',
    ) as stage:
        seq_ok = await sync_postgres_sequences()
        token_ok = await ensure_default_web_api_token()
        if not seq_ok:
            stage.warning('Не удалось синхронизировать последовательности PostgreSQL')
        if not token_ok:
            stage.warning('Не удалось создать/проверить дефолтный веб-API токен')
