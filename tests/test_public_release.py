from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_public_release_declares_canonical_gpl3_only() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

    assert project["license"] == "GPL-3.0-only"
    assert project["license-files"] == ["LICENSE"]
    assert "GNU GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 29 June 2007" in license_text
    assert "END OF TERMS AND CONDITIONS" in license_text


def test_public_repository_excludes_research_and_private_data() -> None:
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for required in (
        "/source_lexicons/",
        "/resources/**",
        "/.uv-cache/",
        "/corpora/",
        "/source_texts/",
        "/projects/",
        "/exports/",
        "/backups/",
        "*.sqlite3",
    ):
        assert required in ignored
    assert "!/resources/README.md" in ignored


def test_source_distribution_excludes_local_and_research_state() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    excluded = set(
        metadata["tool"]["hatch"]["build"]["targets"]["sdist"]["exclude"]
    )

    assert {
        "/.runtime",
        "/.tools",
        "/.uv-cache",
        "/.venv",
        "/backups",
        "/corpora",
        "/data",
        "/dist",
        "/exports",
        "/projects",
        "/resources",
        "/source_lexicons",
        "/source_texts",
    }.issubset(excluded)


def test_resource_guide_contains_every_runtime_destination_and_license_boundary() -> None:
    guide = (ROOT / "docs" / "resource-installation.md").read_text(
        encoding="utf-8"
    )

    for required in (
        "Ratings_Warriner_et_al.csv",
        "NRC-VAD-Lexicon.txt",
        "NRC-VAD-Lexicon-v2.1.txt",
        "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
        "NRC-Emotion-Intensity-Lexicon-v1.txt",
        "brysbaert_warriner_kuperman_concreteness_DATA.xlsx",
        "SUBTLEX-US frequency list with PoS and Zipf information.xlsx",
        "kuperman_2013_erratum_ESM1_official.xlsx",
        "cmudict.dict",
        "cmudict.phones",
        "cmudict.symbols",
        "GPL-3.0-only",
        "never downloads",
    ):
        assert required in guide


def test_user_facing_sources_use_versevad_folder_name() -> None:
    paths = (
        ROOT / "README.md",
        ROOT / "docs" / "user-guide.md",
        ROOT / "docs" / "phase1-validation.md",
        ROOT / "docs" / "phase2-validation.md",
        ROOT / "docs" / "VerseVAD_User_Manual_Source.md",
        ROOT / "setup_windows.bat",
        ROOT / "start_versevad.bat",
        ROOT / "scripts" / "setup_windows.ps1",
    )

    assert all(
        "ANEW VAD Study" not in path.read_text(encoding="utf-8")
        for path in paths
    )
