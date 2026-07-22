from __future__ import annotations

import csv
from pathlib import Path

from versevad.analysis import analyze_vad
from versevad.exports import export_analysis_csv
from versevad.preprocessing import create_text_document
from versevad.validation import PHASE1_DEMO_TEXT, phase1_synthetic_lexicon


def test_csv_bundle_is_complete_and_traceable(tmp_path: Path, preprocessor) -> None:
    result = analyze_vad(
        create_text_document("export", "Export", PHASE1_DEMO_TEXT),
        phase1_synthetic_lexicon(),
        preprocessor,
    )

    created = export_analysis_csv(result, tmp_path)

    assert {path.name for path in created} == {
        "token_audit.csv",
        "coverage.csv",
        "vad_summary.csv",
        "analysis_manifest.csv",
    }
    with (tmp_path / "token_audit.csv").open(encoding="utf-8-sig", newline="") as source:
        audit = list(csv.DictReader(source))
    assert len(audit) == result.coverage.total_tokens
    assert all(row["analysis_id"] == result.analysis_id for row in audit)
    assert sum(row["included"] == "True" for row in audit) == 7

    with (tmp_path / "vad_summary.csv").open(encoding="utf-8-sig", newline="") as source:
        summary = list(csv.DictReader(source))
    assert len(summary) == 12
    assert {row["weighting"] for row in summary} == {"token", "type"}
    assert {row["scale"] for row in summary} == {"source", "normalized_0_1"}

    with (tmp_path / "analysis_manifest.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        manifest = {row["field"]: row["value"] for row in csv.DictReader(source)}
    assert manifest["text_sha256"] == result.document.text_sha256
    assert manifest["lexicon_sha256"] == result.lexicon_validation.source_sha256
    assert manifest["pipeline_name"] == "en_core_web_sm"


def test_empty_text_export_has_headers_and_missing_statistics(
    tmp_path: Path, preprocessor
) -> None:
    result = analyze_vad(
        create_text_document("empty", "Empty", ""),
        phase1_synthetic_lexicon(),
        preprocessor,
    )

    export_analysis_csv(result, tmp_path)

    with (tmp_path / "token_audit.csv").open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        assert "surface_form" in (reader.fieldnames or [])
        assert list(reader) == []
    with (tmp_path / "vad_summary.csv").open(encoding="utf-8-sig", newline="") as source:
        summary = list(csv.DictReader(source))
    valence = next(
        row
        for row in summary
        if row["weighting"] == "token"
        and row["scale"] == "source"
        and row["dimension"] == "valence"
    )
    assert valence["count"] == "0"
    assert valence["mean"] == ""
