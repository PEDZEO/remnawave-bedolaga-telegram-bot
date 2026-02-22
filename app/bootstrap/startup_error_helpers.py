from typing import Protocol

from .types import LoggerLike


class StageWarningHandle(Protocol):
    def warning(self, message: str) -> None: ...


def warn_startup_stage_error(
    *,
    stage: StageWarningHandle,
    logger: LoggerLike,
    stage_error_message: str,
    logger_error_message: str,
    error: Exception,
) -> None:
    stage.warning(f'{stage_error_message}: {error}')
    logger.error(logger_error_message, error=error)
