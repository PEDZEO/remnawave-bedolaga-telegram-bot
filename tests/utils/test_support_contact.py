from types import SimpleNamespace

from app.utils import support_contact
from app.utils.support_contact import build_support_contact_keyboard


def test_build_support_contact_keyboard_returns_none_without_url(monkeypatch) -> None:
    monkeypatch.setattr(
        support_contact,
        'settings',
        SimpleNamespace(get_support_contact_url=lambda: None),
    )

    assert build_support_contact_keyboard() is None


def test_build_support_contact_keyboard_returns_inline_button(monkeypatch) -> None:
    monkeypatch.setattr(
        support_contact,
        'settings',
        SimpleNamespace(get_support_contact_url=lambda: 'https://t.me/test_support'),
    )

    markup = build_support_contact_keyboard(button_text='🆘 Обжаловать')

    assert markup is not None
    assert len(markup.inline_keyboard) == 1
    assert len(markup.inline_keyboard[0]) == 1
    assert markup.inline_keyboard[0][0].text == '🆘 Обжаловать'
    assert markup.inline_keyboard[0][0].url == 'https://t.me/test_support'
