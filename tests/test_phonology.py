from __future__ import annotations

import pytest

from versevad.core import ModuleInput
from versevad.phonology import (
    PhonologicalConfiguration,
    PhonologicalModule,
    RhymeEndingStatus,
)
from versevad.preprocessing import create_text_document
from versevad.prosody.pronunciation import PronunciationConfiguration
from tests.test_pronunciation import _module


def _analyze(tmp_path, preprocessor, text: str, configuration=None):
    poem = preprocessor.process_document(
        create_text_document("phonology-test", "Phonology test", text)
    )
    pronunciation = _module(tmp_path).analyze_detailed(
        ModuleInput.from_poem_document(poem),
        PronunciationConfiguration(),
    )
    return PhonologicalModule().analyze_detailed(
        ModuleInput.from_poem_document(poem),
        pronunciation,
        configuration or PhonologicalConfiguration(),
    )


def test_abab_perfect_rhyme_scheme_and_masculine_pairs(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "bright cat\nsilver night\nsoftly hat\nstone bright",
    )

    assert result.summary.whole_poem_rhyme_scheme == "ABAB"
    assert result.summary.stanza_scheme_sequence == "ABAB"
    assert result.summary.perfect_rhyme_pair_count == 2
    assert result.summary.identical_rhyme_pair_count == 0
    assert result.summary.rhymed_line_count == 4
    assert result.summary.rhyme_density == 1.0
    assert {
        pair.relationship for pair in result.pair_results
    } >= {"perfect", "none"}
    assert all(
        "masculine" in pair.rhyme_types
        for pair in result.pair_results
        if pair.relationship == "perfect"
    )


def test_identical_feminine_multisyllabic_and_refrain_are_separate(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "softly motion\nsilver ocean\nsoftly motion\nsilver ocean",
    )

    identical = [
        item for item in result.pair_results if item.relationship == "identical"
    ]
    perfect = [
        item for item in result.pair_results if item.relationship == "perfect"
    ]
    assert identical
    assert perfect
    assert any("feminine" in item.rhyme_types for item in perfect)
    assert any("multisyllabic" in item.rhyme_types for item in perfect)
    assert result.summary.refrain_line_count == 4
    assert {item.refrain_group_id for item in result.line_results} == {
        "refrain-1",
        "refrain-2",
    }


def test_slant_and_eye_rhyme_remain_outside_exact_scheme_groups(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "sit\nseat\nlove\nmove",
    )

    slant = next(
        item
        for item in result.pair_results
        if {item.first_word, item.second_word} == {"sit", "seat"}
    )
    eye = next(
        item
        for item in result.pair_results
        if {item.first_word, item.second_word} == {"love", "move"}
    )
    assert slant.relationship == "slant"
    assert slant.similarity_score is not None
    assert slant.similarity_score >= result.configuration.slant_rhyme_threshold
    assert eye.is_eye_rhyme
    assert eye.relationship == "none"
    assert result.summary.whole_poem_rhyme_scheme == "xxxx"
    assert result.summary.slant_rhyme_pair_count >= 1
    assert result.summary.eye_rhyme_pair_count >= 1


def test_internal_rhyme_alliteration_assonance_and_consonance(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "cat hat stone\nsilver softly sing",
    )
    first, second = result.line_results

    assert len(first.internal_rhyme_matches) == 1
    assert first.internal_rhyme_matches[0].rhyme_part == "AE T"
    assert second.repeated_initial_consonants == ("S",)
    assert second.alliteration_density == 1.0
    assert first.assonance_density is not None
    assert first.consonance_density is not None
    assert result.summary.internal_rhyme_pair_count == 1
    assert "S" in result.summary.dominant_initial_consonants


def test_missing_and_materially_ambiguous_endings_remain_unassigned(
    tmp_path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "stone quorvax\nstone permit\nstone hm",
    )
    statuses = [item.status for item in result.line_results]

    assert statuses == [
        RhymeEndingStatus.UNMATCHED_PRONUNCIATION,
        RhymeEndingStatus.AMBIGUOUS_PRONUNCIATION,
        RhymeEndingStatus.SOURCE_WITHOUT_MARKED_VOWEL,
    ]
    assert result.summary.analyzable_ending_count == 0
    assert result.summary.ending_coverage == 0.0
    assert result.summary.whole_poem_rhyme_scheme == "???"
    assert result.summary.rhyme_density is None


def test_empty_nonlexical_and_deterministic_results(
    tmp_path,
    preprocessor,
) -> None:
    first = _analyze(tmp_path, preprocessor, "...\ncat\nhat")
    second = _analyze(tmp_path, preprocessor, "...\ncat\nhat")

    assert first == second
    assert first.line_results[0].status is RhymeEndingStatus.NO_LEXICAL_TOKENS
    assert first.summary.whole_poem_rhyme_scheme == "AA"
    assert first.summary.ending_coverage == pytest.approx(1.0)


def test_configuration_requires_normalized_weights() -> None:
    with pytest.raises(ValueError, match="sum to 1"):
        PhonologicalConfiguration(stressed_vowel_weight=0.30)
