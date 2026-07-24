"""Invented, hand-calculated validation for Stage 7 rhyme evidence."""

from __future__ import annotations

import hashlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

from versevad.core import ModuleInput, ResourceSpec
from versevad.phonology import PhonologicalModule
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document
from versevad.prosody.pronunciation import PronunciationModule


_DICTIONARY_ROWS = (
    "bright B R AY1 T",
    "cat K AE1 T",
    "hat HH AE1 T",
    "love L AH1 V",
    "motion M OW1 SH AH0 N",
    "move M UW1 V",
    "night N AY1 T",
    "ocean OW1 SH AH0 N",
    "seat S IY1 T",
    "silver S IH1 L V ER0",
    "sing S IH1 NG",
    "sit S IH1 T",
    "softly S AO1 F T L IY0",
    "stone S T OW1 N",
)
_VOWELS = ("AE", "AH", "AO", "AY", "ER", "IH", "IY", "OW", "UW")
_CONSONANTS = (
    "B",
    "F",
    "HH",
    "K",
    "L",
    "M",
    "N",
    "NG",
    "R",
    "S",
    "SH",
    "T",
    "V",
)
_PHONE_ROWS = (
    *(f"{phone}\tvowel" for phone in _VOWELS),
    *(f"{phone}\tconsonant" for phone in _CONSONANTS),
)
_SYMBOL_ROWS = (
    *_VOWELS,
    *(f"{phone}{stress}" for phone in _VOWELS for stress in "012"),
    *_CONSONANTS,
)


@dataclass(frozen=True)
class SyntheticPhonologyValidation:
    abab_scheme: str
    perfect_pair_count: int
    masculine_pair_count: int
    feminine_pair_count: int
    multisyllabic_pair_count: int
    slant_pair_count: int
    eye_pair_count: int
    slant_eye_scheme: str
    internal_pair_count: int
    alliteration_density: float | None
    assonance_density: float | None
    consonance_density: float | None
    unresolved_scheme: str
    unresolved_coverage: float | None
    source_files_unchanged: bool


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_rows(path: Path, rows: tuple[str, ...]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _spec(path: Path, resource_id: str) -> ResourceSpec:
    return ResourceSpec(
        resource_id=resource_id,
        display_name=f"Synthetic phonology {resource_id}",
        relative_path=path.name,
        version="synthetic-v1",
        accepted_sha256=(_sha256(path),),
        citation="Invented VerseVAD Stage 7 validation data.",
        license_notice="Synthetic data generated locally for validation.",
    )


def _analyze(
    module: PronunciationModule,
    preprocessor: SpacyEnglishPreprocessor,
    text_id: str,
    text: str,
):
    poem = preprocessor.process_document(
        create_text_document(text_id, "Invented Stage 7 validation", text)
    )
    module_input = ModuleInput.from_poem_document(poem)
    pronunciation = module.analyze_detailed(module_input)
    return PhonologicalModule().analyze_detailed(module_input, pronunciation)


def run_synthetic_phonology_validation(
) -> tuple[SyntheticPhonologyValidation, tuple[str, ...]]:
    """Run transparent invented examples with fixed expected results."""

    with tempfile.TemporaryDirectory(prefix="versevad-phonology-") as directory:
        root = Path(directory)
        dictionary = root / "cmudict.dict"
        phones = root / "cmudict.phones"
        symbols = root / "cmudict.symbols"
        _write_rows(dictionary, _DICTIONARY_ROWS)
        _write_rows(phones, _PHONE_ROWS)
        _write_rows(symbols, _SYMBOL_ROWS)
        paths = (dictionary, phones, symbols)
        before = tuple(_sha256(path) for path in paths)
        module = PronunciationModule(
            root,
            dictionary_spec=_spec(dictionary, "dictionary"),
            phones_spec=_spec(phones, "phones"),
            symbols_spec=_spec(symbols, "symbols"),
            expected_dictionary_rows=len(_DICTIONARY_ROWS),
            expected_phone_rows=len(_PHONE_ROWS),
            expected_symbol_rows=len(_SYMBOL_ROWS),
        )
        preprocessor = SpacyEnglishPreprocessor()
        abab = _analyze(
            module,
            preprocessor,
            "phonology-abab",
            "bright cat\nsilver night\nsoftly hat\nstone bright",
        )
        feminine = _analyze(
            module,
            preprocessor,
            "phonology-feminine",
            "softly motion\nsilver ocean",
        )
        slant_eye = _analyze(
            module,
            preprocessor,
            "phonology-slant-eye",
            "sit\nseat\nlove\nmove",
        )
        internal = _analyze(
            module,
            preprocessor,
            "phonology-internal",
            "cat hat stone\nsilver softly sing",
        )
        unresolved = _analyze(
            module,
            preprocessor,
            "phonology-unresolved",
            "stone quorvax",
        )
        after = tuple(_sha256(path) for path in paths)

    perfect_pairs = [
        pair for pair in abab.pair_results if pair.relationship == "perfect"
    ]
    feminine_pairs = [
        pair for pair in feminine.pair_results if pair.relationship == "perfect"
    ]
    report = SyntheticPhonologyValidation(
        abab_scheme=abab.summary.whole_poem_rhyme_scheme,
        perfect_pair_count=abab.summary.perfect_rhyme_pair_count,
        masculine_pair_count=sum(
            "masculine" in pair.rhyme_types for pair in perfect_pairs
        ),
        feminine_pair_count=sum(
            "feminine" in pair.rhyme_types for pair in feminine_pairs
        ),
        multisyllabic_pair_count=sum(
            "multisyllabic" in pair.rhyme_types for pair in feminine_pairs
        ),
        slant_pair_count=slant_eye.summary.slant_rhyme_pair_count,
        eye_pair_count=slant_eye.summary.eye_rhyme_pair_count,
        slant_eye_scheme=slant_eye.summary.whole_poem_rhyme_scheme,
        internal_pair_count=internal.summary.internal_rhyme_pair_count,
        alliteration_density=internal.summary.alliteration_density,
        assonance_density=internal.summary.assonance_density,
        consonance_density=internal.summary.consonance_density,
        unresolved_scheme=unresolved.summary.whole_poem_rhyme_scheme,
        unresolved_coverage=unresolved.summary.ending_coverage,
        source_files_unchanged=before == after,
    )
    expected = {
        "abab_scheme": "ABAB",
        "perfect_pair_count": 2,
        "masculine_pair_count": 2,
        "feminine_pair_count": 1,
        "multisyllabic_pair_count": 1,
        "slant_eye_scheme": "xxxx",
        "internal_pair_count": 1,
        "unresolved_scheme": "?",
        "unresolved_coverage": 0.0,
        "source_files_unchanged": True,
    }
    problems = [
        f"{field} was {getattr(report, field)!r}; expected {value!r}."
        for field, value in expected.items()
        if getattr(report, field) != value
    ]
    if report.slant_pair_count < 1:
        problems.append("The invented sit/seat pair lacked graded slant evidence.")
    if report.eye_pair_count < 1:
        problems.append("The invented love/move pair lacked eye-rhyme evidence.")
    for field in (
        "alliteration_density",
        "assonance_density",
        "consonance_density",
    ):
        value = getattr(report, field)
        if value is None or value <= 0:
            problems.append(f"{field} did not retain repeated-sound evidence.")
    return report, tuple(problems)


def main() -> int:
    report, problems = run_synthetic_phonology_validation()
    if problems:
        print("VerseVAD's Stage 7 validation did not match expectations.")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("VerseVAD Stage 7 rhyme and phonological validation passed.")
    print(
        f"The exact end-rhyme example produced {report.abab_scheme} with "
        f"{report.perfect_pair_count} perfect pairs."
    )
    print(
        "Masculine, feminine, multisyllabic, graded slant, eye, internal-rhyme, "
        "alliteration, assonance, and consonance evidence matched expectations."
    )
    print("An unresolved ending remained ? with 0% ending coverage.")
    print("The generated synthetic pronunciation files remained unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
