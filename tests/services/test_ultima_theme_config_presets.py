import importlib

import pytest
from pydantic import ValidationError


def _load_branding_module():
    return importlib.import_module('app.cabinet.routes.branding')


branding = _load_branding_module()


def test_default_ultima_theme_config_has_separate_theme_and_animation_presets():
    model = branding.UltimaThemeConfigResponse(**branding.DEFAULT_ULTIMA_THEME_CONFIG)

    assert model.themePresetId == 'emerald-classic'
    assert model.animationPresetId == 'orbital-aura'


def test_ultima_theme_config_update_accepts_known_presets():
    update = branding.UltimaThemeConfigUpdate(
        themePresetId='rose-nebula',
        animationPresetId='classic-waves',
    )

    assert update.themePresetId == 'rose-nebula'
    assert update.animationPresetId == 'classic-waves'


def test_ultima_theme_config_update_rejects_unknown_theme_preset():
    with pytest.raises(ValidationError):
        branding.UltimaThemeConfigUpdate(themePresetId='unknown-theme')


def test_ultima_theme_config_update_rejects_unknown_animation_preset():
    with pytest.raises(ValidationError):
        branding.UltimaThemeConfigUpdate(animationPresetId='unknown-animation')
