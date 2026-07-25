import csv
from pathlib import Path

from versevad.analysis.phase2 import analyze_lexicon, compare_lexicons
from versevad.exports.phase2_csv import export_phase2_csv
from versevad.phase2_validation import (
    phase2_synthetic_emotion_lexicon,
    phase2_synthetic_intensity_lexicon,
    phase2_synthetic_vad_lexicon,
)
from versevad.preprocessing import create_text_document


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def test_phase2_bundle_is_traceable_and_contains_no_consensus(preprocessor, tmp_path) -> None:
    document = create_text_document(
        "phase2-export", "Phase 2 export", "Fear joy dark night."
    )
    results = (
        analyze_lexicon(document, phase2_synthetic_vad_lexicon(), preprocessor),
        analyze_lexicon(document, phase2_synthetic_emotion_lexicon(), preprocessor),
        analyze_lexicon(document, phase2_synthetic_intensity_lexicon(), preprocessor),
    )
    comparison = compare_lexicons(results)
    paths = export_phase2_csv(results, comparison, tmp_path)
    assert len(paths) == 7
    assert all(path.is_file() for path in paths)
    assert all(
        path.read_bytes().startswith(b"\xef\xbb\xbf")
        for path in paths
        if path.suffix == ".csv"
    )

    audit = _rows(tmp_path / "phase2_match_audit.csv")
    assert any(
        row["surface_span"] == "dark night"
        and row["match_method"] == "exact_phrase"
        and row["included"] == "True"
        for row in audit
    )
    assert any(row["selection"] == "suppressed_component" for row in audit)
    assert {
        "stopword_status",
        "included_in_all_matched",
        "included_in_stopword_excluded",
        "stopword_exclusion_reason",
    }.issubset(audit[0])

    manifest = _rows(tmp_path / "phase2_manifest.csv")
    assert len(manifest) == 3
    assert {row["phrase_policy"] for row in manifest} == {"phrase_preferred"}
    assert all(row["source_sha256"] for row in manifest)
    assert {row["stopword_source"] for row in manifest} == {
        "spaCy English STOP_WORDS"
    }

    assert not any(path.suffix == ".json" for path in paths)

    comparison_rows = _rows(tmp_path / "phase2_cross_lexicon_comparison.csv")
    assert comparison_rows
    assert "consensus_score" not in comparison_rows[0]
    assert {row["lexicon_id"] for row in comparison_rows} == {
        result.lexicon_metadata.lexicon_id for result in results
    }


def test_phase2_export_can_replace_its_previous_bundle(preprocessor, tmp_path) -> None:
    document = create_text_document("phase2-replace", "Replace", "Dark night.")
    result = analyze_lexicon(document, phase2_synthetic_vad_lexicon(), preprocessor)
    comparison = compare_lexicons((result,))
    first = export_phase2_csv((result,), comparison, tmp_path)
    second = export_phase2_csv((result,), comparison, tmp_path)
    assert first == second
    assert _rows(tmp_path / "phase2_coverage.csv")[0]["matched_token_count"] == "2"
