"""Beginner-facing Phase 2 validation and five-lexicon demonstration."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from versevad.adapters import (
    NrcEmotionAdapter,
    NrcEmotionIntensityAdapter,
    NrcVadV1Adapter,
    NrcVadV21Adapter,
    WarrinerVadAdapter,
)
from versevad.analysis.phase2 import analyze_lexicon, compare_lexicons
from versevad.exports.phase2_csv import export_phase2_csv
from versevad.models import PhrasePolicy
from versevad.phase2_validation import (
    PHASE2_PHRASE_TEXT,
    phase2_synthetic_emotion_lexicon,
    phase2_synthetic_intensity_lexicon,
    phase2_synthetic_vad_lexicon,
)
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source_lexicons"
DEMO_TEXT = """A bit of bright joy and fear in the dark night.
Outraged hearts glowed.
"""

SOURCE_SPECS = (
    (
        WarrinerVadAdapter(),
        SOURCE_ROOT / "XANEW-master" / "XANEW-master" / "Ratings_Warriner_et_al.csv",
        "78ac8107c78e116bb96538fae4faa47281a155f5f8fe39f30bbc6ea3db05b446",
    ),
    (
        NrcVadV1Adapter(),
        SOURCE_ROOT / "NRC-VAD-Lexicon" / "NRC-VAD-Lexicon" / "NRC-VAD-Lexicon.txt",
        "fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7",
    ),
    (
        NrcVadV21Adapter(),
        SOURCE_ROOT
        / "NRC-VAD-Lexicon-v2.1"
        / "NRC-VAD-Lexicon-v2.1"
        / "NRC-VAD-Lexicon-v2.1.txt",
        "42c718817fc91d5c133581b24b0bb31d2b14a0b16edb19bc6ce6ab70343e5a45",
    ),
    (
        NrcEmotionAdapter(),
        SOURCE_ROOT
        / "NRC-Emotion-Lexicon"
        / "NRC-Emotion-Lexicon"
        / "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
        "02c661544f4f12ae0c14f9576a10959e8d39a151bb091e455a71a08dcaa2535a",
    ),
    (
        NrcEmotionIntensityAdapter(),
        SOURCE_ROOT
        / "NRC-Emotion-Intensity-Lexicon"
        / "NRC-Emotion-Intensity-Lexicon"
        / "NRC-Emotion-Intensity-Lexicon-v1.txt",
        "2bed5450b43134e4f849b013424eb76a76e2bdc0ec35df7ec0a0a477031239cb",
    ),
)


def _validate_synthetic_examples(preprocessor: SpacyEnglishPreprocessor) -> None:
    phrase_document = create_text_document(
        "phase2-synthetic-phrase", "Synthetic phrase validation", PHASE2_PHRASE_TEXT
    )
    phrase = analyze_lexicon(
        phrase_document,
        phase2_synthetic_vad_lexicon(),
        preprocessor,
        phrase_policy=PhrasePolicy.PHRASE_PREFERRED,
    )
    if phrase.coverage.matched_token_count != 7 or phrase.coverage.phrase_match_count != 1:
        raise RuntimeError("The hand-calculated phrase coverage check did not reproduce.")
    assert phrase.vad_summary is not None
    mean = phrase.vad_summary.token_weighted_original.valence.mean
    if mean is None or not math.isclose(mean, 27 / 5):
        raise RuntimeError("The hand-calculated phrase VAD mean did not reproduce.")

    emotion = analyze_lexicon(
        create_text_document(
            "phase2-synthetic-emotion", "Synthetic emotion validation", "Joy joy fear stone."
        ),
        phase2_synthetic_emotion_lexicon(),
        preprocessor,
    )
    joy = next(item for item in emotion.category_statistics if item.category == "joy")
    if joy.associated_token_count != 2 or joy.proportion_of_lexical_tokens != 0.5:
        raise RuntimeError("The hand-calculated categorical-emotion check did not reproduce.")

    intensity = analyze_lexicon(
        create_text_document(
            "phase2-synthetic-intensity",
            "Synthetic intensity validation",
            "Rage rage fear stone.",
        ),
        phase2_synthetic_intensity_lexicon(),
        preprocessor,
    )
    anger = next(item for item in intensity.intensity_statistics if item.category == "anger")
    if anger.token_weighted.mean is None or not math.isclose(
        anger.token_weighted.mean, 0.6
    ):
        raise RuntimeError("The hand-calculated intensity mean did not reproduce.")


def run_demo(output_directory: Path) -> tuple[Path, ...]:
    preprocessor = SpacyEnglishPreprocessor()
    _validate_synthetic_examples(preprocessor)
    lexicons = []
    for adapter, path, expected_hash in SOURCE_SPECS:
        lexicon = adapter.load(path)
        if lexicon.validation.source_sha256 != expected_hash:
            raise RuntimeError(
                f"The source checksum for {lexicon.metadata.display_name} differs "
                "from the inspected Phase 0 source. No analysis was exported."
            )
        lexicons.append(lexicon)

    document = create_text_document("phase2-real-demo", "Phase 2 five-lexicon demo", DEMO_TEXT)
    results = tuple(
        analyze_lexicon(
            document,
            lexicon,
            preprocessor,
            phrase_policy=PhrasePolicy.PHRASE_PREFERRED,
        )
        for lexicon in lexicons
    )
    comparison = compare_lexicons(results)
    paths = export_phase2_csv(results, comparison, output_directory)

    print("VerseVAD Phase 2 validation passed.")
    print("All five private source files matched their inspected SHA-256 checksums.")
    print("Independent results (no consensus score):")
    for result in results:
        coverage = result.coverage.lexical_token_coverage
        percentage = f"{coverage:.1%}" if coverage is not None else "not available"
        print(
            f"- {result.lexicon_metadata.display_name}: "
            f"{result.coverage.matched_token_count}/"
            f"{result.coverage.total_lexical_tokens} lexical tokens ({percentage})"
        )
    print("Created auditable Phase 2 CSV and JSON files:")
    for path in paths:
        print(f"- {path.resolve()}")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "phase2_demo_output",
        help="Directory for generated Phase 2 audit CSV files.",
    )
    arguments = parser.parse_args()
    run_demo(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
