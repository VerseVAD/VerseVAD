from __future__ import annotations

import csv
import io

from versevad.core import ModuleInput
from versevad.exports.phonology import (
    export_phonological_bundle,
    export_phonological_sounds_csv,
    export_phonological_summary_csv,
    export_rhyme_lines_csv,
    export_rhyme_pairs_csv,
    export_rhyme_stanzas_csv,
)
from versevad.phonology import PhonologicalModule
from versevad.preprocessing import create_text_document
from versevad.prosody.pronunciation import PronunciationConfiguration
from tests.test_pronunciation import _module


def _rows(content: bytes) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    )


def _result(tmp_path, preprocessor):
    poem = preprocessor.process_document(
        create_text_document(
            "rhyme-export",
            "Rhyme export",
            "bright cat\nsilver night\nsoftly hat\nstone bright",
        )
    )
    pronunciation = _module(tmp_path).analyze_detailed(
        ModuleInput.from_poem_document(poem),
        PronunciationConfiguration(),
    )
    return PhonologicalModule().analyze_detailed(
        ModuleInput.from_poem_document(poem),
        pronunciation,
    )


def test_phonological_csv_exports_preserve_scheme_pairs_and_sounds(
    tmp_path,
    preprocessor,
) -> None:
    result = _result(tmp_path, preprocessor)

    summary = _rows(export_phonological_summary_csv(result))
    stanzas = _rows(export_rhyme_stanzas_csv(result))
    lines = _rows(export_rhyme_lines_csv(result))
    pairs = _rows(export_rhyme_pairs_csv(result))
    sounds = _rows(export_phonological_sounds_csv(result))

    scheme = next(
        row for row in summary if row["metric"] == "whole_poem_rhyme_scheme"
    )
    assert scheme["value"] == "ABAB"
    assert stanzas[0]["rhyme_scheme"] == "ABAB"
    assert [row["poem_scheme_label"] for row in lines] == ["A", "B", "A", "B"]
    assert any(row["relationship"] == "perfect" for row in pairs)
    assert {"initial_consonant", "stressed_vowel", "consonant"} <= {
        row["category"] for row in sounds
    }


def test_phonological_word_report_and_bundle_are_complete_and_deterministic(
    tmp_path,
    preprocessor,
) -> None:
    result = _result(tmp_path, preprocessor)

    bundle = export_phonological_bundle(result)
    second = export_phonological_bundle(result)

    assert bundle["rhyme_report.docx"] == second["rhyme_report.docx"]
    assert result.summary.whole_poem_rhyme_scheme == "ABAB"
    assert set(bundle) == {
        "rhyme_summary.csv",
        "rhyme_stanzas.csv",
        "rhyme_lines.csv",
        "rhyme_pairs.csv",
        "rhyme_internal.csv",
        "phonological_sounds.csv",
        "rhyme_manifest.csv",
        "rhyme_report.docx",
    }
    assert bundle["rhyme_report.docx"].startswith(b"PK")
    assert not any(name.endswith(".json") for name in bundle)
