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
)


@dataclass(frozen=True)
class SyntheticMeterValidation:
    fixed_candidate_count: int
    iambic_pentameter_label: str
    iambic_pentameter_fit: float
    feminine_ending_count: int
    initial_inversion_count: int
    catalectic_count: int
    trochaic_tetrameter_label: str
    trochaic_tetrameter_fit: float
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
    trochaic = estimator.evaluate_line(
        _line("10" * 4, line_number=5)
    )
    missing = estimator.evaluate_line(
        MeterLineInput(
            line_id="missing-line",
            line_number=6,
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
    assert trochaic.closest_candidate is not None
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
        trochaic_tetrameter_label=trochaic.closest_candidate.label,
        trochaic_tetrameter_fit=trochaic.closest_candidate.fit_score,
        missing_line_status=missing.status.value,
        missing_line_has_fit=missing.closest_candidate is not None,
    )
    expected = {
        "fixed_candidate_count": 40,
        "iambic_pentameter_label": "Iambic pentameter",
        "feminine_ending_count": 1,
        "initial_inversion_count": 1,
        "catalectic_count": 1,
        "trochaic_tetrameter_label": "Trochaic tetrameter",
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
    if not math.isclose(report.trochaic_tetrameter_fit, 1.0):
        problems.append("Exact trochaic tetrameter did not receive fit 1.0.")
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
        "Exact trochaic tetrameter received fit 1.0 as a separate fixed "
        "pattern-and-foot-count candidate."
    )
    print("A line missing pronunciation evidence remained unscored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
