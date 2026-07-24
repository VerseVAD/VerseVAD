from __future__ import annotations

import pytest

from versevad.prosody.meter import (
    FOOT_COUNT_NAMES,
    FootPattern,
    MeterConfiguration,
    MeterEstimator,
    MeterLineInput,
    MeterLineStatus,
    StressSyllable,
    StressVariant,
    candidate_templates,
    summarize_meter_lines,
)


def _line(
    stress: str,
    *,
    line_number: int = 1,
    stanza_number: int = 1,
    part_of_speech: str = "NOUN",
) -> MeterLineInput:
    syllables = tuple(
        StressSyllable(
            stress_digit=digit,
            token_id=f"token-{index + 1}",
            surface_form=f"w{index + 1}",
            part_of_speech=part_of_speech,
            word_index=index,
            syllable_index_in_word=0,
        )
        for index, digit in enumerate(stress)
    )
    return MeterLineInput(
        line_id=f"line-{line_number}",
        line_number=line_number,
        stanza_number=stanza_number,
        source_text=stress,
        eligible_token_count=len(stress),
        supported_token_count=len(stress),
        missing_forms=(),
        stress_variants=(
            StressVariant(
                variant_id=f"line-{line_number}-variant-1",
                syllables=syllables,
                word_stress_sequence=" | ".join(stress),
                pronunciation_choices=tuple(
                    f"w{index + 1}={digit}"
                    for index, digit in enumerate(stress)
                ),
            ),
        ),
    )


def _fit(stress: str):
    return MeterEstimator(MeterConfiguration()).evaluate_line(_line(stress))


def test_candidate_inventory_crosses_five_patterns_with_one_to_eight_feet() -> None:
    templates = candidate_templates(MeterConfiguration())

    assert len(templates) == 40
    assert {item.pattern for item in templates} == {
        FootPattern.IAMBIC,
        FootPattern.TROCHAIC,
        FootPattern.ANAPESTIC,
        FootPattern.DACTYLIC,
        FootPattern.AMPHIBRACHIC,
    }
    assert {item.foot_count for item in templates} == set(range(1, 9))
    assert FOOT_COUNT_NAMES[1] == "monometer"
    assert FOOT_COUNT_NAMES[5] == "pentameter"
    assert FOOT_COUNT_NAMES[7] == "heptameter"
    assert FOOT_COUNT_NAMES[8] == "octameter"


@pytest.mark.parametrize(
    ("stress", "pattern", "feet", "label"),
    [
        ("01" * 5, FootPattern.IAMBIC, 5, "Iambic pentameter"),
        ("10" * 4, FootPattern.TROCHAIC, 4, "Trochaic tetrameter"),
        ("001" * 3, FootPattern.ANAPESTIC, 3, "Anapestic trimeter"),
        ("100" * 6, FootPattern.DACTYLIC, 6, "Dactylic hexameter"),
        ("010" * 3, FootPattern.AMPHIBRACHIC, 3, "Amphibrachic trimeter"),
    ],
)
def test_regular_patterns_receive_exact_candidate_fits(
    stress: str,
    pattern: FootPattern,
    feet: int,
    label: str,
) -> None:
    result = _fit(stress)

    assert result.status is MeterLineStatus.ANALYZED
    assert result.closest_candidate is not None
    assert result.closest_candidate.pattern is pattern
    assert result.closest_candidate.foot_count == feet
    assert result.closest_candidate.label == label
    assert result.closest_candidate.fit_score == pytest.approx(1.0)
    assert result.closest_candidate.total_cost == pytest.approx(0.0)


def test_feminine_ending_initial_inversion_and_catalexis_are_not_plain_matches() -> None:
    feminine = _fit(("01" * 5) + "0").closest_candidate
    inversion = _fit("10" + ("01" * 4)).closest_candidate
    catalectic = _fit(("10" * 4)[:-1]).closest_candidate

    assert feminine is not None
    assert feminine.pattern is FootPattern.IAMBIC
    assert feminine.foot_count == 5
    assert feminine.feminine_ending_count == 1
    assert feminine.extra_syllable_count == 1
    assert feminine.fit_score < 1

    assert inversion is not None
    assert inversion.pattern is FootPattern.IAMBIC
    assert inversion.foot_count == 5
    assert inversion.initial_inversion_count == 1
    assert inversion.substitution_count == 0
    assert inversion.fit_score < 1

    assert catalectic is not None
    assert catalectic.pattern is FootPattern.TROCHAIC
    assert catalectic.foot_count == 4
    assert catalectic.catalectic_count == 1
    assert catalectic.omitted_syllable_count == 1
    assert catalectic.fit_score < 1


def test_spondee_and_pyrrhic_are_local_substitutions_not_base_meter_candidates() -> None:
    spondaic_line = _fit("0111010101")
    pyrrhic_line = _fit("0100010101")

    assert all(
        item.pattern not in {FootPattern.SPONDAIC, FootPattern.PYRRHIC}
        for item in spondaic_line.candidate_fits
    )
    assert spondaic_line.closest_candidate is not None
    assert spondaic_line.closest_candidate.pattern is FootPattern.IAMBIC
    assert spondaic_line.closest_candidate.spondee_substitution_count >= 1
    assert pyrrhic_line.closest_candidate is not None
    assert pyrrhic_line.closest_candidate.pattern is FootPattern.IAMBIC
    assert pyrrhic_line.closest_candidate.pyrrhic_substitution_count >= 1


def test_secondary_stress_and_function_word_promotion_have_configurable_costs() -> None:
    secondary = _fit("0201010101").closest_candidate
    function_line = _line("00", part_of_speech="DET")
    function_fit = MeterEstimator(MeterConfiguration()).evaluate_line(
        function_line
    ).closest_candidate
    content_fit = _fit("00").closest_candidate

    assert secondary is not None
    assert secondary.pattern is FootPattern.IAMBIC
    assert secondary.fit_score > 0.9
    assert function_fit is not None and content_fit is not None
    function_iamb = next(
        item
        for item in MeterEstimator(MeterConfiguration())
        .evaluate_line(function_line)
        .candidate_fits
        if item.pattern is FootPattern.IAMBIC and item.foot_count == 1
    )
    content_iamb = next(
        item
        for item in _fit("00").candidate_fits
        if item.pattern is FootPattern.IAMBIC and item.foot_count == 1
    )
    assert function_iamb.fit_score > content_iamb.fit_score


def test_missing_pronunciation_and_variant_limit_leave_line_fit_missing() -> None:
    missing = MeterLineInput(
        line_id="line-1",
        line_number=1,
        stanza_number=1,
        source_text="unknown word",
        eligible_token_count=2,
        supported_token_count=1,
        missing_forms=("unknown",),
        stress_variants=(),
    )
    variants = tuple(
        StressVariant(
            variant_id=f"variant-{index}",
            syllables=_line("01").stress_variants[0].syllables,
            word_stress_sequence="0 | 1",
            pronunciation_choices=(f"choice-{index}",),
        )
        for index in range(3)
    )
    too_many = MeterLineInput(
        line_id="line-2",
        line_number=2,
        stanza_number=1,
        source_text="ambiguous",
        eligible_token_count=1,
        supported_token_count=1,
        missing_forms=(),
        stress_variants=variants,
        variant_count_before_limit=3,
        variants_truncated=True,
    )
    estimator = MeterEstimator(MeterConfiguration(maximum_line_variants=2))

    missing_result = estimator.evaluate_line(missing)
    too_many_result = estimator.evaluate_line(too_many)

    assert missing_result.status is MeterLineStatus.MISSING_PRONUNCIATION
    assert missing_result.closest_candidate is None
    assert too_many_result.status is MeterLineStatus.TOO_MANY_VARIANTS
    assert too_many_result.closest_candidate is None


def test_line_candidate_ranking_is_deterministic_and_keeps_alternatives() -> None:
    estimator = MeterEstimator(MeterConfiguration())
    first = estimator.evaluate_line(_line("0101010101"))
    second = estimator.evaluate_line(_line("0101010101"))

    assert first == second
    assert len(first.candidate_fits) == 40
    assert first.candidate_fits[0] == first.closest_candidate
    assert first.alternative_candidates
    assert first.candidate_fits[0].fit_score >= first.candidate_fits[1].fit_score


def test_candidate_specific_pronunciation_path_does_not_change_line_evidence() -> None:
    regular = _line("01010101")
    alternate = StressVariant(
        variant_id="line-1-variant-irregular",
        syllables=_line("11111111").stress_variants[0].syllables,
        word_stress_sequence="1 | 1 | 1 | 1 | 1 | 1 | 1 | 1",
        pronunciation_choices=("invented irregular alternative",),
    )
    ambiguous_line = MeterLineInput(
        **{
            **regular.__dict__,
            "stress_variants": (alternate, regular.stress_variants[0]),
            "variant_count_before_limit": 2,
        }
    )

    result = MeterEstimator(MeterConfiguration()).evaluate_line(ambiguous_line)

    assert result.closest_candidate is not None
    assert result.closest_candidate.label == "Iambic tetrameter"
    assert result.closest_candidate.selected_variant_id == (
        regular.stress_variants[0].variant_id
    )
    assert result.pronunciation_variant_count == 2
    assert ambiguous_line.stress_variants[0] is alternate


def test_empty_and_mixed_lines_have_explicit_nonclassification_states() -> None:
    empty = MeterLineInput(
        line_id="line-empty",
        line_number=1,
        stanza_number=1,
        source_text="",
        eligible_token_count=0,
        supported_token_count=0,
        missing_forms=(),
        stress_variants=(),
        variant_count_before_limit=0,
    )
    estimator = MeterEstimator(MeterConfiguration())
    empty_result = estimator.evaluate_line(empty)
    mixed_lines = tuple(
        estimator.evaluate_line(item)
        for item in (
            _line("01010101", line_number=2),
            _line("100100100", line_number=3),
            _line("1110001", line_number=4),
        )
    )
    summary, _, _ = summarize_meter_lines(
        mixed_lines,
        MeterConfiguration(),
    )

    assert empty_result.status is MeterLineStatus.NO_LEXICAL_TOKENS
    assert empty_result.closest_candidate is None
    assert summary.assessment.value in {
        "mixed_line_lengths",
        "mixed_or_irregular",
    }


def test_common_meter_is_evaluated_as_iambic_4_3_4_3_scheme() -> None:
    configuration = MeterConfiguration()
    estimator = MeterEstimator(configuration)
    inputs = (
        _line("01" * 4, line_number=1, stanza_number=1),
        _line("01" * 3, line_number=2, stanza_number=1),
        _line("01" * 4, line_number=3, stanza_number=1),
        _line("01" * 3, line_number=4, stanza_number=1),
        _line("01" * 4, line_number=5, stanza_number=2),
        _line("01" * 3, line_number=6, stanza_number=2),
        _line("01" * 4, line_number=7, stanza_number=2),
        _line("01" * 3, line_number=8, stanza_number=2),
    )
    lines = tuple(estimator.evaluate_line(item) for item in inputs)

    summary, _, schemes = summarize_meter_lines(lines, configuration)

    assert schemes[0].scheme_id == "common_meter"
    assert schemes[0].foot_count_cycle == (4, 3, 4, 3)
    assert schemes[0].mean_fit == pytest.approx(1.0)
    assert schemes[0].matching_line_count == 8
    assert schemes[0].complete_stanza_count == 2
    assert summary.closest_candidate_kind == "alternating meter scheme"
    assert summary.closest_candidate_label == (
        "Common meter (alternating iambic tetrameter/trimeter)"
    )
