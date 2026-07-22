"""Beginner-facing Phase 1 validation demonstration."""

from __future__ import annotations

import argparse
from pathlib import Path

from versevad.analysis import analyze_vad
from versevad.exports import export_analysis_csv
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document
from versevad.validation import (
    PHASE1_DEMO_TEXT,
    phase1_synthetic_lexicon,
    validate_phase1_demo,
)


def run_demo(output_directory: Path) -> int:
    document = create_text_document(
        "phase1-demo",
        "Invented Phase 1 validation poem",
        PHASE1_DEMO_TEXT,
    )
    result = analyze_vad(
        document,
        phase1_synthetic_lexicon(),
        SpacyEnglishPreprocessor(),
    )
    problems = validate_phase1_demo(result)
    if problems:
        print("VerseVAD's Phase 1 calculations did not match the expected results.")
        for problem in problems:
            print(f"- {problem}")
        print("No source text or lexicon file was changed.")
        return 1

    paths = export_analysis_csv(result, output_directory)
    coverage = result.coverage.lexical_token_coverage
    valence = result.vad_summary.token_weighted_original.valence.mean
    print("VerseVAD Phase 1 validation passed.")
    print(
        "Matched lexical tokens: "
        f"{result.coverage.matched_token_count}/{result.coverage.total_lexical_tokens} "
        f"({coverage:.1%} coverage)."
    )
    print(f"Mean normative valence of matched tokens: {valence:.6f} on the 1-9 scale.")
    print("Created auditable CSV files:")
    for path in paths:
        print(f"- {path.resolve()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the invented VerseVAD Phase 1 validation example."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("phase1_demo_output"),
        help="Directory for generated CSV files.",
    )
    args = parser.parse_args()
    return run_demo(args.output)


if __name__ == "__main__":
    raise SystemExit(main())
