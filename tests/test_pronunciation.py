from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from versevad.adapters.cmudict import CMUDictAdapter, CMUDictAdapterError
from versevad.core import ModuleInput, ResourceSpec
from versevad.preprocessing import create_text_document
from versevad.prosody.pronunciation import (
    PronunciationConfiguration,
    PronunciationModule,
    PronunciationModuleError,
    PronunciationOverride,
    PronunciationStatus,
    parse_pronunciation_overrides,
    upsert_pronunciation_override_text,
)


DICTIONARY_ROWS = (
    "alice AE1 L IH0 S",
    "bright B R AY1 T",
    "cat K AE1 T",
    "hm HH M",
    "hat HH AE1 T",
    "i'd AY1 D",
    "i'm AY1 M",
    "isn't IH1 Z AH0 N T",
    "didn't D IH1 D AH0 N T",
    "love L AH1 V",
    "motion M OW1 SH AH0 N",
    "move M UW1 V",
    "night N AY1 T",
    "o'er AO1 R",
    "ocean OW1 SH AH0 N",
    "permit P ER0 M IH1 T",
    "permit(2) P ER1 M IH2 T",
    "rings R IH1 NG Z",
    "seat S IY1 T",
    "she'll SH IY1 L",
    "silver S IH1 L V ER0",
    "sing S IH1 NG",
    "sit S IH1 T",
    "softly S AO1 F T L IY0",
    "stone S T OW1 N",
    "the DH AH0",
    "the(2) DH AH1",
    "true T R UW1",
    "we'll W IY1 L",
    "you Y UW1",
    "you're Y UW1 R",
    "can't K AE1 N T",
    "won't W OW1 N T",
    "'tis T IH1 Z",
    "wind W IH1 N D",
    "wind(2) W AY1 N D",
)
PHONE_ROWS = (
    "AE\tvowel",
    "AH\tvowel",
    "AO\tvowel",
    "AY\tvowel",
    "ER\tvowel",
    "IH\tvowel",
    "IY\tvowel",
    "OW\tvowel",
    "UW\tvowel",
    "B\tstop",
    "D\tstop",
    "DH\tfricative",
    "F\tfricative",
    "HH\taspirate",
    "K\tstop",
    "L\tliquid",
    "M\tnasal",
    "N\tnasal",
    "NG\tnasal",
    "P\tstop",
    "R\tliquid",
    "S\tfricative",
    "SH\tfricative",
    "T\tstop",
    "V\tfricative",
    "W\tsemivowel",
    "Y\tsemivowel",
    "Z\tfricative",
)
SYMBOL_ROWS = tuple(
    [
        *("AE", "AH", "AO", "AY", "ER", "IH", "IY", "OW", "UW"),
        *(
            f"{phone}{stress}"
            for phone in ("AE", "AH", "AO", "AY", "ER", "IH", "IY", "OW", "UW")
            for stress in "012"
        ),
        "B",
        "D",
        "DH",
        "F",
        "HH",
        "K",
        "L",
        "M",
        "N",
        "NG",
        "P",
        "R",
        "S",
        "SH",
        "T",
        "V",
        "W",
        "Y",
        "Z",
    ]
)


def _write_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    dictionary = tmp_path / "cmudict.dict"
    phones = tmp_path / "cmudict.phones"
    symbols = tmp_path / "cmudict.symbols"
    dictionary.write_text("\n".join(DICTIONARY_ROWS) + "\n", encoding="utf-8")
    phones.write_text("\n".join(PHONE_ROWS) + "\n", encoding="utf-8")
    symbols.write_text("\n".join(SYMBOL_ROWS) + "\n", encoding="utf-8")
    return dictionary, phones, symbols


def _spec(path: Path, resource_id: str) -> ResourceSpec:
    return ResourceSpec(
        resource_id=resource_id,
        display_name=f"Synthetic {resource_id}",
        relative_path=path.name,
        version="synthetic-v1",
        accepted_sha256=(hashlib.sha256(path.read_bytes()).hexdigest(),),
        citation="Constructed pronunciation fixture.",
        license_notice="Synthetic test data.",
    )


def _module(tmp_path: Path) -> PronunciationModule:
    dictionary, phones, symbols = _write_fixture(tmp_path)
    return PronunciationModule(
        tmp_path,
        dictionary_spec=_spec(dictionary, "dictionary"),
        phones_spec=_spec(phones, "phones"),
        symbols_spec=_spec(symbols, "symbols"),
        expected_dictionary_rows=len(DICTIONARY_ROWS),
        expected_phone_rows=len(PHONE_ROWS),
        expected_symbol_rows=len(SYMBOL_ROWS),
    )


def _analyze(
    tmp_path: Path,
    preprocessor,
    text: str,
    configuration: PronunciationConfiguration | None = None,
):
    poem = preprocessor.process_document(
        create_text_document("pronunciation-test", "Pronunciation test", text)
    )
    return _module(tmp_path).analyze_detailed(
        ModuleInput.from_poem_document(poem),
        configuration or PronunciationConfiguration(),
    )


def test_adapter_preserves_alternatives_and_vowelless_source_rows(
    tmp_path: Path,
) -> None:
    dictionary, phones, symbols = _write_fixture(tmp_path)

    lexicon = CMUDictAdapter().load(
        dictionary,
        phones,
        symbols,
        expected_dictionary_rows=len(DICTIONARY_ROWS),
        expected_phone_rows=len(PHONE_ROWS),
        expected_symbol_rows=len(SYMBOL_ROWS),
    )

    permit = lexicon.lookup("PERMIT")
    assert permit is not None
    assert [item.variant_number for item in permit.pronunciations] == [1, 2]
    assert [item.stress_pattern for item in permit.pronunciations] == ["01", "12"]
    assert lexicon.validation.vowelless_pronunciations == 1
    assert lexicon.lookup("O\u2019ER") is not None


def test_unique_consensus_ambiguous_unmatched_and_vowelless_are_distinct(
    tmp_path: Path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "stone wind permit quorvax hm",
    )
    by_surface = {item.surface_form: item for item in result.token_audit}

    assert by_surface["stone"].status is PronunciationStatus.DICTIONARY_UNIQUE
    assert by_surface["stone"].resolved_syllable_count == 1
    assert (
        by_surface["wind"].status
        is PronunciationStatus.DICTIONARY_PROSODIC_CONSENSUS
    )
    assert by_surface["wind"].resolved_phones is None
    assert by_surface["wind"].resolved_stress_pattern == "1"
    assert by_surface["permit"].status is PronunciationStatus.AMBIGUOUS_DICTIONARY
    assert by_surface["permit"].resolved_syllable_count is None
    assert by_surface["quorvax"].status is PronunciationStatus.UNMATCHED
    assert (
        by_surface["hm"].status
        is PronunciationStatus.SOURCE_WITHOUT_MARKED_VOWEL
    )
    assert result.summary.resolved_token_count == 2
    assert result.summary.token_coverage == pytest.approx(0.4)


def test_dictionary_candidate_selection_is_validated_and_auditable(
    tmp_path: Path,
    preprocessor,
) -> None:
    override = PronunciationOverride(
        term="permit",
        phones=("P", "ER0", "M", "IH1", "T"),
        note="Verb reading in this line.",
    )
    result = _analyze(
        tmp_path,
        preprocessor,
        "permit rings",
        PronunciationConfiguration(overrides=(override,)),
    )
    permit = result.token_audit[0]

    assert permit.status is PronunciationStatus.DICTIONARY_USER_SELECTION
    assert permit.resolved_syllable_count == 2
    assert permit.resolved_stress_pattern == "01"
    assert permit.override_note == "Verb reading in this line."
    assert permit.dictionary_candidate_count == 2
    assert result.line_summaries[0].is_complete
    assert result.line_summaries[0].syllable_count == 3
    assert result.line_summaries[0].lexical_stress_sequence == "01 | 1"
    assert result.summary.override_token_count == 1


def test_incomplete_lines_remain_missing_instead_of_undercounted(
    tmp_path: Path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "stone rings\nstone quorvax\n",
    )
    first, second = result.line_summaries

    assert first.is_complete and first.syllable_count == 2
    assert first.compact_stress_sequence == "11"
    assert not second.is_complete
    assert second.syllable_count is None
    assert second.lexical_stress_sequence is None
    assert result.summary.syllables_per_complete_line.count == 1
    assert result.summary.syllables_per_complete_line.mean == 2.0


def test_proper_names_are_eligible_and_exact_observed_forms_are_used(
    tmp_path: Path,
    preprocessor,
) -> None:
    result = _analyze(tmp_path, preprocessor, "Alice stone's O\u2019er")
    by_surface = {item.surface_form: item for item in result.token_audit}

    assert by_surface["Alice"].is_proper_noun
    assert by_surface["Alice"].resolved
    assert by_surface["stone's"].status is PronunciationStatus.UNMATCHED
    assert by_surface["O\u2019er"].resolved


def test_recorded_contractions_use_complete_observed_form_not_model_fragments(
    tmp_path: Path,
    preprocessor,
) -> None:
    result = _analyze(
        tmp_path,
        preprocessor,
        "You're can't won't I\u2019m I\u2019d we'll she'll isn't didn't \u2019tis.",
    )
    eligible = [item for item in result.token_audit if item.eligible]
    excluded = [item for item in result.token_audit if not item.eligible]

    assert [item.lookup_form for item in eligible] == [
        "you're",
        "can't",
        "won't",
        "i'm",
        "i'd",
        "we'll",
        "she'll",
        "isn't",
        "didn't",
        "'tis",
    ]
    assert all(item.resolved for item in eligible)
    assert all(
        "preserved contraction span" in item.reason
        for item in eligible
    )
    assert {item.surface_form for item in excluded} >= {
        "'re",
        "n't",
        "\u2019",
    }
    assert all(
        item.status is PronunciationStatus.NOT_ELIGIBLE
        for item in excluded
    )
    assert result.summary.eligible_token_count == 10
    assert result.summary.resolved_token_count == 10
    assert result.summary.unmatched_token_count == 0
    assert result.line_summaries[0].is_complete
    assert result.line_summaries[0].syllable_count == 12
    assert result.line_summaries[0].compact_stress_sequence == "111111110101"


def test_override_parser_requires_notes_and_rejects_unknown_symbols(
    tmp_path: Path,
    preprocessor,
) -> None:
    parsed = parse_pronunciation_overrides(
        "# poem-specific readings\npermit = P ER0 M IH1 T | verb reading"
    )
    assert parsed[0].lookup_form == "permit"

    with pytest.raises(ValueError, match="requires a note"):
        parse_pronunciation_overrides("permit = P ER0 M IH1 T")
    with pytest.raises(ValueError, match="Duplicate"):
        parse_pronunciation_overrides(
            "permit = P ER0 M IH1 T | verb\nPERMIT = P ER1 M IH2 T | noun"
        )
    with pytest.raises(PronunciationModuleError, match="Unknown CMUdict symbol"):
        _analyze(
            tmp_path,
            preprocessor,
            "stone",
            PronunciationConfiguration(
                overrides=(
                    PronunciationOverride(
                        term="stone",
                        phones=("ZZZ1",),
                        note="Invalid test override.",
                    ),
                )
            ),
        )


def test_session_override_upsert_adds_and_replaces_normalized_word() -> None:
    text = upsert_pronunciation_override_text(
        "fire = F AY1 ER0 | two syllables",
        term="permit",
        phones_text="P ER0 M IH1 T",
        note="Selected dictionary candidate.",
    )
    parsed = parse_pronunciation_overrides(text)
    assert [row.lookup_form for row in parsed] == ["fire", "permit"]

    replaced = upsert_pronunciation_override_text(
        text,
        term="PERMIT",
        phones_text="P ER1 M IH2 T",
        note="Context supports the noun reading.",
    )
    parsed_replacement = parse_pronunciation_overrides(replaced)
    assert len(parsed_replacement) == 2
    assert parsed_replacement[1].phones_text == "P ER1 M IH2 T"
    assert parsed_replacement[1].note == "Context supports the noun reading."


def test_empty_input_and_repeated_words_are_deterministic(
    tmp_path: Path,
    preprocessor,
) -> None:
    empty = _analyze(tmp_path, preprocessor, "")
    first = _analyze(tmp_path, preprocessor, "stone stone")
    second = _analyze(tmp_path, preprocessor, "stone stone")

    assert empty.summary.eligible_token_count == 0
    assert empty.summary.token_coverage is None
    assert empty.summary.stress_density is None
    assert first == second
    assert first.summary.resolved_token_count == 2
    assert first.type_summaries[0].token_occurrences == 2


def test_invalid_source_contract_is_reported_without_partial_activation(
    tmp_path: Path,
) -> None:
    dictionary, phones, symbols = _write_fixture(tmp_path)
    dictionary.write_text("stone S T UNKNOWN1 N\n", encoding="utf-8")

    with pytest.raises(CMUDictAdapterError, match="structural problems"):
        CMUDictAdapter().load(
            dictionary,
            phones,
            symbols,
            expected_dictionary_rows=1,
            expected_phone_rows=len(PHONE_ROWS),
            expected_symbol_rows=len(SYMBOL_ROWS),
        )
