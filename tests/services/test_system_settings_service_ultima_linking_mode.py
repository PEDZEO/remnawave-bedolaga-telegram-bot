from __future__ import annotations

from app.services.system_settings_service import BotConfigurationService


def test_ultima_account_linking_mode_is_mapped_to_happ_category() -> None:
    assert BotConfigurationService.CATEGORY_KEY_OVERRIDES['CABINET_ULTIMA_ACCOUNT_LINKING_MODE'] == 'HAPP'


def test_ultima_account_linking_mode_declares_expected_choices() -> None:
    choices = BotConfigurationService.CHOICES['CABINET_ULTIMA_ACCOUNT_LINKING_MODE']

    assert [choice.value for choice in choices] == ['code', 'provider_auth']


def test_ultima_account_linking_mode_has_operator_hint() -> None:
    hint = BotConfigurationService.SETTING_HINTS['CABINET_ULTIMA_ACCOUNT_LINKING_MODE']

    assert 'Сохранение доступа' in hint['description']
    assert 'safe-merge' in hint['warning']
