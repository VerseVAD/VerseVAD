from __future__ import annotations

import csv
import io

import pytest

from versevad.core import ModuleInput
from versevad.exports.meter import (
    export_meter_bundle,
    export_meter_realizations_csv,
)
from versevad.preprocessing import create_text_document
from versevad.prosody.meter import (
    MeterAnalysisMode,
    MeterConfiguration,
    MeterModule,
    MeterStyleProfile,
    parse_meter_scholar_revisions,
)
from versevad.prosody.performance_meter import (
    MetricalConfidence,
    RhythmicOrganization,
)
from versevad.prosody.pronunciation import PronunciationConfiguration
from tests.test_pronunciation import _module


def _analyze(
    tmp_path,
    preprocessor,
    text: str,
    configuration: MeterConfiguration,
):
    poem = preprocessor.process_document(
        create_text_document(
            "performance-meter",
            "Performance-aware meter",
            text,
        )
    )
    module_input = ModuleInput.from_poem_document(poem)
    pronunciation = _module(tmp_path).analyze_detailed(
        module_input,
        PronunciationConfiguration(),
    )
    return MeterModule().analyze_detailed(
        module_input,
        pronunciation,
        configuration,
    )


def _rows(content: bytes) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(content.decode("utf-8-sig"), newline=""))
    )


def test_performance_mode_preserves_fixed_candidate_layer(
    tmp_path,
    preprocessor,
) -> None:
    text = "\n".join(
        "the stone the stone the stone the stone" for _ in range(4)
    )
    fixed = _analyze(
        tmp_path,
        preprocessor,
        text,
        MeterConfiguration(),
    )
    realized = _analyze(
        tmp_path,
        preprocessor,
        text,
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
        ),
    )

    assert realized.line_results == fixed.line_results
    assert realized.candidate_summaries == fixed.candidate_summaries
    assert realized.summary == fixed.summary
    assert fixed.performance_aware is None
    assert realized.performance_aware is not None
    performance = realized.performance_aware
    assert performance.poem_summary.primary_meter == "Iambic tetrameter"
    assert performance.poem_summary.rhythmic_organization is (
        RhythmicOrganization.ACCENTUAL_SYLLABIC
    )
    assert performance.poem_summary.confidence in {
        MetricalConfidence.MODERATE,
        MetricalConfidence.STRONG,
    }
    for fixed_line, performance_line in zip(
        realized.line_results,
        performance.line_results,
        strict=True,
    ):
        assert fixed_line.closest_candidate is not None
        assert performance_line.primary_realization is not None
        assert performance_line.raw_lexical_stress == (
            performance_line.primary_realization.lexical_stress
        )
        assert fixed_line.closest_candidate.selected_stress_sequence == (
            "01010101"
        )


def test_declared_style_changes_interpretation_not_source_stress(
    tmp_path,
    preprocessor,
) -> None:
    text = "\n".join(
        (
            "stone the stone the stone the stone the",
            "the stone the stone the stone the stone",
            "stone the stone the stone the stone the",
            "the stone the stone the stone the stone",
        )
    )
    traditional = _analyze(
        tmp_path,
        preprocessor,
        text,
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
            style_profile=MeterStyleProfile.TRADITIONAL,
        ),
    )
    cadential = _analyze(
        tmp_path,
        preprocessor,
        text,
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
            style_profile=MeterStyleProfile.FREE_VERSE_CADENTIAL,
        ),
    )

    assert traditional.line_results == cadential.line_results
    assert traditional.performance_aware is not None
    assert cadential.performance_aware is not None
    assert [
        line.raw_lexical_stress
        for line in traditional.performance_aware.line_results
    ] == [
        line.raw_lexical_stress
        for line in cadential.performance_aware.line_results
    ]
    assert traditional.performance_aware.style_profile.profile is (
        MeterStyleProfile.TRADITIONAL
    )
    assert cadential.performance_aware.style_profile.profile is (
        MeterStyleProfile.FREE_VERSE_CADENTIAL
    )


def test_contextual_adjustments_and_caesura_are_explicit(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "the stone, the stone the stone the stone",
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.COMPARE_BOTH,
        ),
    )

    assert result.performance_aware is not None
    line = result.performance_aware.line_results[0]
    reading = line.primary_realization
    assert reading is not None
    assert reading.caesurae
    assert all(
        syllable.lexical_stress in {"0", "1", "2", None}
        for syllable in reading.syllables
    )
    assert all(
        substitution.kind
        in {
            "promotion",
            "demotion",
            "initial_inversion",
            "headless_line",
            "feminine_ending",
            "catalexis",
            "spondee",
            "pyrrhic",
            "extrametrical_syllable",
            "omitted_position",
            "visible_orthographic_elision",
        }
        for substitution in reading.substitutions
    )
    assert "||" in reading.realized_display


def test_performance_exports_are_auditable_and_exclude_named_common_meter(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "\n".join(
            "the stone the stone the stone the stone" for _ in range(4)
        ),
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
        ),
    )

    bundle = export_meter_bundle(result)
    rows = _rows(export_meter_realizations_csv(result))

    assert {
        "meter_realizations.csv",
        "meter_stanzas.csv",
        "meter_rhythm_trajectory.csv",
        "meter_report.docx",
    } <= set(bundle)
    assert not any(name.endswith((".json", ".txt", ".xlsx")) for name in bundle)
    assert rows
    assert {"primary", "alternate"} <= {
        row["reading_role"] for row in rows
    }
    assert "candidate_fit" in rows[0]
    assert "contextual_fit" in rows[0]


def test_performance_mode_retains_missing_evidence_as_missing(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "qzqxv",
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
        ),
    )

    assert result.performance_aware is not None
    assert result.performance_aware.poem_summary.confidence is (
        MetricalConfidence.INSUFFICIENT
    )
    assert result.performance_aware.line_results[0].primary_realization is None


def test_scholar_revision_remains_separate_from_automatic_reading(
    tmp_path,
    preprocessor,
) -> None:
    revisions = parse_meter_scholar_revisions(
        "line 1 = trochaic tetrameter | / x / x / x / x | "
        "alternate performance for comparison"
    )
    result = _analyze(
        tmp_path,
        preprocessor,
        "\n".join(
            "the stone the stone the stone the stone" for _ in range(4)
        ),
        MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
            scholar_revisions=revisions,
        ),
    )

    assert result.performance_aware is not None
    automatic = result.performance_aware.line_results[0].primary_realization
    revision = result.performance_aware.scholar_revisions[0]
    assert automatic is not None
    assert automatic.candidate_label == "Iambic tetrameter"
    assert revision.automatic_candidate == "Iambic tetrameter"
    assert revision.revised_candidate == "Trochaic tetrameter"
    assert revision.revised_scansion == "/ x / x / x / x"
    assert "meter_scholar_revisions.csv" in export_meter_bundle(result)


def test_scholar_revision_parser_requires_line_candidate_scansion_and_note() -> None:
    with pytest.raises(ValueError, match="must use"):
        parse_meter_scholar_revisions("line 2 = iambic pentameter")
