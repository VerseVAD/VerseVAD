from __future__ import annotations

import pytest

from versevad.prosody.meter import (
    FootPattern,
    MeterAssessment,
    MeterConfiguration,
    MeterEstimator,
    MeterLineInput,
    MeterStyleProfile,
    StressSyllable,
    StressVariant,
    clear_meter_alignment_cache,
    meter_alignment_cache_info,
    summarize_meter_lines,
)


def _line(stress: str, line_number: int) -> MeterLineInput:
    syllables = tuple(
        StressSyllable(
            stress_digit=digit,
            token_id=f"token-{line_number}-{index}",
            surface_form=f"w{index}",
            part_of_speech="NOUN",
            word_index=index,
            syllable_index_in_word=0,
        )
        for index, digit in enumerate(stress)
    )
    variant = StressVariant(
        variant_id=f"variant-{line_number}",
        syllables=syllables,
        word_stress_sequence=" | ".join(stress),
        pronunciation_choices=tuple(
            f"w{index}={digit}" for index, digit in enumerate(stress)
        ),
    )
    return MeterLineInput(
        line_id=f"line-{line_number}",
        line_number=line_number,
        stanza_number=1,
        source_text=stress,
        eligible_token_count=len(stress),
        supported_token_count=len(stress),
        missing_forms=(),
        stress_variants=(variant,),
    )


@pytest.mark.parametrize(
    ("stress", "expected"),
    [
        (
            "0101010101",
            {
                "pattern": FootPattern.IAMBIC,
                "feet": 5,
                "cost": 0.0,
                "fit": 1.0,
                "inversion": 0,
                "extras": 0,
                "feminine": 0,
                "observed": "0101010101",
                "template": "0101010101",
            },
        ),
        (
            "1001010101",
            {
                "pattern": FootPattern.IAMBIC,
                "feet": 5,
                "cost": 0.25,
                "fit": 0.975,
                "inversion": 1,
                "extras": 0,
                "feminine": 0,
                "observed": "1001010101",
                "template": "1001010101",
            },
        ),
        (
            "01010101010",
            {
                "pattern": FootPattern.IAMBIC,
                "feet": 5,
                "cost": 0.2,
                "fit": 0.9818181818181818,
                "inversion": 0,
                "extras": 1,
                "feminine": 1,
                "observed": "01010101010",
                "template": "0101010101-",
            },
        ),
        (
            "100100100",
            {
                "pattern": FootPattern.DACTYLIC,
                "feet": 3,
                "cost": 0.0,
                "fit": 1.0,
                "inversion": 0,
                "extras": 0,
                "feminine": 0,
                "observed": "100100100",
                "template": "100100100",
            },
        ),
    ],
)
def test_stage6_candidate_layer_baseline_is_exact(
    stress: str,
    expected: dict[str, object],
) -> None:
    fit = MeterEstimator(MeterConfiguration()).evaluate_line(
        _line(stress, 1)
    ).closest_candidate

    assert fit is not None
    assert fit.pattern is expected["pattern"]
    assert fit.foot_count == expected["feet"]
    assert fit.total_cost == pytest.approx(expected["cost"])
    assert fit.fit_score == pytest.approx(expected["fit"])
    assert fit.initial_inversion_count == expected["inversion"]
    assert fit.extra_syllable_count == expected["extras"]
    assert fit.feminine_ending_count == expected["feminine"]
    assert fit.aligned_observed == expected["observed"]
    assert fit.aligned_template == expected["template"]


def test_stage6_poem_summary_baseline_is_exact() -> None:
    estimator = MeterEstimator(MeterConfiguration())
    lines = tuple(
        estimator.evaluate_line(_line(stress, line_number))
        for line_number, stress in enumerate(
            ("0101010101", "1001010101", "01010101010"),
            start=1,
        )
    )

    summary, candidates = summarize_meter_lines(lines, MeterConfiguration())

    assert summary.closest_candidate_label == "Iambic pentameter"
    assert summary.alternative_candidate_label == "Iambic hexameter"
    assert summary.assessment is MeterAssessment.RECURRING_CANDIDATE
    assert summary.candidate_confidence == "Moderate"
    assert summary.whole_poem_mean_fit == pytest.approx(0.9856060606060607)
    assert summary.candidate_margin == pytest.approx(0.057828282828283006)
    assert summary.rhythmic_variability == pytest.approx(
        0.010551809300897068
    )
    assert summary.initial_inversion_count == 1
    assert summary.extra_syllable_count == 1
    assert summary.feminine_ending_count == 1
    assert candidates[0].label == "Iambic pentameter"


def test_style_only_change_reuses_fixed_alignment_plans() -> None:
    clear_meter_alignment_cache()
    line = _line("0101010101", 1)
    traditional = MeterEstimator(
        MeterConfiguration(style_profile=MeterStyleProfile.TRADITIONAL)
    ).evaluate_line(line)
    after_first = meter_alignment_cache_info()
    modernist = MeterEstimator(
        MeterConfiguration(style_profile=MeterStyleProfile.MODERNIST)
    ).evaluate_line(line)
    after_second = meter_alignment_cache_info()

    assert traditional == modernist
    assert after_second["misses"] == after_first["misses"]
    assert after_second["hits"] > after_first["hits"]
    MeterStyleProfile,
    clear_meter_alignment_cache,
    meter_alignment_cache_info,
