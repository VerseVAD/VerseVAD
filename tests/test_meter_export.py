from __future__ import annotations

import csv
import io
import json

from versevad.core import ModuleInput
from versevad.exports.meter import (
    export_meter_alignment_operations_csv,
    export_meter_bundle,
    export_meter_json,
    export_meter_lines_csv,
)
from versevad.preprocessing import create_text_document
from versevad.prosody.meter import MeterModule
from versevad.prosody.pronunciation import PronunciationConfiguration
from tests.test_pronunciation import _module


def _rows(content: bytes) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    )


def _fixed_meter_text() -> str:
    tetrameter = "the stone the stone the stone the stone"
    return "\n".join((tetrameter, tetrameter, tetrameter, tetrameter))


def _result(tmp_path, preprocessor):
    poem = preprocessor.process_document(
        create_text_document(
            "meter-export",
            "Meter export",
            _fixed_meter_text(),
        )
    )
    pronunciation = _module(tmp_path).analyze_detailed(
        ModuleInput.from_poem_document(poem),
        PronunciationConfiguration(),
    )
    return MeterModule().analyze_detailed(
        ModuleInput.from_poem_document(poem),
        pronunciation,
    )


def test_meter_exports_preserve_fixed_candidates_and_alignment_audit(
    tmp_path,
    preprocessor,
) -> None:
    result = _result(tmp_path, preprocessor)

    lines = _rows(export_meter_lines_csv(result))
    operations = _rows(export_meter_alignment_operations_csv(result))

    assert len(lines) == 4
    assert {row["status"] for row in lines} == {"analyzed"}
    assert {row["closest_candidate"] for row in lines} == {"Iambic tetrameter"}
    assert {float(row["fit_score"]) for row in lines} == {1.0}
    assert "common_meter_line_fit" not in lines[0]
    assert operations
    assert {"observed_stress", "template_stress", "cost"} <= set(
        operations[0]
    )


def test_meter_json_and_bundle_are_complete_and_deterministic(
    tmp_path,
    preprocessor,
) -> None:
    result = _result(tmp_path, preprocessor)

    first = export_meter_json(result)
    second = export_meter_json(result)
    payload = json.loads(first)
    bundle = export_meter_bundle(result)

    assert first == second
    assert payload["summary"]["closest_candidate_kind"] == (
        "fixed pattern and foot count"
    )
    assert payload["summary"]["closest_candidate_label"] == "Iambic tetrameter"
    assert set(bundle) == {
        "meter_summary.csv",
        "meter_candidates.csv",
        "meter_lines.csv",
        "meter_alignment_operations.csv",
        "meter_result.json",
    }
