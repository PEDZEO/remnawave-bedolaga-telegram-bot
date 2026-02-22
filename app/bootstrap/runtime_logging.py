import logging
import sys

from app.config import settings
from app.services.log_rotation_service import log_rotation_service
from app.utils.log_handlers import ExcludePaymentFilter, LevelFilterHandler
from app.utils.payment_logger import configure_payment_logger


async def configure_runtime_logging(
    file_formatter: logging.Formatter,
    console_formatter: logging.Formatter,
) -> None:
    log_handlers = []

    if settings.is_log_rotation_enabled():
        await log_rotation_service.initialize()

        log_dir = log_rotation_service.current_dir
        log_dir.mkdir(parents=True, exist_ok=True)

        bot_handler = logging.FileHandler(log_dir / 'bot.log', encoding='utf-8')
        bot_handler.setFormatter(file_formatter)
        bot_handler.addFilter(ExcludePaymentFilter())
        log_handlers.append(bot_handler)

        info_handler = LevelFilterHandler(
            str(log_dir / settings.LOG_INFO_FILE),
            min_level=logging.INFO,
            max_level=logging.INFO,
        )
        info_handler.setFormatter(file_formatter)
        info_handler.addFilter(ExcludePaymentFilter())
        log_handlers.append(info_handler)

        warning_handler = LevelFilterHandler(
            str(log_dir / settings.LOG_WARNING_FILE),
            min_level=logging.WARNING,
        )
        warning_handler.setFormatter(file_formatter)
        warning_handler.addFilter(ExcludePaymentFilter())
        log_handlers.append(warning_handler)

        error_handler = LevelFilterHandler(
            str(log_dir / settings.LOG_ERROR_FILE),
            min_level=logging.ERROR,
        )
        error_handler.setFormatter(file_formatter)
        error_handler.addFilter(ExcludePaymentFilter())
        log_handlers.append(error_handler)

        payment_handler = logging.FileHandler(
            log_dir / settings.LOG_PAYMENTS_FILE,
            encoding='utf-8',
        )
        configure_payment_logger(payment_handler, file_formatter)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(console_formatter)
        log_handlers.append(stream_handler)

        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            handlers=log_handlers,
            force=True,
        )

        log_rotation_service.register_handlers(log_handlers)
        return

    file_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    log_handlers.append(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(console_formatter)
    log_handlers.append(stream_handler)

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        handlers=log_handlers,
        force=True,
    )
