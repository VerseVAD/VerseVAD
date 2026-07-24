"""Invented, hand-calculated validation for Stage 6 meter estimation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from versevad.prosody.meter import (
    MeterConfiguration,
    MeterEstimator,
    MeterLineInput,
    MeterLineStatus,
    StressSyllable,
    StressVariant,
    candidate_templates,
    summarize_meter_lines,
)


@dataclass(frozen=True)
class SyntheticMeterValidation:
    fixed_candidate_count: int
    iambic_pentameter_label: str
    iambic_pentameter_fit: float
    feminine_ending_count: int
    initial_inversion_count: int
    catalectic_count: int
    common_meter_label: str
    common_meter_cycle: tuple[int, ...]
    common_meter_fit: float
    common_meter_matching_lines: int
    common_meter_complete_stanzas: int
    missing_line_status: str
    missing_line_has_fit: bool


def _line(
    stress: str,
    *,
    line_number: int,
    stanza_number: int = 1,
) -> MeterLineInput:
    syllables = tuple(
        StressSyllable(
            stress_digit=digit,
            token_id=f"line-{line_number}-token-{index + 1}",
            surface_form=f"w{index + 1}",
            part_of_speech="NOUN",
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
                variant_id=f"line-{line_number}-stress-1",
                syllables=syllables,
                word_stress_sequence=" | ".join(stress),
                pronunciation_choices=tuple(
                    f"w{index + 1}={digit}"
                    for index, digit in enumerate(stress)
                ),
            ),
        ),
    )


def run_synthetic_meter_validation(
) -> tuple[SyntheticMeterValidation, tuple[str, ...]]:
    """Run transparent stress strings with hand-calculated expected fits."""

    configuration = MeterConfiguration()
    estimator = MeterEstimator(configuration)
    pentameter = estimator.evaluate_line(
        _line("01" * 5, line_number=1)
    )
    feminine = estimator.evaluate_line(
        _line(("01" * 5) + "0", line_number=2)
    )
    inversion = estimator.evaluate_line(
        _line("10" + ("01" * 4), line_number=3)
    )
    catalectic = estimator.evaluate_line(
        _line(("10" * 4)[:-1], line_number=4)
    )
    common_lines = tuple(
        estimator.evaluate_line(line)
        for line in (
            _line("01" * 4, line_number=1),
            _line("01" * 3, line_number=2),
            _line("01" * 4, line_number=3),
            _line("01" * 3, line_number=4),
        )
    )
    common_summary, _, schemes = summarize_meter_lines(
        common_lines,
        configuration,
    )
    common = schemes[0]
    missing = estimator.evaluate_line(
        MeterLineInput(
            line_id="missing-line",
            line_number=5,
            stanza_number=1,
            source_text="quorvax",
            eligible_token_count=1,
            supported_token_count=0,
            missing_forms=("quorvax",),
            stress_variants=(),
        )
    )
    assert pentameter.closest_candidate is not None
    assert feminine.closest_candidate is not None
    assert inversion.closest_candidate is not None
    assert catalectic.closest_candidate is not None
    report = SyntheticMeterValidation(
        fixed_candidate_count=len(candidate_templates(configuration)),
        iambic_pentameter_label=pentameter.closest_candidate.label,
        iambic_pentameter_fit=pentameter.closest_candidate.fit_score,
        feminine_ending_count=(
            feminine.closest_candidate.feminine_ending_count
        ),
        initial_inversion_count=(
            inversion.closest_candidate.initial_inversion_count
        ),
        catalectic_count=catalectic.closest_candidate.catalectic_count,
        common_meter_label=common_summary.closest_candidate_label,
        common_meter_cycle=common.foot_count_cycle,
        common_meter_fit=common.mean_fit or 0,
        common_meter_matching_lines=common.matching_line_count,
        common_meter_complete_stanzas=common.complete_stanza_count,
        missing_line_status=missing.status.value,
        missing_line_has_fit=missing.closest_candidate is not None,
    )
    expected = {
        "fixed_candidate_count": 40,
        "iambic_pentameter_label": "Iambic pentameter",
        "feminine_ending_count": 1,
        "initial_inversion_count": 1,
        "catalectic_count": 1,
        "common_meter_label": (
            "Common meter (alternating iambic tetrameter/trimeter)"
        ),
        "common_meter_cycle": (4, 3, 4, 3),
        "common_meter_matching_lines": 4,
        "common_meter_complete_stanzas": 1,
        "missing_line_status": MeterLineStatus.MISSING_PRONUNCIATION.value,
        "missing_line_has_fit": False,
    }
    problems = []
    for field, value in expected.items():
        if getattr(report, field) != value:
            problems.append(
                f"{field} was {getattr(report, field)!r}; expected {value!r}."
            )
    if not math.isclose(report.iambic_pentameter_fit, 1.0):
        problems.append("Exact iambic pentameter did not receive fit 1.0.")
    if not math.isclose(report.common_meter_fit, 1.0):
        problems.append("Exact common meter did not receive scheme fit 1.0.")
    return report, tuple(problems)


def main() -> int:
    report, problems = run_synthetic_meter_validation()
    if problems:
        print("VerseVAD's meter validation did not match expectations.")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("VerseVAD Stage 6 meter validation passed.")
    print(
        f"All {report.fixed_candidate_count} fixed line templates were present; "
        "exact iambic pentameter received fit 1.0."
    )
    print(
        "Feminine ending, initial inversion, and catalectic ending each produced "
        "the expected explicit deviation count."
    )
    print(
        "One exact common-meter quatrain followed iambic 4-3-4-3, matched all "
        "four lines, and received scheme fit 1.0."
    )
    print("A line missing pronunciation evidence remained unscored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
