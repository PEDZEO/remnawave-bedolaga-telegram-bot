import os

from app.database.migrations import run_alembic_upgrade


async def run_database_migration_stage(timeline, logger):
    skip_migration = os.getenv('SKIP_MIGRATION', 'false').lower() == 'true'

    if skip_migration:
        timeline.add_manual_step(
            'Миграция базы данных (Alembic)',
            '⏭️',
            'Пропущено',
            'SKIP_MIGRATION=true',
        )
        return

    async with timeline.stage(
        'Миграция базы данных (Alembic)',
        '🧬',
        success_message='Миграция завершена успешно',
    ) as stage:
        try:
            await run_alembic_upgrade()
            stage.success('Миграция завершена успешно')
        except Exception as migration_error:
            allow_failure = os.getenv('ALLOW_MIGRATION_FAILURE', 'false').lower() == 'true'
            logger.error('Ошибка выполнения миграции', migration_error=migration_error)
            if not allow_failure:
                raise
            stage.warning(f'Ошибка миграции: {migration_error} (ALLOW_MIGRATION_FAILURE=true)')
