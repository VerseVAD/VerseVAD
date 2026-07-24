from pathlib import Path

from versevad.ui.design import (
    DARK_TOKENS,
    LIGHT_TOKENS,
    MODULE_PRESETS,
    preset_widget_state,
    stylesheet_for,
)
from versevad.ui.preferences import (
    AppearanceMode,
    UiPreferences,
    load_preferences,
    save_preferences,
)


def test_ui_preferences_default_and_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "private" / "ui_preferences.json"
    assert load_preferences(path).appearance is AppearanceMode.SYSTEM

    saved = save_preferences(
        UiPreferences(appearance=AppearanceMode.DARK),
        path,
    )
    assert saved == path
    assert load_preferences(path).appearance is AppearanceMode.DARK


def test_malformed_ui_preferences_fail_safely(tmp_path: Path) -> None:
    path = tmp_path / "ui_preferences.json"
    path.write_text("{not valid", encoding="utf-8")
    assert load_preferences(path) == UiPreferences()


def test_stylesheet_uses_semantic_tokens_and_accessibility_modes() -> None:
    light = stylesheet_for(AppearanceMode.LIGHT)
    dark = stylesheet_for(AppearanceMode.DARK)
    system = stylesheet_for(AppearanceMode.SYSTEM)

    for sheet in (light, dark, system):
        assert "--color-background" in sheet
        assert "--color-text-primary" in sheet
        assert "--color-focus" in sheet
        assert "prefers-reduced-motion" in sheet
        assert "focus-visible" in sheet
    assert "prefers-color-scheme: dark" not in light
    assert "prefers-color-scheme: dark" not in dark
    assert "prefers-color-scheme: dark" in system
    assert light != dark


def _relative_luminance(value: str) -> float:
    channels = [
        int(value[index : index + 2], 16) / 255
        for index in (1, 3, 5)
    ]
    linear = [
        channel / 12.92
        if channel <= 0.04045
        else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted(
        (_relative_luminance(first), _relative_luminance(second)),
        reverse=True,
    )
    return (lighter + 0.05) / (darker + 0.05)


def test_primary_text_and_focus_tokens_meet_contrast_expectations() -> None:
    for tokens in (LIGHT_TOKENS, DARK_TOKENS):
        assert _contrast(tokens["text-primary"], tokens["background"]) >= 7
        assert _contrast(tokens["text-primary"], tokens["surface"]) >= 7
        assert _contrast(tokens["text-secondary"], tokens["background"]) >= 4.5
        assert _contrast(tokens["focus"], tokens["background"]) >= 3


def test_presets_change_only_module_selection_not_advanced_settings() -> None:
    state = preset_widget_state(
        "Literary",
        available_lexicon_ids=(
            "warriner_vad_2013",
            "nrc_vad_v2_1",
            "nrc_emotion_v0_92",
            "nrc_emotion_intensity_v1",
        ),
    )
    assert state["include_poetry_id"] is True
    assert state["include_meter"] is False
    assert "frequency_rare_threshold" not in state
    assert "poetry_id_low_threshold" not in state
    assert preset_widget_state(
        "Custom",
        available_lexicon_ids=(),
    ) == {}
    assert set(MODULE_PRESETS) == {
        "Essential",
        "Literary",
        "Sound and Form",
        "Complete",
        "Custom",
    }
