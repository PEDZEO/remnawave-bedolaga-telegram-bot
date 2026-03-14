from app.config import settings
from app.services.ultima_start_service import (
    UltimaNotificationButton,
    UltimaNotificationConfig,
    build_ultima_notification_keyboard,
)


def test_build_ultima_notification_keyboard_skips_when_miniapp_url_missing(monkeypatch):
    monkeypatch.setattr(settings, 'MINIAPP_CUSTOM_URL', '', raising=False)
    monkeypatch.setattr(settings, 'BOT_USERNAME', '', raising=False)

    config = UltimaNotificationConfig(
        enabled=True,
        buttons=[UltimaNotificationButton(text='💳 Купить подписку', path='/subscription/purchase')],
    )

    keyboard = build_ultima_notification_keyboard(config)

    assert keyboard is None


def test_build_ultima_notification_keyboard_uses_cabinet_url_when_configured(monkeypatch):
    monkeypatch.setattr(settings, 'MINIAPP_CUSTOM_URL', 'https://web.pedzeo.ru', raising=False)

    config = UltimaNotificationConfig(
        enabled=True,
        buttons=[UltimaNotificationButton(text='💳 Купить подписку', path='/subscription/purchase')],
    )

    keyboard = build_ultima_notification_keyboard(config)

    assert keyboard is not None
    assert keyboard.inline_keyboard
    button = keyboard.inline_keyboard[0][0]
    assert button.web_app is not None
    assert button.web_app.url.startswith('https://web.pedzeo.ru/subscription/purchase')
