from app.services.backup_service import backup_service


async def initialize_backup_stage(timeline, logger, bot):
    async with timeline.stage(
        'Сервис бекапов',
        '🗄️',
        success_message='Сервис бекапов инициализирован',
    ) as stage:
        try:
            backup_service.bot = bot
            settings_obj = await backup_service.get_backup_settings()
            if settings_obj.auto_backup_enabled:
                await backup_service.start_auto_backup()
                stage.log(
                    'Автобекапы включены: интервал '
                    f'{settings_obj.backup_interval_hours}ч, запуск {settings_obj.backup_time}'
                )
            else:
                stage.log('Автобекапы отключены настройками')
            stage.success('Сервис бекапов инициализирован')
        except Exception as error:
            stage.warning(f'Ошибка инициализации сервиса бекапов: {error}')
            logger.error('❌ Ошибка инициализации сервиса бекапов', error=error)
