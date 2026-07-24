"""Hand-calculated validation for lexical diversity and structural word counts."""

from __future__ import annotations

import math

from versevad.core import ModuleInput
from versevad.lexical_style import LexicalStyleConfiguration, LexicalStyleModule
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document


SYNTHETIC_TEXT = "red blue red\ngreen blue\n\nyellow red"


def main() -> int:
    poem = SpacyEnglishPreprocessor().process_document(
        create_text_document(
            "lexical-style-validation",
            "Lexical style validation",
            SYNTHETIC_TEXT,
        )
    )
    result = LexicalStyleModule().analyze_detailed(
        ModuleInput.from_poem_document(poem),
        LexicalStyleConfiguration(
            mattr_window_size=3,
            hdd_sample_size=3,
            short_text_warning_threshold=10,
        ),
    )

    expected_mattr = 14 / 15
    expected_hdd = 86 / 105
    assert result.summary.lexical_token_count == 7
    assert result.summary.normalized_surface_type_count == 4
    assert math.isclose(
        result.summary.surface_type_token_ratio or 0,
        4 / 7,
    )
    assert math.isclose(result.summary.mattr or 0, expected_mattr)
    assert math.isclose(result.summary.hdd or 0, expected_hdd)
    assert result.summary.mean_alphabetic_characters_per_token == 4
    assert [item.word_count for item in result.line_summaries] == [3, 2, 0, 2]
    assert [item.word_count for item in result.stanza_summaries] == [5, 2]

    print("VerseVAD lexical style validation passed.")
    print("Tokens: 7; normalized observed surface types: 4.")
    print(f"MATTR (window 3): {result.summary.mattr:.6f} = 14/15.")
    print(f"HD-D (sample 3): {result.summary.hdd:.6f} = 86/105.")
    print("Mean alphabetic characters per lexical token: 4.")
    print("Line word counts: 3, 2, 0, 2.")
    print("Stanza word counts: 5, 2.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
