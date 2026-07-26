from __future__ import annotations

import csv
import io

from versevad.core import ModuleInput
from versevad.exports.lexical_style import export_lexical_style_bundle
from versevad.lexical_style import LexicalStyleConfiguration, LexicalStyleModule
from versevad.preprocessing import create_text_document


def _rows(content: bytes) -> list[dict[str, str]]:
    return list(
        csv.DictReader(
            io.StringIO(content.decode("utf-8-sig")),
        )
    )


def test_lexical_style_bundle_is_complete_and_auditable(preprocessor) -> None:
    poem = preprocessor.process_document(
        create_text_document(
            "lexical-export",
            "Lexical export",
            "red blue red\ngreen blue\n\nyellow red",
        )
    )
    result = LexicalStyleModule().analyze_detailed(
        ModuleInput.from_poem_document(poem),
        LexicalStyleConfiguration(
            mattr_window_size=3,
            hdd_sample_size=3,
        ),
    )

    bundle = export_lexical_style_bundle(result)

    assert set(bundle) == {
        "lexical_style_summary.csv",
        "lexical_style_word_lengths.csv",
        "lexical_style_lines.csv",
        "lexical_style_stanzas.csv",
        "lexical_style_token_audit.csv",
        "lexical_style_manifest.csv",
        "lexical_style_report.docx",
    }
    summary = _rows(bundle["lexical_style_summary.csv"])
    assert any(
        row["metric"] == "moving_average_type_token_ratio"
        and row["value"] == str(result.summary.mattr)
        for row in summary
    )
    summary_by_metric = {row["metric"]: row for row in summary}
    assert summary_by_metric["line_word_count_mean"]["value"] == str(7 / 3)
    assert summary_by_metric[
        "line_word_count_population_standard_deviation"
    ]["value"] == str((2 / 9) ** 0.5)
    assert summary_by_metric["stanza_word_count_mean"]["value"] == "3.5"
    assert summary_by_metric[
        "stanza_word_count_population_standard_deviation"
    ]["value"] == "1.5"
    assert summary_by_metric["stanza_line_count_mean"]["value"] == "1.5"
    assert summary_by_metric[
        "stanza_line_count_population_standard_deviation"
    ]["value"] == "0.5"
    lines = _rows(bundle["lexical_style_lines.csv"])
    assert [row["word_count"] for row in lines] == ["3", "2", "0", "2"]
    stanzas = _rows(bundle["lexical_style_stanzas.csv"])
    assert [row["word_count"] for row in stanzas] == ["5", "2"]
    audit = _rows(bundle["lexical_style_token_audit.csv"])
    assert audit[0]["surface_form"] == "red"
    assert audit[0]["normalized_surface_type"] == "red"
    assert bundle["lexical_style_report.docx"].startswith(b"PK")
    assert not any(name.endswith(".json") for name in bundle)
