"""Hand-calculated synthetic checks for performance-aware meter."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from versevad.core import ModuleInput
from versevad.models import PreprocessingMetadata, TextDocument, TokenRecord
from versevad.prosody.meter import (
    MeterAnalysisMode,
    MeterConfiguration,
    MeterEstimator,
    MeterLineInput,
    StressSyllable,
    StressVariant,
)
from versevad.prosody.performance_meter import (
    analyze_performance_aware_meter,
)


@dataclass(frozen=True)
class PerformanceMeterValidationReport:
    alternating_sequence: str
    analyzed_lines: int
    fixed_candidate_labels: tuple[str, ...]
    realized_candidate_labels: tuple[str, ...]
    lexical_stress_preserved: bool
    named_stanza_form_absent: bool


def _line(stress: str, line_number: int) -> MeterLineInput:
    syllables = tuple(
        StressSyllable(
            stress_digit=digit,
            token_id=f"token-{line_number}-{index}",
            surface_form=f"w{line_number}_{index}",
            part_of_speech="NOUN",
            word_index=index,
            syllable_index_in_word=0,
        )
        for index, digit in enumerate(stress, start=1)
    )
    return MeterLineInput(
        line_id=f"line-{line_number}",
        line_number=line_number,
        stanza_number=1,
        source_text=" ".join(item.surface_form for item in syllables),
        eligible_token_count=len(syllables),
        supported_token_count=len(syllables),
        missing_forms=(),
        stress_variants=(
            StressVariant(
                variant_id=f"line-{line_number}-variant",
                syllables=syllables,
                word_stress_sequence=" | ".join(stress),
                pronunciation_choices=tuple(
                    f"{item.surface_form}={item.stress_digit}"
                    for item in syllables
                ),
            ),
        ),
    )


def _module_input(lines: tuple[MeterLineInput, ...]) -> ModuleInput:
    text = "\n".join(line.source_text for line in lines)
    text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    document = TextDocument(
        text_id="performance-meter-validation",
        title="Synthetic performance-aware meter validation",
        original_text=text,
        text_sha256=text_sha256,
        text_version_id=f"performance-meter-validation:{text_sha256[:12]}",
    )
    tokens = []
    position = 0
    offset = 0
    for line in lines:
        for syllable in line.stress_variants[0].syllables:
            surface = syllable.surface_form
            tokens.append(
                TokenRecord(
                    token_id=syllable.token_id,
                    text_id=document.text_id,
                    text_version_id=document.text_version_id,
                    section_number=1,
                    stanza_number=1,
                    line_number=line.line_number,
                    token_position=position,
                    sentence_number=None,
                    token_position_in_sentence=None,
                    character_start=offset,
                    character_end=offset + len(surface),
                    surface_form=surface,
                    lowercase_form=surface,
                    punctuation_stripped_form=surface,
                    normalized_form=surface,
                    part_of_speech="NOUN",
                    lemma=surface,
                    normalized_lemma=surface,
                    morphological_features="",
                    is_punctuation=False,
                    is_numeric=False,
                    is_proper_noun=False,
                    is_stopword=False,
                    context=line.source_text,
                )
            )
            position += 1
            offset += len(surface) + 1
        offset += 1
    return ModuleInput(
        document=document,
        tokens=tuple(tokens),
        preprocessing=PreprocessingMetadata(
            recipe_id="synthetic-performance-meter-v1",
            pipeline_name="hand-calculated",
            pipeline_version="1",
            disabled_components=(),
        ),
    )


def run_synthetic_performance_meter_validation(
) -> tuple[PerformanceMeterValidationReport, tuple[str, ...]]:
    """Validate recurrence and lexical-stress safeguards without external data."""

    inputs = tuple(
        _line(stress, line_number)
        for line_number, stress in enumerate(
            ("01010101", "010101", "01010101", "010101"),
            start=1,
        )
    )
    configuration = MeterConfiguration(
        analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
    )
    estimator = MeterEstimator(configuration)
    fixed = tuple(estimator.evaluate_line(line) for line in inputs)
    realized = analyze_performance_aware_meter(
        _module_input(inputs),
        fixed,
        configuration,
    )
    fixed_labels = tuple(
        line.closest_candidate.label if line.closest_candidate else ""
        for line in fixed
    )
    realized_labels = tuple(
        (
            line.primary_realization.candidate_label
            if line.primary_realization
            else ""
        )
        for line in realized.line_results
    )
    preserved = all(
        (
            line.primary_realization is not None
            and line.raw_lexical_stress
            == line.primary_realization.lexical_stress
        )
        for line in realized.line_results
    )
    serialized_words = " ".join(
        (
            realized.poem_summary.generic_composite_pattern,
            *realized.methodology,
        )
    ).casefold()
    report = PerformanceMeterValidationReport(
        alternating_sequence=(
            realized.poem_summary.generic_composite_pattern
        ),
        analyzed_lines=realized.poem_summary.analyzable_line_count,
        fixed_candidate_labels=fixed_labels,
        realized_candidate_labels=realized_labels,
        lexical_stress_preserved=preserved,
        named_stanza_form_absent="common meter" not in serialized_words,
    )
    problems = []
    if report.analyzed_lines != 4:
        problems.append("Expected all four synthetic lines to be analyzable.")
    if report.fixed_candidate_labels != (
        "Iambic tetrameter",
        "Iambic trimeter",
        "Iambic tetrameter",
        "Iambic trimeter",
    ):
        problems.append("Fixed candidate sequence changed unexpectedly.")
    if "Recurring alternating sequence" not in report.alternating_sequence:
        problems.append("Generic alternating sequence was not reported.")
    if not report.lexical_stress_preserved:
        problems.append("Realization changed the retained lexical stress path.")
    if not report.named_stanza_form_absent:
        problems.append("A removed named stanza-form label reappeared.")
    return report, tuple(problems)
