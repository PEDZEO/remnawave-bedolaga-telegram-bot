"""Programmatic Alembic migration runner for bot startup."""

import asyncio
from pathlib import Path
from typing import Any

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


async def _run_alembic_command(func: Any, cfg: Config, *args: Any) -> None:
    """Run blocking Alembic command in thread executor."""
    loop = asyncio.get_running_loop()
    # Offload to thread where env.py can safely call asyncio.run() for its own loop.
    await loop.run_in_executor(None, func, cfg, *args)


async def _needs_auto_stamp() -> bool:
    """Check if DB has existing tables but no alembic_version (transition from universal_migration)."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('alembic_version'))
        if has_alembic:
            return False
        has_users = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('users'))
        return has_users


async def _is_fresh_database() -> bool:
    """Return True when the target DB has no public tables and no Alembic state."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('alembic_version'))
        if has_alembic:
            return False

        def _has_any_tables(sync_conn) -> bool:
            return bool(inspect(sync_conn).get_table_names())

        has_any_tables = await conn.run_sync(_has_any_tables)
        return not has_any_tables


async def _is_current_schema_snapshot_without_alembic() -> bool:
    """Detect partially bootstrapped/current-schema DBs that should be stamped at head."""
    from app.database.database import engine

    async with engine.connect() as conn:
        has_alembic = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('alembic_version'))
        if has_alembic:
            return False

        def _has_current_schema_markers(sync_conn) -> bool:
            inspector = inspect(sync_conn)
            return any(
                [
                    inspector.has_table('guest_purchases'),
                    inspector.has_table('cabinet_refresh_tokens'),
                    inspector.has_table('main_menu_buttons'),
                ]
            )

        return await conn.run_sync(_has_current_schema_markers)


async def _bootstrap_current_schema() -> None:
    """Create the current SQLAlchemy metadata for a fresh database."""
    from app.database.database import engine
    from app.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn, checkfirst=True))

    logger.info('Current SQLAlchemy schema bootstrapped for fresh database')


_INITIAL_REVISION = '0001'
_LEGACY_REVISION_REMAP: dict[str, str] = {
    # Legacy branch value from older server snapshots no longer present in new chain.
    '0004': '0003',
    # Legacy post-0040 revisions were later squashed out of the current branch.
    # Production snapshots may still be stamped with these values even though the
    # current metadata already works with the resulting schema.
    '0041': '0040',
    '0042': '0040',
    '0043': '0040',
    '0044': '0040',
    '0045': '0040',
}


async def _get_current_alembic_revision(conn) -> str | None:
    """Return current revision from alembic_version table, if present."""
    revision = (
        await conn.execute(text('SELECT version_num FROM alembic_version ORDER BY version_num LIMIT 1'))
    ).scalar_one_or_none()
    if revision is None:
        return None
    return str(revision)


async def _remap_legacy_revision_if_needed() -> bool:
    """Rewrite known obsolete alembic_version values to current chain nodes."""
    from app.database.database import engine

    async with engine.begin() as conn:
        has_alembic = await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table('alembic_version'))
        if not has_alembic:
            return False

        current_revision = await _get_current_alembic_revision(conn)
        if current_revision is None:
            return False

        target_revision = _LEGACY_REVISION_REMAP.get(current_revision)
        if target_revision is None:
            return False

        await conn.execute(
            text('UPDATE alembic_version SET version_num = :target WHERE version_num = :current'),
            {'target': target_revision, 'current': current_revision},
        )

    logger.warning(
        'Alembic revision remap applied for legacy database snapshot',
        from_revision=current_revision,
        to_revision=target_revision,
    )
    return True


async def run_alembic_upgrade() -> None:
    """Run ``alembic upgrade heads``, auto-stamping existing databases first."""
    await _remap_legacy_revision_if_needed()

    if await _is_fresh_database():
        logger.warning('Fresh database detected — bootstrapping current schema and stamping Alembic heads')
        await _bootstrap_current_schema()
        await _stamp_alembic_revision('heads')
        return

    if await _is_current_schema_snapshot_without_alembic():
        logger.warning('Current-schema database without alembic_version detected — stamping Alembic heads')
        await _stamp_alembic_revision('heads')
        return

    if await _needs_auto_stamp():
        logger.warning(
            'Обнаружена существующая БД без alembic_version — автоматический stamp 0001 (переход с universal_migration)'
        )
        await _stamp_alembic_revision(_INITIAL_REVISION)

    cfg = _get_alembic_config()
    await _run_alembic_command(command.upgrade, cfg, 'heads')
    logger.info('Alembic миграции применены')


async def stamp_alembic_head() -> None:
    """Stamp the DB as being at head without running migrations (for existing DBs)."""
    await _stamp_alembic_revision('heads')


async def _stamp_alembic_revision(revision: str) -> None:
    """Stamp the DB at a specific revision without running migrations."""
    cfg = _get_alembic_config()
    await _run_alembic_command(command.stamp, cfg, revision)
    logger.info('Alembic: база отмечена как актуальная', revision=revision)
