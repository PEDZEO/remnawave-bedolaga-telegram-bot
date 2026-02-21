from app.localization.loader import ensure_locale_templates
from app.utils.startup_timeline import StartupTimeline

from .types import LoggerLike


async def prepare_localizations(timeline: StartupTimeline, logger: LoggerLike) -> None:
    async with timeline.stage('Подготовка локализаций', '🗂️', success_message='Шаблоны локализаций готовы') as stage:
        try:
            ensure_locale_templates()
        except Exception as error:
            stage.warning(f'Не удалось подготовить шаблоны локализаций: {error}')
            logger.warning('Failed to prepare locale templates', error=error)
