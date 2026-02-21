import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent))

from app.bootstrap.crash_notification import send_crash_notification_on_error
from app.bootstrap.entrypoint import run_main_entrypoint
from app.bootstrap.runtime_preflight import prepare_runtime_preflight
from app.bootstrap.runtime_session import run_runtime_session


async def main():
    preflight = await prepare_runtime_preflight()
    await run_runtime_session(preflight)


if __name__ == '__main__':
    run_main_entrypoint(main, send_crash_notification_on_error)
