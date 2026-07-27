"""Invented, hand-calculated validation for Stage 5 pronunciation evidence."""

from __future__ import annotations

import hashlib
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path

from versevad.core import ModuleInput, ResourceSpec
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document
from versevad.prosody.pronunciation import (
    PronunciationConfiguration,
    PronunciationModule,
    PronunciationOverride,
    PronunciationStatus,
)


_DICTIONARY_ROWS = (
    "permit P ER0 M IH1 T",
    "permit(2) P ER1 M IH2 T",
    "rings R IH1 NG Z",
    "stone S T OW1 N",
    "wind W IH1 N D",
    "wind(2) W AY1 N D",
)
_PHONE_ROWS = (
    "AY\tvowel",
    "ER\tvowel",
    "IH\tvowel",
    "OW\tvowel",
    "D\tstop",
    "M\tnasal",
    "N\tnasal",
    "NG\tnasal",
    "P\tstop",
    "R\tliquid",
    "S\tfricative",
    "T\tstop",
    "W\tsemivowel",
    "Z\tfricative",
)
_VOWELS = ("AY", "ER", "IH", "OW")
_SYMBOL_ROWS = (
    *_VOWELS,
    *(f"{phone}{stress}" for phone in _VOWELS for stress in "012"),
    "D",
    "M",
    "N",
    "NG",
    "P",
    "R",
    "S",
    "T",
    "W",
    "Z",
)


@dataclass(frozen=True)
class SyntheticPronunciationValidation:
    eligible_tokens: int
    resolved_tokens_before_override: int
    resolved_tokens_after_override: int
    ambiguous_tokens_before_override: int
    token_coverage_before_override: float | None
    token_coverage_after_override: float | None
    complete_lines_before_override: int
    complete_lines_after_override: int
    first_line_syllables: int | None
    second_line_syllables_after_override: int | None
    first_line_stress: str | None
    second_line_stress_after_override: str | None
    unique_status: str
    consensus_status: str
    ambiguous_status: str
    override_status: str
    source_files_unchanged: bool


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_rows(path: Path, rows: tuple[str, ...]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _spec(path: Path, resource_id: str) -> ResourceSpec:
    return ResourceSpec(
        resource_id=resource_id,
        display_name=f"Synthetic pronunciation {resource_id}",
        relative_path=path.name,
        version="synthetic-v1",
        accepted_sha256=(_sha256(path),),
        citation="Invented VerseVAD validation data.",
        license_notice="Synthetic data generated locally for validation.",
    )


def run_synthetic_pronunciation_validation(
) -> tuple[SyntheticPronunciationValidation, tuple[str, ...]]:
    """Run invented examples with auditable, hand-calculated expectations."""

    with tempfile.TemporaryDirectory(
        prefix="versevad-pronunciation-"
    ) as directory:
        root = Path(directory)
        dictionary = root / "cmudict.dict"
        phones = root / "cmudict.phones"
        symbols = root / "cmudict.symbols"
        _write_rows(dictionary, _DICTIONARY_ROWS)
        _write_rows(phones, _PHONE_ROWS)
        _write_rows(symbols, _SYMBOL_ROWS)
        before = tuple(_sha256(path) for path in (dictionary, phones, symbols))
        module = PronunciationModule(
            root,
            dictionary_spec=_spec(dictionary, "dictionary"),
            phones_spec=_spec(phones, "phones"),
            symbols_spec=_spec(symbols, "symbols"),
            expected_dictionary_rows=len(_DICTIONARY_ROWS),
            expected_phone_rows=len(_PHONE_ROWS),
            expected_symbol_rows=len(_SYMBOL_ROWS),
        )
        poem = SpacyEnglishPreprocessor().process_document(
            create_text_document(
                "pronunciation-validation",
                "Invented pronunciation validation",
                "stone wind\npermit rings",
            )
        )
        module_input = ModuleInput.from_poem_document(poem)
        unresolved = module.analyze_detailed(module_input)
        resolved = module.analyze_detailed(
            module_input,
            PronunciationConfiguration(
                overrides=(
                    PronunciationOverride(
                        term="permit",
                        phones=("P", "ER0", "M", "IH1", "T"),
                        note="Verb reading in the invented validation line.",
                    ),
                )
            ),
        )
        after = tuple(_sha256(path) for path in (dictionary, phones, symbols))

    unresolved_by_surface = {
        item.surface_form: item for item in unresolved.token_audit
    }
    resolved_by_surface = {
        item.surface_form: item for item in resolved.token_audit
    }
    report = SyntheticPronunciationValidation(
        eligible_tokens=unresolved.summary.eligible_token_count,
        resolved_tokens_before_override=unresolved.summary.resolved_token_count,
        resolved_tokens_after_override=resolved.summary.resolved_token_count,
        ambiguous_tokens_before_override=unresolved.summary.ambiguous_token_count,
        token_coverage_before_override=unresolved.summary.token_coverage,
        token_coverage_after_override=resolved.summary.token_coverage,
        complete_lines_before_override=unresolved.summary.complete_line_count,
        complete_lines_after_override=resolved.summary.complete_line_count,
        first_line_syllables=unresolved.line_summaries[0].syllable_count,
        second_line_syllables_after_override=(
            resolved.line_summaries[1].syllable_count
        ),
        first_line_stress=(
            unresolved.line_summaries[0].lexical_stress_sequence
        ),
        second_line_stress_after_override=(
            resolved.line_summaries[1].lexical_stress_sequence
        ),
        unique_status=unresolved_by_surface["stone"].status.value,
        consensus_status=unresolved_by_surface["wind"].status.value,
        ambiguous_status=unresolved_by_surface["permit"].status.value,
        override_status=resolved_by_surface["permit"].status.value,
        source_files_unchanged=before == after,
    )

    problems = []
    expected = {
        "eligible_tokens": 4,
        "resolved_tokens_before_override": 3,
        "resolved_tokens_after_override": 4,
        "ambiguous_tokens_before_override": 1,
        "complete_lines_before_override": 1,
        "complete_lines_after_override": 2,
        "first_line_syllables": 2,
        "second_line_syllables_after_override": 3,
        "first_line_stress": "1 | 1",
        "second_line_stress_after_override": "01 | 1",
        "unique_status": PronunciationStatus.DICTIONARY_UNIQUE.value,
        "consensus_status": (
            PronunciationStatus.DICTIONARY_PROSODIC_CONSENSUS.value
        ),
        "ambiguous_status": PronunciationStatus.AMBIGUOUS_DICTIONARY.value,
        "override_status": (
            PronunciationStatus.DICTIONARY_USER_SELECTION.value
        ),
    }
    for field, value in expected.items():
        if getattr(report, field) != value:
            problems.append(
                f"{field} was {getattr(report, field)!r}; expected {value!r}."
            )
    if (
        report.token_coverage_before_override is None
        or not math.isclose(report.token_coverage_before_override, 3 / 4)
    ):
        problems.append(
            "Coverage before the override did not equal the hand-calculated 3/4."
        )
    if (
        report.token_coverage_after_override is None
        or not math.isclose(report.token_coverage_after_override, 1.0)
    ):
        problems.append(
            "Coverage after the override did not equal the hand-calculated 4/4."
        )
    if not report.source_files_unchanged:
        problems.append(
            "A synthetic CMUdict source file changed during validation."
        )
    if any(
        item.resolved_syllable_count is not None
        for item in unresolved.token_audit
        if not item.resolved
    ):
        problems.append("An unresolved token received a syllable count.")
    if unresolved.line_summaries[1].syllable_count is not None:
        problems.append("An incomplete line received a syllable total.")
    return report, tuple(problems)


def main() -> int:
    report, problems = run_synthetic_pronunciation_validation()
    if problems:
        print("VerseVAD's pronunciation validation did not match expectations.")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("VerseVAD Stage 5 pronunciation validation passed.")
    print(
        "Resolved lexical tokens before/after the explicit override: "
        f"{report.resolved_tokens_before_override}/"
        f"{report.resolved_tokens_after_override} of "
        f"{report.eligible_tokens}."
    )
    print(
        "The complete first line has 2 syllables and lexical stress `1 | 1`; "
        "the override makes the second line complete with 3 syllables and "
        "lexical stress `01 | 1`."
    )
    print(
        "Unique, prosodically agreeing, materially ambiguous, and explicit "
        "dictionary-user-selection cases followed the expected audit."
    )
    print("The generated synthetic dictionary files remained unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
