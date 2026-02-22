from typing import Protocol


class LoggerLike(Protocol):
    def info(self, event: str, *args: object, **kwargs: object) -> None: ...

    def warning(self, event: str, *args: object, **kwargs: object) -> None: ...

    def error(self, event: str, *args: object, **kwargs: object) -> None: ...


class KillerLike(Protocol):
    exit: bool


class TelegramNotifierLike(Protocol):
    def set_bot(self, bot: object) -> None: ...


class WebAPIServerLike(Protocol):
    async def stop(self) -> None: ...
