"""Programmatic Alembic migration runner for bot startup."""

from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text


logger = structlog.get_logger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_ALEMBIC_INI = _PROJECT_ROOT / 'alembic.ini'


def _get_alembic_config() -> Config:
    """Build Alembic Config pointing at the project root."""
    from app.config import settings

    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option('sqlalchemy.url', settings.get_database_url())
    return cfg


async def _needs_auto_stamp() -> bool:
    """Check if DB has existing tables but no alembic_version (transition from universal_migration)."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('alembic_version'))
        if has_alembic:
            return False
        has_users = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('users'))
        return has_users


_INITIAL_REVISION = '0001'
_LEGACY_REVISION_REMAP: dict[str, str] = {
    # Legacy branch value from older server snapshots no longer present in new chain.
    '0004': '0003',
}


async def _remap_legacy_revision_if_needed() -> bool:
    """Rewrite known obsolete alembic_version values to current chain nodes."""
    from app.database.database import engine

    async with engine.begin() as conn:
        has_alembic = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('alembic_version'))
        if not has_alembic:
            return False

        current_revision = (
            await conn.execute(
                text('SELECT version_num FROM alembic_version ORDER BY version_num LIMIT 1')
            )
        ).scalar_one_or_none()
        if current_revision is None:
            return False

        target_revision = _LEGACY_REVISION_REMAP.get(str(current_revision))
        if target_revision is None:
            return False

        await conn.execute(
            text('UPDATE alembic_version SET version_num = :target WHERE version_num = :current'),
            {'target': target_revision, 'current': str(current_revision)},
        )

    logger.warning(
        'Alembic revision remap applied for legacy database snapshot',
        from_revision=str(current_revision),
        to_revision=target_revision,
    )
    return True


async def run_alembic_upgrade() -> None:
    """Run ``alembic upgrade head``, auto-stamping existing databases first."""
    import asyncio

    await _remap_legacy_revision_if_needed()

    if await _needs_auto_stamp():
        logger.warning(
            'Обнаружена существующая БД без alembic_version — автоматический stamp 0001 (переход с universal_migration)'
        )
        await _stamp_alembic_revision(_INITIAL_REVISION)

    cfg = _get_alembic_config()
    loop = asyncio.get_running_loop()
    # run_in_executor offloads to a thread where env.py can safely
    # call asyncio.run() to create its own event loop.
    await loop.run_in_executor(None, command.upgrade, cfg, 'head')
    logger.info('Alembic миграции применены')


async def stamp_alembic_head() -> None:
    """Stamp the DB as being at head without running migrations (for existing DBs)."""
    await _stamp_alembic_revision('head')


async def _stamp_alembic_revision(revision: str) -> None:
    """Stamp the DB at a specific revision without running migrations."""
    import asyncio

    cfg = _get_alembic_config()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, command.stamp, cfg, revision)
    logger.info('Alembic: база отмечена как актуальная', revision=revision)
