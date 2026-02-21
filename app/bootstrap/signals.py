import signal

import structlog


class GracefulExit:
    def __init__(self):
        self.exit = False

    def exit_gracefully(self, signum, frame):
        structlog.get_logger(__name__).info('Получен сигнал, корректное завершение работы', signum=signum)
        self.exit = True


def install_signal_handlers() -> GracefulExit:
    killer = GracefulExit()
    signal.signal(signal.SIGINT, killer.exit_gracefully)
    signal.signal(signal.SIGTERM, killer.exit_gracefully)
    return killer
