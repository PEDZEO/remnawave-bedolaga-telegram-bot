import asyncio
from dataclasses import dataclass, field
from typing import Any

from aiogram import Bot, Dispatcher


@dataclass
class RuntimeState:
    bot: Bot | None = None
    dp: Dispatcher | None = None
    monitoring_task: asyncio.Task | None = None
    maintenance_task: asyncio.Task | None = None
    version_check_task: asyncio.Task | None = None
    traffic_monitoring_task: asyncio.Task | None = None
    daily_subscription_task: asyncio.Task | None = None
    polling_task: asyncio.Task | None = None
    web_api_server: Any | None = None
    telegram_webhook_enabled: bool = False
    polling_enabled: bool = True
    verification_providers: list[str] = field(default_factory=list)
    auto_verification_active: bool = False
    summary_logged: bool = False
