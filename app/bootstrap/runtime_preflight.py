from dataclasses import dataclass

import structlog

from app.bootstrap.localization_startup import prepare_localizations
from app.bootstrap.runtime_logging import configure_runtime_logging
from app.config import settings
from app.logging_config import setup_logging
from app.utils.startup_timeline import StartupTimeline


@dataclass(slots=True)
class RuntimePreflightContext:
    logger: structlog.typing.FilteringBoundLogger
    timeline: StartupTimeline
    telegram_notifier: object | None


async def prepare_runtime_preflight() -> RuntimePreflightContext:
    file_formatter, console_formatter, telegram_notifier = setup_logging()
    await configure_runtime_logging(file_formatter, console_formatter)

    # NOTE: TelegramNotifierProcessor and noisy logger suppression are
    # handled inside setup_logging() / logging_config.py.
    logger = structlog.get_logger(__name__)
    timeline = StartupTimeline(logger, 'Bedolaga Remnawave Bot')
    timeline.log_banner(
        [
            ('Уровень логирования', settings.LOG_LEVEL),
            ('Режим БД', settings.DATABASE_MODE),
        ]
    )
    await prepare_localizations(timeline, logger)

    return RuntimePreflightContext(
        logger=logger,
        timeline=timeline,
        telegram_notifier=telegram_notifier,
    )
