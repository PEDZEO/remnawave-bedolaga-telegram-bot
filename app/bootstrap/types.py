from typing import Any, Protocol


class LoggerLike(Protocol):
    def info(self, event: str, *args: Any, **kwargs: Any) -> Any: ...

    def warning(self, event: str, *args: Any, **kwargs: Any) -> Any: ...

    def error(self, event: str, *args: Any, **kwargs: Any) -> Any: ...


class KillerLike(Protocol):
    exit: bool


class TelegramNotifierLike(Protocol):
    def set_bot(self, bot: Any) -> Any: ...
