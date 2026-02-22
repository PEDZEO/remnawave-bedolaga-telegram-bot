import os

from app.database.migrations import run_alembic_upgrade
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


def _env_flag_enabled(name: str) -> bool:
    return os.getenv(name, 'false').lower() == 'true'


async def run_database_migration_stage(timeline: StartupTimeline, logger: LoggerLike) -> None:
    skip_migration = _env_flag_enabled('SKIP_MIGRATION')

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
            allow_failure = _env_flag_enabled('ALLOW_MIGRATION_FAILURE')
            logger.error('Ошибка выполнения миграции', migration_error=migration_error)
            if not allow_failure:
                raise
            stage.warning(f'Ошибка миграции: {migration_error} (ALLOW_MIGRATION_FAILURE=true)')
