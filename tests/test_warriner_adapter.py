from __future__ import annotations

import csv
from pathlib import Path

import pytest

from versevad.adapters import LexiconAdapterError, WarrinerVadAdapter
from versevad.analysis import analyze_vad
from versevad.preprocessing import create_text_document
from versevad.validation import PHASE1_DEMO_TEXT


HEADER = ["Word", "V.Mean.Sum", "A.Mean.Sum", "D.Mean.Sum"]


def _write_fixture(path: Path, rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.writer(destination)
        writer.writerow(HEADER)
        writer.writerows(rows)


def test_warriner_adapter_preserves_original_and_normalized_scores(tmp_path: Path) -> None:
    source = tmp_path / "warriner.csv"
    _write_fixture(source, [["invented", 1, 5, 9]])

    lexicon = WarrinerVadAdapter().load(source)
    entry = lexicon.entries["invented"]

    assert entry.original.as_dict() == {"valence": 1.0, "arousal": 5.0, "dominance": 9.0}
    assert entry.normalized.as_dict() == {
        "valence": 0.0,
        "arousal": 0.5,
        "dominance": 1.0,
    }
    assert source.read_text(encoding="utf-8").startswith("Word,")


def test_warriner_adapter_stops_on_missing_columns(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_text("Word,V.Mean.Sum\ninvented,5\n", encoding="utf-8")

    with pytest.raises(LexiconAdapterError) as captured:
        WarrinerVadAdapter().load(source)

    assert "expected columns" in str(captured.value)
    assert not captured.value.data_changed
    assert "A.Mean.Sum" in captured.value.technical_detail


def test_warriner_adapter_stops_on_malformed_duplicate_or_range_errors(
    tmp_path: Path,
) -> None:
    source = tmp_path / "bad.csv"
    _write_fixture(
        source,
        [
            ["duplicate", 5, 5, 5],
            ["duplicate", 5, 5, 5],
            ["out-of-range", 10, 5, 5],
            ["malformed", "not-a-number", 5, 5],
        ],
    )

    with pytest.raises(LexiconAdapterError) as captured:
        WarrinerVadAdapter().load(source)

    assert "structural problems" in str(captured.value)
    assert "duplicate" in captured.value.technical_detail.lower()
    assert "outside" in captured.value.technical_detail.lower()
    assert "malformed" in captured.value.technical_detail.lower()


def test_warriner_adapter_preserves_casefold_collisions_for_review(
    tmp_path: Path,
) -> None:
    source = tmp_path / "case.csv"
    _write_fixture(
        source,
        [
            ["invented", 2, 3, 4],
            ["Invented", 7, 6, 5],
        ],
    )

    lexicon = WarrinerVadAdapter().load(source)

    assert lexicon.validation.is_valid
    assert lexicon.validation.conflicting_normalized_keys == 1
    assert len(lexicon.conflicting_entries["invented"]) == 2
    lowercase, conflict = lexicon.resolve("invented", "invented")
    capitalized, second_conflict = lexicon.resolve("invented", "Invented")
    ambiguous, unresolved = lexicon.resolve("invented", "INVENTED")
    assert lowercase is not None and lowercase.original.valence == 2
    assert not conflict
    assert capitalized is not None and capitalized.original.valence == 7
    assert not second_conflict
    assert ambiguous is None and unresolved


def test_engine_does_not_guess_when_casefold_collision_is_unresolved(
    tmp_path: Path, preprocessor
) -> None:
    source = tmp_path / "case.csv"
    _write_fixture(
        source,
        [
            ["invented", 2, 3, 4],
            ["Invented", 7, 6, 5],
        ],
    )
    lexicon = WarrinerVadAdapter().load(source)
    document = create_text_document(
        "case-conflict", "Case conflict", "INVENTED invented Invented."
    )

    result = analyze_vad(document, lexicon, preprocessor)
    lexical_pairs = [
        (token.surface_form, match)
        for token, match in zip(result.tokens, result.matches, strict=True)
        if token.is_lexical
    ]

    assert lexical_pairs[0][0] == "INVENTED"
    assert not lexical_pairs[0][1].included
    assert "collide" in lexical_pairs[0][1].reason
    assert lexical_pairs[1][1].included
    assert lexical_pairs[1][1].original_scores is not None
    assert lexical_pairs[1][1].original_scores.valence == 2
    assert lexical_pairs[2][1].included
    assert lexical_pairs[2][1].original_scores is not None
    assert lexical_pairs[2][1].original_scores.valence == 7


def test_warriner_adapter_reports_invalid_utf8(tmp_path: Path) -> None:
    source = tmp_path / "bad.csv"
    source.write_bytes(b"Word,V.Mean.Sum,A.Mean.Sum,D.Mean.Sum\n\xff,5,5,5")

    with pytest.raises(LexiconAdapterError) as captured:
        WarrinerVadAdapter().load(source)

    assert "UTF-8" in str(captured.value)
    assert not captured.value.data_changed


def test_local_supplied_warriner_file_passes_contract_if_present() -> None:
    source = Path(
        "source_lexicons/XANEW-master/XANEW-master/Ratings_Warriner_et_al.csv"
    )
    if not source.is_file():
        pytest.skip("The restricted user-supplied Warriner file is not present.")

    lexicon = WarrinerVadAdapter().load(source)

    assert lexicon.validation.is_valid
    assert lexicon.validation.total_rows == 13_915
    assert lexicon.validation.usable_entries == 13_915
    assert lexicon.validation.phrase_entries == 102
    assert lexicon.validation.conflicting_normalized_keys == 10
    assert lexicon.validation.source_sha256 == (
        "78ac8107c78e116bb96538fae4faa47281a155f5f8fe39f30bbc6ea3db05b446"
    )


def test_local_warriner_adapter_integrates_with_engine_if_present(preprocessor) -> None:
    source = Path(
        "source_lexicons/XANEW-master/XANEW-master/Ratings_Warriner_et_al.csv"
    )
    if not source.is_file():
        pytest.skip("The restricted user-supplied Warriner file is not present.")

    result = analyze_vad(
        create_text_document("local-smoke", "Local smoke test", PHASE1_DEMO_TEXT),
        WarrinerVadAdapter().load(source),
        preprocessor,
    )

    assert result.lexicon_metadata.lexicon_id == "warriner_vad_2013"
    assert result.coverage.matched_token_count > 0
    for match in result.matches:
        if match.included:
            assert match.original_scores is not None
            assert all(1 <= value <= 9 for value in match.original_scores.as_dict().values())
            assert match.normalized_scores is not None
            assert all(
                0 <= value <= 1 for value in match.normalized_scores.as_dict().values()
            )
