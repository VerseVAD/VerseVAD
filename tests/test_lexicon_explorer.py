import pytest

from versevad.explorer import explore_loaded_lexicons
from versevad.phase2_validation import phase2_synthetic_vad_lexicon


def test_explorer_distinguishes_exact_phrase_and_lemma(preprocessor) -> None:
    lexicon = phase2_synthetic_vad_lexicon()
    phrase = explore_loaded_lexicons("dark night", (lexicon,), preprocessor)
    assert len(phrase.entries) == 1
    assert phrase.entries[0].matched_term == "dark night"
    assert phrase.entries[0].match_method == "exact phrase"
    assert not phrase.component_averages

    lemma = explore_loaded_lexicons("glowing", (lexicon,), preprocessor)
    assert lemma.processing_lemma == "glow"
    assert lemma.entries[0].matched_term == "glow"
    assert lemma.entries[0].match_method == "lemma-derived entry"


def test_explorer_accepts_entry_from_session_without_optional_uncertainty_fields(
    preprocessor,
) -> None:
    lexicon = phase2_synthetic_vad_lexicon()
    entry = lexicon.entries["bright"]
    object.__delattr__(entry, "standard_deviation")
    object.__delattr__(entry, "rater_count")

    result = explore_loaded_lexicons("bright", (lexicon,), preprocessor)

    assert result.entries[0].matched_term == "bright"
    assert result.entries[0].standard_deviation is None
    assert result.entries[0].rater_count is None


def test_explorer_labels_component_average_as_derived(preprocessor) -> None:
    result = explore_loaded_lexicons(
        "bright glow",
        (phase2_synthetic_vad_lexicon(),),
        preprocessor,
    )
    assert not result.entries
    assert len(result.component_averages) == 1
    average = result.component_averages[0]
    assert average.components == ("bright", "glow")
    assert average.normalized_scores.valence == pytest.approx((0.875 + 0.75) / 2)


def test_explorer_does_not_turn_close_word_suggestion_into_match(preprocessor) -> None:
    result = explore_loaded_lexicons(
        "brigt",
        (phase2_synthetic_vad_lexicon(),),
        preprocessor,
    )
    assert not result.entries
    assert "bright" in result.suggestions


def test_user_mapping_is_explicit_and_does_not_replace_original_query(preprocessor) -> None:
    result = explore_loaded_lexicons(
        "glowy",
        (phase2_synthetic_vad_lexicon(),),
        preprocessor,
        mapped_query="glow",
    )
    assert result.query == "glowy"
    assert result.entries[0].matched_term == "glow"
    assert result.entries[0].match_method == "user-supplied mapped lookup"
    assert any("does not alter" in notice for notice in result.notices)
