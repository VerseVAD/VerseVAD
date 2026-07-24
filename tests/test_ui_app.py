from pathlib import Path

from streamlit.testing.v1 import AppTest

from versevad.db.repository import CorpusTextImport, ProjectRepository


APP_PATH = Path(__file__).parents[1] / "src" / "versevad" / "ui" / "app.py"


def _button(app: AppTest, label: str):
    return next(button for button in app.button if button.label == label)


def test_interface_starts_with_beginner_input_workflow() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    assert not app.exception
    assert [title.value for title in app.title] == ["VerseVAD"]
    assert "Paste the poem exactly as you want it analyzed" in [
        area.label for area in app.text_area
    ]
    navigation = app.get("button_group")[0]
    assert navigation.label == "Workspace"
    assert navigation.value == "One Poem"
    assert "Poem title or working label" in [field.label for field in app.text_input]
    assert "Analyze this text" in [button.label for button in app.button]
    assert "Run self-test" in [button.label for button in app.button]
    assert "Concreteness profile (Brysbaert et al. ratings)" in [
        field.label for field in app.checkbox
    ]
    assert "Frequency & rarity profile (SUBTLEX-US Zipf)" in [
        field.label for field in app.checkbox
    ]
    assert not app.tabs


def test_interface_opens_persistent_corpus_workspace(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("VERSEVAD_DATABASE_PATH", str(tmp_path / "versevad.sqlite3"))
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    navigation = app.get("button_group")[0]
    navigation.set_value("Projects & Corpus")
    app.run(timeout=30)
    assert not app.exception
    assert [title.value for title in app.title] == ["VerseVAD Projects & Corpus"]
    assert "Project title" in [field.label for field in app.text_input]
    assert "Create project" in [button.label for button in app.button]


def test_corpus_workspace_exposes_phase5_review_scenarios(
    tmp_path,
    monkeypatch,
) -> None:
    database_path = tmp_path / "versevad.sqlite3"
    monkeypatch.setenv("VERSEVAD_DATABASE_PATH", str(database_path))
    repository = ProjectRepository(database_path)
    project = repository.create_project("Review interface project")
    repository.import_texts(
        project.project_id,
        (CorpusTextImport("Poem", "poem.txt", "poem.txt", "Bright."),),
    )
    repository.create_review_scenario(
        project.project_id,
        "Conservative review",
    )

    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    navigation = app.get("button_group")[0]
    navigation.set_value("Projects & Corpus")
    app.run(timeout=30)

    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Works & Metadata",
        "Language Profile",
        "Analyze & Compare",
        "Review & Scenarios",
        "Excel Export",
        "Project Settings",
    ]
    assert "Review scenario" in [field.label for field in app.selectbox]
    assert "Scenario to edit" in [field.label for field in app.selectbox]
    assert "Create review scenario" in [button.label for button in app.button]


def test_interface_deletes_only_exactly_confirmed_project(tmp_path, monkeypatch) -> None:
    database_path = tmp_path / "versevad.sqlite3"
    monkeypatch.setenv("VERSEVAD_DATABASE_PATH", str(database_path))
    repository = ProjectRepository(database_path)
    disposable = repository.create_project("Disposable project")
    keeper = repository.create_project("Keep this project")

    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    navigation = app.get("button_group")[0]
    navigation.set_value("Projects & Corpus")
    app.run(timeout=30)
    active_project = next(
        field for field in app.selectbox if field.label == "Active project"
    )
    active_project.set_value(disposable.project_id)
    app.run(timeout=30)

    confirmation = next(
        field
        for field in app.text_input
        if field.label.startswith("Type the exact project title to confirm")
    )
    delete_button = _button(app, "Delete this project")
    assert delete_button.disabled

    confirmation.input("Disposable project")
    app.run(timeout=30)
    delete_button = _button(app, "Delete this project")
    assert not delete_button.disabled
    delete_button.click()
    app.run(timeout=30)

    assert not app.exception
    assert any(
        'Project "Disposable project" was deleted' in message.value
        for message in app.success
    )
    assert [project.project_id for project in repository.list_projects()] == [
        keeper.project_id
    ]


def test_interface_opens_lexicon_explorer() -> None:
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    navigation = app.get("button_group")[0]
    navigation.set_value("Lexicon Explorer")
    app.run(timeout=30)
    assert not app.exception
    assert [title.value for title in app.title] == ["Lexicon Explorer"]
    assert "Word or phrase" in [field.label for field in app.text_input]
    assert "Optional user-supplied mapping" in [field.label for field in app.text_input]
    assert "Search installed lexicons" in [button.label for button in app.button]


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
            "Language Profile",
            "Concreteness Profile",
            "Frequency & Rarity",
            "Age of Acquisition",
            "Pronunciation & Prosody",
            "Meter & Rhythm",
            "Rhyme & Sound",
            "VAD Profile",
        "Emotion Profile",
        "Evidence",
        "Downloads",
        "How to Read",
    ]
    assert ("Lexicons analyzed", "3") in [
        (metric.label, metric.value) for metric in app.metric
    ]
    downloads = app.get("download_button")
    assert {button.label for button in downloads} >= {
        "Download readable summary",
        "Download CSV reading guide",
        "Download full audit bundle",
    }
    assert any("Parallel Normalized VAD Views" in heading.value for heading in app.subheader)
    assert any("Stopword Sensitivity" in heading.value for heading in app.subheader)
    assert any("Eight Emotion Associations" in heading.value for heading in app.subheader)
    assert any(
        "Positive and Negative Sentiment Associations" in heading.value
        for heading in app.subheader
    )
    assert any("Part-of-Speech Profile" in heading.value for heading in app.subheader)
    assert any(
        "Shared Processing Record" in heading.value for heading in app.subheader
    )
    assert any(
        "Concreteness was not selected" in message.value
        for message in app.info
    )


def test_interface_runs_optional_concreteness_profile_if_resource_is_present() -> None:
    resource = (
        APP_PATH.parents[3]
        / "resources"
        / "brysbaert_warriner_kuperman_concreteness_DATA.xlsx"
    )
    if not resource.is_file():
        return

    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    title = next(
        field
        for field in app.text_input
        if field.label == "Poem title or working label"
    )
    title.input("Concreteness interface validation")
    app.text_area[0].input("Stone and justice.\n\nThe grasshopper jumps.")
    app.multiselect[0].set_value([])
    concreteness = next(
        field
        for field in app.checkbox
        if field.label == "Concreteness profile (Brysbaert et al. ratings)"
    )
    assert not concreteness.disabled
    concreteness.set_value(True)
    app.run(timeout=90)
    _button(app, "Analyze this text").click()
    app.run(timeout=90)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert [tab.label for tab in app.tabs] == [
        "Overview",
        "Language Profile",
        "Concreteness Profile",
        "Frequency & Rarity",
        "Age of Acquisition",
        "Pronunciation & Prosody",
        "Meter & Rhythm",
        "Rhyme & Sound",
        "VAD Profile",
        "Emotion Profile",
        "Evidence",
        "Downloads",
        "How to Read",
    ]
    assert any(
        heading.value == "Normative Lexical Concreteness"
        for heading in app.subheader
    )
    assert ("Lexicons analyzed", "0") in [
        (metric.label, metric.value) for metric in app.metric
    ]


def test_interface_runs_optional_frequency_profile_and_content_scope_if_present() -> None:
    resource = (
        APP_PATH.parents[3]
        / "resources"
        / "subtlex-us"
        / "SUBTLEX-US frequency list with PoS and Zipf information.xlsx"
    )
    if not resource.is_file():
        return

    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    title = next(
        field
        for field in app.text_input
        if field.label == "Poem title or working label"
    )
    title.input("Frequency interface validation")
    app.text_area[0].input("The stone runs swiftly and the bright grass bends.")
    app.multiselect[0].set_value([])
    frequency = next(
        field
        for field in app.checkbox
        if field.label == "Frequency & rarity profile (SUBTLEX-US Zipf)"
    )
    assert not frequency.disabled
    frequency.set_value(True)
    app.run(timeout=90)
    content_scope = next(
        field for field in app.checkbox if field.label == "Content words only"
    )
    assert not content_scope.disabled
    content_scope.set_value(True)
    app.run(timeout=90)
    _button(app, "Analyze this text").click()
    app.run(timeout=90)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert [tab.label for tab in app.tabs] == [
        "Overview",
        "Language Profile",
        "Concreteness Profile",
        "Frequency & Rarity",
        "Age of Acquisition",
        "Pronunciation & Prosody",
        "Meter & Rhythm",
        "Rhyme & Sound",
        "VAD Profile",
        "Emotion Profile",
        "Evidence",
        "Downloads",
        "How to Read",
    ]
    assert any(
        heading.value == "SUBTLEX-US Lexical Frequency & Rarity"
        for heading in app.subheader
    )
    median_metric = next(
        metric for metric in app.metric if metric.label == "Median Zipf (primary)"
    )
    assert median_metric.value != "—"
    assert any(
        "Content words only" in caption.value for caption in app.caption
    )


def test_interface_runs_optional_aoa_profile_and_contextual_scope_if_present() -> None:
    resource = (
        APP_PATH.parents[3]
        / "resources"
        / "kuperman_2013_erratum_ESM1_official.xlsx"
    )
    if not resource.is_file():
        return

    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    title = next(
        field
        for field in app.text_input
        if field.label == "Poem title or working label"
    )
    title.input("AoA interface validation")
    app.text_area[0].input("The stone and slowly bending grass.")
    app.multiselect[0].set_value([])
    aoa = next(
        field
        for field in app.checkbox
        if field.label
        == "Age of Acquisition profile (Kuperman et al. ratings)"
    )
    assert not aoa.disabled
    aoa.set_value(True)
    app.run(timeout=90)
    content_scope = next(
        field
        for field in app.checkbox
        if field.label == "AoA content words only"
    )
    assert not content_scope.disabled
    content_scope.set_value(True)
    app.run(timeout=90)
    _button(app, "Analyze this text").click()
    app.run(timeout=90)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert any(
        heading.value == "Normative Lexical Age of Acquisition"
        for heading in app.subheader
    )
    mean_metric = next(
        metric for metric in app.metric if metric.label == "Mean normative AoA"
    )
    assert mean_metric.value != "â€”"
    assert any(
        "Content words only" in caption.value for caption in app.caption
    )
    assert any(
        "not diagnostic of cognitive impairment" in warning.value
        for warning in app.warning
    )


def test_interface_runs_optional_pronunciation_and_override_workflow() -> None:
    resource_root = APP_PATH.parents[3] / "resources" / "pronunciation"
    if not all(
        (resource_root / filename).is_file()
        for filename in ("cmudict.dict", "cmudict.phones", "cmudict.symbols")
    ):
        return

    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    title = next(
        field
        for field in app.text_input
        if field.label == "Poem title or working label"
    )
    title.input("Pronunciation interface validation")
    app.text_area[0].input("The permit rings.\nStone.")
    app.multiselect[0].set_value([])
    pronunciation = next(
        field
        for field in app.checkbox
        if field.label == "Pronunciation & prosody foundation (CMUdict)"
    )
    assert not pronunciation.disabled
    pronunciation.set_value(True)
    app.run(timeout=90)
    overrides = next(
        field
        for field in app.text_area
        if field.label == "Poem-specific pronunciation overrides"
    )
    overrides.input(
        "the = DH AH0 | unstressed article in this reading\n"
        "permit = P ER0 M IH1 T | noun reading"
    )
    app.run(timeout=90)
    _button(app, "Analyze this text").click()
    app.run(timeout=90)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert any(
        heading.value == "Dictionary Pronunciation, Syllables & Lexical Stress"
        for heading in app.subheader
    )
    coverage = next(
        metric for metric in app.metric if metric.label == "Resolved coverage"
    )
    assert coverage.value == "100.0%"
    assert any(
        "CMUdict supplies North American dictionary pronunciations"
        in warning.value
        for warning in app.warning
    )


def test_interface_runs_fixed_meter_workflow() -> None:
    resource_root = APP_PATH.parents[3] / "resources" / "pronunciation"
    if not all(
        (resource_root / filename).is_file()
        for filename in ("cmudict.dict", "cmudict.phones", "cmudict.symbols")
    ):
        return

    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    title = next(
        field
        for field in app.text_input
        if field.label == "Poem title or working label"
    )
    title.input("Fixed meter interface validation")
    tetrameter = "the stone the stone the stone the stone"
    app.text_area[0].input("\n".join((tetrameter,) * 4))
    app.multiselect[0].set_value([])
    meter = next(
        field
        for field in app.checkbox
        if field.label == "Meter & rhythmic regularity"
    )
    assert not meter.disabled
    meter.set_value(True)
    app.run(timeout=90)
    _button(app, "Analyze this text").click()
    app.run(timeout=90)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert any(
        heading.value == "Candidate Meter & Rhythmic Regularity"
        for heading in app.subheader
    )
    nearest = next(
        metric for metric in app.metric if metric.label == "Nearest candidate"
    )
    assert nearest.value == "Iambic tetrameter"
    assert any(
        "nearest configured candidates" in warning.value.lower()
        for warning in app.warning
    )


def test_interface_runs_rhyme_and_sound_workflow() -> None:
    resource_root = APP_PATH.parents[3] / "resources" / "pronunciation"
    if not all(
        (resource_root / filename).is_file()
        for filename in ("cmudict.dict", "cmudict.phones", "cmudict.symbols")
    ):
        return

    app = AppTest.from_file(str(APP_PATH), default_timeout=90).run()
    title = next(
        field
        for field in app.text_input
        if field.label == "Poem title or working label"
    )
    title.input("Rhyme interface validation")
    app.text_area[0].input(
        "The bright cat\nA silver night\nThe soft hat\nA quiet light"
    )
    app.multiselect[0].set_value([])
    rhyme = next(
        field
        for field in app.checkbox
        if field.label == "Rhyme & phonological patterns"
    )
    assert not rhyme.disabled
    rhyme.set_value(True)
    app.run(timeout=90)
    _button(app, "Analyze this text").click()
    app.run(timeout=90)

    assert not app.exception
    assert any("Analysis complete" in message.value for message in app.success)
    assert any(
        heading.value == "Rhyme & Recurring Phonological Patterns"
        for heading in app.subheader
    )
    scheme = next(
        metric for metric in app.metric if metric.label == "Whole-poem scheme"
    )
    assert scheme.value == "ABAB"
    assert any(
        "dictionary- and spelling-based" in warning.value
        for warning in app.warning
    )


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
