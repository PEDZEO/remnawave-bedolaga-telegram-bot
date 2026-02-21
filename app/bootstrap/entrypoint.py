import asyncio
import sys
import traceback
from collections.abc import Awaitable, Callable
from typing import Any


def run_main_entrypoint(
    main_coroutine: Callable[[], Awaitable[Any]],
    crash_notifier: Callable[[Exception], Awaitable[None]],
) -> None:
    try:
        asyncio.run(main_coroutine())
    except KeyboardInterrupt:
        print('\n🛑 Бот остановлен пользователем')
    except Exception as error:
        print(f'❌ Критическая ошибка: {error}')
        traceback.print_exc()
        try:
            asyncio.run(crash_notifier(error))
        except Exception:
            pass
        sys.exit(1)
