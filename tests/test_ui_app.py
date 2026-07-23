from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parents[1] / "src" / "versevad" / "ui" / "app.py"


def _button(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def test_interface_starts_with_beginner_input_workflow() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not app.exception
    assert [title.value for title in app.title] == ["VerseVAD"]
    assert [area.label for area in app.text_area] == [
        "Paste the poem exactly as you want it analyzed"
    ]
    assert "Poem title or working label" in [field.label for field in app.text_input]
    assert "Analyze this text" in [button.label for button in app.button]
    assert "Run self-test" in [button.label for button in app.button]
    assert not app.tabs


def test_interface_shows_plain_language_input_error() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    _button(app, "Analyze this text").click()
    app.run()
    assert not app.exception
    assert any("Enter a title" in error.value for error in app.error)


def test_interface_analyzes_pasted_poem_and_builds_readable_views() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=60).run()
    title = next(field for field in app.text_input if field.label == "Poem title or working label")
    title.input("Interface validation poem")
    app.text_area[0].input("A bit of bright joy and fear in the dark night.")
    app.multiselect[0].set_value(
        ["nrc_vad_v2_1", "nrc_emotion_v0_92", "nrc_emotion_intensity_v1"]
    )
    _button(app, "Analyze this text").click()
    app.run(timeout=60)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert [tab.label for tab in app.tabs] == [
        "Overview",
        "VAD profile",
        "Emotion profile",
        "Evidence",
        "Downloads",
        "How to read",
    ]
    assert ("Lexicons analyzed", "3") in [
        (metric.label, metric.value) for metric in app.metric
    ]
    downloads = app.get("download_button")
    assert {button.label for button in downloads} == {
        "Download readable summary",
        "Download CSV reading guide",
        "Download full audit bundle",
    }
    assert any("Comparable normalized VAD" in heading.value for heading in app.subheader)
    assert any("Categorical emotion associations" in heading.value for heading in app.subheader)


def test_windows_helpers_are_local_and_telemetry_disabled() -> None:
    root = APP_PATH.parents[3]
    launcher = (root / "start_versevad.bat").read_text(encoding="utf-8")
    setup = (root / "scripts" / "setup_windows.ps1").read_text(encoding="utf-8")
    config = (root / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "127.0.0.1" in launcher
    assert "--offline" in launcher
    assert "gatherUsageStats false" in launcher
    assert "UV_PYTHON_INSTALL_DIR" in setup
    assert "ExpectedUvHash" in setup
    assert "gatherUsageStats = false" in config
