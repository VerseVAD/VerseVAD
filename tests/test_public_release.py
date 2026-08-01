from __future__ import annotations

import re
import tomllib
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).parents[1]


def test_public_release_version_is_consistent() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    package_source = (ROOT / "src" / "versevad" / "__init__.py").read_text(
        encoding="utf-8"
    )
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")

    assert metadata["project"]["version"] == "1.0.0"
    assert re.search(r'^__version__ = "1\.0\.0"$', package_source, re.MULTILINE)
    assert re.search(
        r'\[\[package\]\]\s+name = "versevad"\s+version = "1\.0\.0"',
        lock,
    )
    assert re.search(r'^version: "1\.0\.0"$', citation, re.MULTILINE)


def test_citation_metadata_names_release_and_author_without_placeholders() -> None:
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")

    for required in (
        'cff-version: "1.2.0"',
        "type: software",
        'title: "VerseVAD"',
        'given-names: "Nicky"',
        'family-names: "Bennett"',
        'license: "GPL-3.0-only"',
        'repository-code: "https://github.com/VerseVAD/VerseVAD"',
        'date-released: "2026-07-24"',
    ):
        assert required in citation
    assert "doi:" not in citation
    assert "TODO" not in citation
    assert "PLACEHOLDER" not in citation


def test_public_package_metadata_names_creator_and_canonical_urls() -> None:
    metadata = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]

    assert project["authors"] == [{"name": "Nicky Bennett"}]
    assert project["urls"] == {
        "Homepage": "https://github.com/VerseVAD/VerseVAD",
        "Documentation": (
            "https://github.com/VerseVAD/VerseVAD/blob/main/docs/index.md"
        ),
        "Repository": "https://github.com/VerseVAD/VerseVAD.git",
        "Issues": "https://github.com/VerseVAD/VerseVAD/issues",
    }


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
        "/private_training/",
        "*.sqlite3",
    ):
        assert required in ignored
    assert "!/resources/README.md" in ignored
    assert "!/resources/training/**" in ignored


def test_public_training_package_contains_only_learner_materials() -> None:
    training_root = ROOT / "resources" / "training"
    expected = {
        "VerseVAD_Foundations_Learner_Manual.docx",
        "VerseVAD_Foundations_Applied_Analysis_Assignment.docx",
        "VerseVAD_Analyst_Level_1_Learner_Manual.docx",
        "VerseVAD_Analyst_Level_1_Applied_Assignment.docx",
        "VerseVAD_Analyst_Level_2_Learner_Manual.docx",
        "VerseVAD_Analyst_Level_2_Applied_Assignment.docx",
        "VerseVAD_Authorized_Instructor_Learner_Manual.docx",
        "VerseVAD_Authorized_Instructor_Applied_Assignment.docx",
    }
    packaged = {path.name for path in training_root.glob("*.docx")}

    assert packaged == expected
    assert not any(
        marker in path.name.casefold()
        for path in training_root.rglob("*")
        for marker in ("answer", "key", "rubric")
    )
    assert all(path.stat().st_size > 0 for path in training_root.glob("*.docx"))


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
        "/private_training",
        "/projects",
        "/source_lexicons",
        "/source_texts",
    }.issubset(excluded)
    assert "/resources" not in excluded


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
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "resource-installation.md",
        ROOT / "docs" / "VerseVAD_User_Manual_Source.md",
        ROOT / "setup_windows.bat",
        ROOT / "start_versevad.bat",
        ROOT / "scripts" / "setup_windows.ps1",
        ROOT / "setup_macos.command",
        ROOT / "start_versevad.command",
        ROOT / "diagnose_macos.command",
    )

    assert all(
        "ANEW VAD Study" not in path.read_text(encoding="utf-8")
        for path in paths
    )


def test_public_release_uses_organization_repository_urls() -> None:
    expected = "https://github.com/VerseVAD/VerseVAD"
    paths = (
        ROOT / "README.md",
        ROOT / "CITATION.cff",
        ROOT / "pyproject.toml",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "updating.md",
        ROOT / "src" / "versevad" / "application.py",
    )

    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert expected in text
        assert "github.com/nickybennett/VerseVAD" not in text


def test_public_documentation_has_no_broken_local_links() -> None:
    markdown_paths = (
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "resources" / "README.md",
        *sorted((ROOT / "docs").glob("*.md")),
    )
    broken: list[str] = []
    pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")

    for markdown_path in markdown_paths:
        text = markdown_path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            raw_target = match.group(1).strip()
            target = raw_target.split(maxsplit=1)[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith("#"):
                continue
            relative_path = unquote(parsed.path)
            if not relative_path:
                continue
            resolved = (markdown_path.parent / relative_path).resolve()
            if not resolved.exists():
                broken.append(
                    f"{markdown_path.relative_to(ROOT)} -> {raw_target}"
                )

    assert broken == []


def test_public_documentation_excludes_historical_stage_artifacts() -> None:
    assert not (ROOT / "PLANS.md").exists()
    assert not (ROOT / "test_phase1.bat").exists()
    assert not (ROOT / "test_phase2.bat").exists()

    historical_patterns = (
        "phase*-validation.md",
        "poetic-fingerprint-stage*.md",
        "design-stage*.md",
        "inherited-form-stage*.md",
        "stage14-*.md",
        "stage14-*.json",
    )
    for pattern in historical_patterns:
        assert list((ROOT / "docs").glob(pattern)) == []

    maintained = {
        "index.md",
        "user-guide.md",
        "methodology.md",
        "resource-installation.md",
        "lexicons.md",
        "architecture.md",
        "data-model.md",
        "testing.md",
    }
    assert maintained.issubset(
        {path.name for path in (ROOT / "docs").glob("*.md")}
    )
