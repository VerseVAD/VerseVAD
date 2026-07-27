from __future__ import annotations

import csv
import io
import zipfile

from versevad.core import ModuleInput
from versevad.exports.inherited_form import export_inherited_form_bundle
from versevad.inherited_form import InheritedFormEngine
from versevad.preprocessing import create_text_document

from tests.test_inherited_form import _villanelle_text


def _rows(content: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


def test_inherited_form_bundle_is_csv_and_narrative_docx_only(
    preprocessor,
) -> None:
    poem = preprocessor.process_document(
        create_text_document(
            "form-export",
            "Form export",
            _villanelle_text(),
        )
    )
    result = InheritedFormEngine().analyze(
        ModuleInput.from_poem_document(poem),
        None,
        None,
        None,
    )

    bundle = export_inherited_form_bundle(
        result,
        text_title="Form export",
    )
    assert set(bundle) == {
        "inherited_form_summary.csv",
        "inherited_form_candidates.csv",
        "inherited_form_features.csv",
        "inherited_form_profiles.csv",
        "inherited_form_methodology.csv",
        "inherited_form_manifest.csv",
        "inherited_form_report.docx",
    }
    assert not any(name.endswith(".json") for name in bundle)
    assert all(
        content.startswith(b"\xef\xbb\xbf")
        for name, content in bundle.items()
        if name.endswith(".csv")
    )
    with zipfile.ZipFile(io.BytesIO(bundle["inherited_form_report.docx"])) as archive:
        assert "word/document.xml" in archive.namelist()
    summary = _rows(bundle["inherited_form_summary.csv"])[0]
    assert summary["best_candidate_id"] == "villanelle"
    assert "Traditionally:" in summary["suggestion_tooltip"]
    profiles = _rows(bundle["inherited_form_profiles.csv"])
    assert len(profiles) == 10
    assert all(row["source_urls"].startswith("https://") for row in profiles)


def test_inherited_form_word_export_is_deterministic(preprocessor) -> None:
    poem = preprocessor.process_document(
        create_text_document(
            "form-export-stable",
            "Stable form export",
            _villanelle_text(),
        )
    )
    result = InheritedFormEngine().analyze(
        ModuleInput.from_poem_document(poem),
        None,
        None,
        None,
    )

    first = export_inherited_form_bundle(result)
    second = export_inherited_form_bundle(result)
    assert first == second
