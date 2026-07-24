from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from versevad.core import ModuleInput
from versevad.exports.pronunciation import (
    export_pronunciation_bundle,
    export_pronunciation_json,
    export_pronunciation_lines_csv,
    export_pronunciation_token_audit_csv,
)
from versevad.preprocessing import create_text_document
from versevad.prosody.pronunciation import PronunciationConfiguration
from tests.test_pronunciation import _module


def _result(tmp_path: Path, preprocessor):
    poem = preprocessor.process_document(
        create_text_document(
            "pronunciation-export",
            "Pronunciation export",
            "stone quorvax\nwind rings",
        )
    )
    return _module(tmp_path).analyze_detailed(
        ModuleInput.from_poem_document(poem),
        PronunciationConfiguration(),
    )


def _csv_rows(content: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


def test_pronunciation_exports_preserve_candidates_and_missing_values(
    tmp_path: Path,
    preprocessor,
) -> None:
    result = _result(tmp_path, preprocessor)
    audit = _csv_rows(export_pronunciation_token_audit_csv(result))
    lines = _csv_rows(export_pronunciation_lines_csv(result))

    unmatched = next(row for row in audit if row["surface_form"] == "quorvax")
    assert unmatched["status"] == "unmatched"
    assert unmatched["resolved_syllable_count"] == ""
    wind = next(row for row in audit if row["surface_form"] == "wind")
    assert wind["dictionary_candidate_count"] == "2"
    assert "W IH1 N D" in wind["dictionary_candidate_phones"]
    assert lines[0]["is_complete"] == "False"
    assert lines[0]["syllable_count"] == ""
    assert lines[1]["syllable_count"] == "2"


def test_pronunciation_json_and_bundle_are_complete_and_deterministic(
    tmp_path: Path,
    preprocessor,
) -> None:
    result = _result(tmp_path, preprocessor)
    first = export_pronunciation_json(result)
    second = export_pronunciation_json(result)
    payload = json.loads(first)
    bundle = export_pronunciation_bundle(result)

    assert first == second
    assert payload["module_result"]["module_name"] == "pronunciation_prosody_foundation"
    assert payload["token_audit"][1]["status"] == "unmatched"
    assert set(bundle) == {
        "pronunciation_summary.csv",
        "pronunciation_lines.csv",
        "pronunciation_types.csv",
        "pronunciation_token_audit.csv",
        "pronunciation_result.json",
    }
