import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from aiogram import Bot, Dispatcher


if TYPE_CHECKING:
    from app.bootstrap.core_runtime_startup import CoreRuntimeStartupContext
    from app.bootstrap.runtime_tasks_startup import RuntimeStartupTasks


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

    def apply_core_runtime(self, runtime_context: 'CoreRuntimeStartupContext') -> None:
        self.bot = runtime_context.bot
        self.dp = runtime_context.dp
        self.verification_providers = runtime_context.verification_providers
        self.auto_verification_active = runtime_context.auto_verification_active
        self.polling_enabled = runtime_context.polling_enabled
        self.telegram_webhook_enabled = runtime_context.telegram_webhook_enabled
        self.web_api_server = runtime_context.web_api_server

    def apply_runtime_tasks(self, runtime_tasks: 'RuntimeStartupTasks') -> None:
        self.monitoring_task = runtime_tasks.monitoring_task
        self.maintenance_task = runtime_tasks.maintenance_task
        self.traffic_monitoring_task = runtime_tasks.traffic_monitoring_task
        self.daily_subscription_task = runtime_tasks.daily_subscription_task
        self.version_check_task = runtime_tasks.version_check_task
        self.polling_task = runtime_tasks.polling_task

    def build_shutdown_payload(self) -> dict[str, Any]:
        return {
            'monitoring_task': self.monitoring_task,
            'maintenance_task': self.maintenance_task,
            'version_check_task': self.version_check_task,
            'traffic_monitoring_task': self.traffic_monitoring_task,
            'daily_subscription_task': self.daily_subscription_task,
            'polling_task': self.polling_task,
            'bot': self.bot,
            'web_api_server': self.web_api_server,
            'telegram_webhook_enabled': self.telegram_webhook_enabled,
        }
