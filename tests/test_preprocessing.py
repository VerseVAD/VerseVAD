from __future__ import annotations

import hashlib

from versevad.preprocessing import create_text_document


def test_original_text_checksum_and_structure_are_preserved(preprocessor) -> None:
    original = "Mountains cried.\n\nBroken stone.\n"
    document = create_text_document("structure", "Structure fixture", original)

    tokens = preprocessor.process(document)
    lexical = [token for token in tokens if token.is_lexical]

    assert document.original_text == original
    assert document.text_sha256 == hashlib.sha256(original.encode("utf-8")).hexdigest()
    assert [(token.surface_form, token.line_number, token.stanza_number) for token in lexical] == [
        ("Mountains", 1, 1),
        ("cried", 1, 1),
        ("Broken", 3, 2),
        ("stone", 3, 2),
    ]


def test_pinned_pipeline_provides_pos_sensitive_lemmas(preprocessor) -> None:
    document = create_text_document(
        "lemmas", "Lemma fixture", "Mountains cried. Broken arms rested."
    )
    tokens = preprocessor.process(document)
    by_surface = {token.surface_form: token for token in tokens}

    assert by_surface["Mountains"].normalized_lemma == "mountain"
    assert by_surface["Mountains"].part_of_speech in {"NOUN", "PROPN"}
    assert by_surface["cried"].normalized_lemma == "cry"
    assert by_surface["cried"].part_of_speech == "VERB"
    assert by_surface["rested"].normalized_lemma == "rest"


def test_possessive_noun_is_one_auditable_token(preprocessor) -> None:
    document = create_text_document("possessive", "Possessive fixture", "Death’s shadow.")
    lexical = [token for token in preprocessor.process(document) if token.is_lexical]

    assert lexical[0].surface_form == "Death’s"
    assert lexical[0].normalized_lemma == "death"
    assert lexical[0].part_of_speech == "NOUN"


def test_same_surface_form_retains_different_pos_and_lemma_analyses(preprocessor) -> None:
    document = create_text_document("ambiguous", "Ambiguous form", "I saw a saw.")

    saw_tokens = [
        token for token in preprocessor.process(document) if token.normalized_form == "saw"
    ]

    assert len(saw_tokens) == 2
    assert (saw_tokens[0].part_of_speech, saw_tokens[0].normalized_lemma) == (
        "VERB",
        "see",
    )
    assert (saw_tokens[1].part_of_speech, saw_tokens[1].normalized_lemma) == (
        "NOUN",
        "saw",
    )
