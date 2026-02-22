"""Глобальные фикстуры и настройки окружения для тестов."""

import asyncio
import base64
import gc
import hashlib
import os
import secrets
import sys
import types
import uuid
import warnings
from datetime import UTC, datetime
from pathlib import Path

import pytest


pytest_plugins = ['tests.fixtures.promocode_fixtures']


def _install_secrets_fallback_for_sandbox() -> None:
    try:
        secrets.token_hex(1)
        return
    except NotImplementedError:
        pass

    counter = {'value': 0}

    def _fallback_token_bytes(nbytes: int | None = None) -> bytes:
        if nbytes is None:
            nbytes = 32
        counter['value'] += 1
        seed = f'{counter["value"]}:{nbytes}'.encode()
        digest = hashlib.sha256(seed).digest()
        needed = max(nbytes, 0)
        while len(digest) < needed:
            digest += hashlib.sha256(digest).digest()
        return digest[:needed]

    def _fallback_token_hex(nbytes: int | None = None) -> str:
        return _fallback_token_bytes(nbytes).hex()

    def _fallback_token_urlsafe(nbytes: int | None = None) -> str:
        return base64.urlsafe_b64encode(_fallback_token_bytes(nbytes)).rstrip(b'=').decode()

    secrets.token_bytes = _fallback_token_bytes
    secrets.token_hex = _fallback_token_hex
    secrets.token_urlsafe = _fallback_token_urlsafe


_install_secrets_fallback_for_sandbox()


def _install_uuid4_fallback_for_sandbox() -> None:
    try:
        uuid.uuid4()
        return
    except NotImplementedError:
        pass

    counter = {'value': 0}

    def _fallback_uuid4() -> uuid.UUID:
        counter['value'] += 1
        return uuid.uuid5(uuid.NAMESPACE_URL, f'sandbox-{counter["value"]}')

    uuid.uuid4 = _fallback_uuid4


_install_uuid4_fallback_for_sandbox()


# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
test_backup_dir = project_root / 'tests' / 'tmp' / 'backups'
test_backup_dir.mkdir(parents=True, exist_ok=True)

# Подменяем параметры подключения к БД, чтобы SQLAlchemy не требовал aiosqlite.
os.environ.setdefault('DATABASE_MODE', 'postgresql')
os.environ.setdefault('DATABASE_URL', 'postgresql+asyncpg://user:pass@localhost/test_db')
os.environ.setdefault('BOT_TOKEN', 'test-token')
os.environ.setdefault('BACKUP_LOCATION', str(test_backup_dir))

# Создаём заглушки для драйверов, которых может не быть в окружении тестов.
sys.modules.setdefault('asyncpg', types.ModuleType('asyncpg'))
sys.modules.setdefault('aiosqlite', types.ModuleType('aiosqlite'))

# Эмуляция redis.asyncio, чтобы модуль кеша мог импортироваться.
if 'redis.asyncio' not in sys.modules:
    redis_module = types.ModuleType('redis')
    redis_async_module = types.ModuleType('redis.asyncio')

    class _FakeRedisClient:
        async def ping(self):
            """Имитируем успешный ответ ping."""
            return True

        async def close(self):
            """Закрытие соединения ничего не делает."""

        async def get(self, key):
            return None

        async def set(self, key, value, ex=None):
            return True

        async def delete(self, *keys):
            return 0

        async def keys(self, pattern='*'):
            return []

        async def exists(self, key):
            return False

        async def expire(self, key, seconds):
            return True

        async def incr(self, key):
            return 1

    def _from_url(url):
        return _FakeRedisClient()

    redis_async_module.from_url = _from_url
    redis_async_module.Redis = _FakeRedisClient
    sys.modules['redis'] = redis_module
    sys.modules['redis.asyncio'] = redis_async_module

# Минимальная заглушка uvicorn, чтобы избежать импорта multiprocessing в sandbox.
if 'uvicorn' not in sys.modules:
    uvicorn_module = types.ModuleType('uvicorn')

    class _FakeConfig:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class _FakeServer:
        def __init__(self, config=None):
            self.config = config

        async def serve(self):
            return True

    uvicorn_module.Config = _FakeConfig
    uvicorn_module.Server = _FakeServer
    uvicorn_module.run = lambda *args, **kwargs: None
    sys.modules['uvicorn'] = uvicorn_module

# Минимальная реализация SDK YooKassa, чтобы импорт сервисов не падал.
try:
    import yookassa as _real_yookassa  # noqa: F401
except Exception:
    fake_yookassa = types.ModuleType('yookassa')

    class _FakeConfiguration:
        @staticmethod
        def configure(*args, **kwargs):
            """Конфигурация заглушки ничего не делает."""

    class _FakePayment:
        @staticmethod
        def create(*args, **kwargs):
            """Возвращает объект с минимально необходимыми атрибутами."""

            class _Response:
                id = 'yk_fake'
                status = 'pending'
                paid = False
                refundable = False
                metadata = {}
                amount = types.SimpleNamespace(value='0.00', currency='RUB')
                confirmation = types.SimpleNamespace(confirmation_url='https://example.com')
                created_at = datetime.now(UTC)
                description = ''
                test = False

            return _Response()

    fake_yookassa.Configuration = _FakeConfiguration
    fake_yookassa.Payment = _FakePayment
    sys.modules['yookassa'] = fake_yookassa

    # Подготавливаем вложенные пакеты, используемые сервисом.
    domain_module = types.ModuleType('yookassa.domain')
    request_module = types.ModuleType('yookassa.domain.request')
    payment_builder_module = types.ModuleType('yookassa.domain.request.payment_request_builder')
    common_module = types.ModuleType('yookassa.domain.common')
    confirmation_module = types.ModuleType('yookassa.domain.common.confirmation_type')

    class _FakePaymentRequestBuilder:
        def __init__(self):
            self.data: dict = {}

        def set_amount(self, value):
            self.data['amount'] = value
            return self

        def set_capture(self, value):
            self.data['capture'] = value
            return self

        def set_confirmation(self, value):
            self.data['confirmation'] = value
            return self

        def set_description(self, value):
            self.data['description'] = value
            return self

        def set_metadata(self, value):
            self.data['metadata'] = value
            return self

        def set_receipt(self, value):
            self.data['receipt'] = value
            return self

        def set_payment_method_data(self, value):
            self.data['payment_method_data'] = value
            return self

        def build(self):
            return self.data

    class _FakeConfirmationType:
        REDIRECT = 'redirect'

    payment_builder_module.PaymentRequestBuilder = _FakePaymentRequestBuilder
    confirmation_module.ConfirmationType = _FakeConfirmationType

    sys.modules['yookassa.domain'] = domain_module
    sys.modules['yookassa.domain.request'] = request_module
    sys.modules['yookassa.domain.request.payment_request_builder'] = payment_builder_module
    sys.modules['yookassa.domain.common'] = common_module
    sys.modules['yookassa.domain.common.confirmation_type'] = confirmation_module


@pytest.fixture
def fixed_datetime() -> datetime:
    """Возвращает фиксированную отметку времени для воспроизводимых проверок."""
    return datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


def pytest_configure(config: pytest.Config) -> None:
    """Регистрируем маркеры для асинхронных тестов."""

    # Keep coroutine origins in warnings to pinpoint un-awaited AsyncMock calls.
    sys.set_coroutine_origin_tracking_depth(10)

    config.addinivalue_line(
        'markers',
        'asyncio: запуск асинхронного теста через встроенный цикл событий',
    )
    config.addinivalue_line(
        'markers',
        'anyio: запуск асинхронного теста через встроенный цикл событий',
    )


def _close_event_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    if loop is None or loop.is_running() or loop.is_closed():
        return
    try:
        loop.close()
    except Exception:
        return


def _close_orphan_event_loops() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', category=DeprecationWarning)
        policy = asyncio.get_event_loop_policy()
        try:
            current_loop = policy.get_event_loop()
        except RuntimeError:
            current_loop = None

    _close_event_loop(current_loop)
    asyncio.set_event_loop(None)

    policy_local = getattr(policy, '_local', None)
    if policy_local is not None:
        for value in vars(policy_local).values():
            if isinstance(value, asyncio.AbstractEventLoop):
                _close_event_loop(value)

    for obj in gc.get_objects():
        if isinstance(obj, asyncio.AbstractEventLoop):
            _close_event_loop(obj)

    gc.collect()


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Close orphaned default event loop to avoid unraisable ResourceWarning at interpreter shutdown."""
    _close_orphan_event_loops()


def pytest_unconfigure(config: pytest.Config) -> None:
    _close_orphan_event_loops()
