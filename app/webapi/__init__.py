"""Пакет административного веб-API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any


if TYPE_CHECKING:
    from .app import create_web_api_app
    from .server import WebAPIServer


__all__ = ['WebAPIServer', 'create_web_api_app']


def __getattr__(name: str) -> Any:
    if name == 'create_web_api_app':
        from .app import create_web_api_app as app_factory

        return app_factory
    if name == 'WebAPIServer':
        from .server import WebAPIServer

        return WebAPIServer
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
