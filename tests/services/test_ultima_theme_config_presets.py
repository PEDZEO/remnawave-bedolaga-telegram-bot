import importlib.util
import sys
import types
from pathlib import Path

import pytest
from pydantic import ValidationError


def _load_branding_module():
    module_name = 'app.cabinet.routes.branding'
    if module_name in sys.modules:
        return sys.modules[module_name]

    routes_package_name = 'app.cabinet.routes'
    if routes_package_name not in sys.modules:
        routes_package = types.ModuleType(routes_package_name)
        routes_package.__path__ = [str(Path(__file__).resolve().parents[2] / 'app' / 'cabinet' / 'routes')]
        sys.modules[routes_package_name] = routes_package

    module_path = Path(__file__).resolve().parents[2] / 'app' / 'cabinet' / 'routes' / 'branding.py'
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError('Failed to load branding module for tests')

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


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
