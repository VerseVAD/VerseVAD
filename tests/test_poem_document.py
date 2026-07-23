from __future__ import annotations

from dataclasses import replace

import pytest

from versevad.core.documents import (
    ModelVocabularyState,
    OrthographicFeatureKind,
    PreprocessingConfiguration,
    StructuralUnitKind,
    TokenRole,
)
from versevad.core.modules import ModuleInput
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document


def test_explicit_hierarchy_preserves_lines_stanzas_and_blank_separator(
    preprocessor,
) -> None:
    original = "The hawk\r\n  turns above stone.\r\n\r\nNight enters.\r\n"
    source = create_text_document("hierarchy", "Hierarchy", original)

    poem = preprocessor.process_document(source)

    assert poem.source is source
    assert poem.section.kind is StructuralUnitKind.SECTION
    assert poem.section.raw_text == original
    assert len(poem.stanzas) == 2
    assert len(poem.lines) == 4
    assert "".join(line.raw_text for line in poem.lines) == original
    assert [line.content_text for line in poem.lines] == [
        "The hawk",
        "  turns above stone.",
        "",
        "Night enters.",
    ]
    assert [line.line_ending for line in poem.lines] == ["\r\n"] * 4
    assert poem.lines[1].indentation == "  "
    assert poem.lines[2].is_blank
    assert poem.lines[2].parent_id == poem.section.unit_id
    assert poem.lines[0].parent_id == poem.stanzas[0].unit_id
    assert poem.lines[3].parent_id == poem.stanzas[1].unit_id


def test_sentence_and_dependencies_can_cross_a_line_boundary(preprocessor) -> None:
    source = create_text_document(
        "lineation",
        "Lineation",
        "The hawk\nturns above the stone.\n",
    )

    poem = preprocessor.process_document(source)

    assert len(poem.sentences) == 1
    assert poem.sentences[0].crosses_line_boundary
    assert poem.sentences[0].raw_text == "The hawk\nturns above the stone.\n"
    assert any(record.crosses_line_boundary for record in poem.dependencies)
    assert all(record.confidence is None for record in poem.dependencies)


def test_hyphen_contraction_and_apostrophe_forms_are_explicit(preprocessor) -> None:
    source = create_text_document(
        "orthography",
        "Orthography",
        "The moon-lit stone doesn't move; O'Brien watches.",
    )

    poem = preprocessor.process_document(source)
    features = {(item.kind, item.raw_text): item for item in poem.orthographic_spans}

    assert (
        OrthographicFeatureKind.HYPHENATED_EXPRESSION,
        "moon-lit",
    ) in features
    assert (OrthographicFeatureKind.CONTRACTION, "doesn't") in features
    assert (OrthographicFeatureKind.APOSTROPHE_FORM, "O'Brien") in features

    by_surface = {token.surface_form: token for token in poem.tokens}
    classifications = poem.classification_map()
    assert classifications[by_surface["The"].token_id].role is TokenRole.FUNCTION
    assert classifications[by_surface["moon"].token_id].role is TokenRole.CONTENT
    assert classifications[by_surface[";"].token_id].role is TokenRole.NON_LEXICAL
    assert classifications[by_surface["O'Brien"].token_id].has_apostrophe


def test_original_unicode_is_unchanged_and_lookup_form_is_separate(
    preprocessor,
) -> None:
    original = "Cafe\u0301 waits — BRIGHT.\n"
    source = create_text_document("unicode", "Unicode", original)

    poem = preprocessor.process_document(source)
    lexical = [token for token in poem.tokens if token.is_lexical]

    assert poem.source.original_text == original
    assert poem.section.raw_text == original
    assert lexical[0].surface_form == "Cafe\u0301"
    assert lexical[0].normalized_form == "café"
    assert lexical[-1].surface_form == "BRIGHT"
    assert lexical[-1].lowercase_form == "bright"
    assert any(token.surface_form == "—" for token in poem.tokens)


def test_one_word_lines_and_repeated_refrains_remain_distinct(preprocessor) -> None:
    source = create_text_document(
        "refrain",
        "Refrain",
        "Alone\nAlone\n\nO'er\nwind without punctuation\n",
    )

    poem = preprocessor.process_document(source)

    assert [line.content_text for line in poem.lines] == [
        "Alone",
        "Alone",
        "",
        "O'er",
        "wind without punctuation",
    ]
    assert poem.lines[0].unit_id != poem.lines[1].unit_id
    assert [token.surface_form for token in poem.tokens].count("Alone") == 2
    assert any(token.surface_form == "O'er" for token in poem.tokens)


def test_default_small_model_reports_oov_tracking_as_unavailable(
    preprocessor,
) -> None:
    source = create_text_document("oov", "OOV", "quizzacious stone")

    poem = preprocessor.process_document(source)

    assert not poem.coverage.model_vocabulary_available
    assert poem.coverage.model_oov_count is None
    assert poem.coverage.model_oov_rate is None
    assert {
        item.model_vocabulary_state for item in poem.token_classifications
    } == {ModelVocabularyState.UNAVAILABLE}
    assert "model_vocabulary_unavailable" in {
        warning.code for warning in poem.warnings
    }


def test_named_entities_are_optional_and_disabled_by_default(preprocessor) -> None:
    source = create_text_document("ner-off", "NER off", "Barack Obama visited Paris.")

    poem = preprocessor.process_document(source)

    assert not poem.configuration.enable_ner
    assert poem.entities == ()
    assert "ner" in poem.preprocessing.disabled_components


def test_named_entities_can_be_enabled_explicitly() -> None:
    processor = SpacyEnglishPreprocessor(
        configuration=PreprocessingConfiguration(enable_ner=True)
    )
    source = create_text_document("ner-on", "NER on", "Barack Obama visited Paris.")

    poem = processor.process_document(source)

    assert poem.configuration.enable_ner
    assert "ner" not in poem.preprocessing.disabled_components
    assert any(entity.raw_text == "Barack Obama" for entity in poem.entities)
    assert all(entity.token_ids for entity in poem.entities)


def test_empty_text_has_one_preserved_blank_line_and_missing_coverage(
    preprocessor,
) -> None:
    source = create_text_document("empty-poem", "Empty poem", "")

    poem = preprocessor.process_document(source)

    assert len(poem.lines) == 1
    assert poem.lines[0].is_blank
    assert poem.lines[0].raw_text == ""
    assert poem.tokens == ()
    assert poem.coverage.sentence_annotation_rate is None
    assert "empty_text" in {warning.code for warning in poem.warnings}


def test_processing_is_deterministic_for_the_same_text_version(preprocessor) -> None:
    source = create_text_document("stable", "Stable", "Stone.\n\nStone.\n")

    first = preprocessor.process_document(source)
    second = preprocessor.process_document(source)

    assert first == second


def test_common_module_input_accepts_the_shared_poem_document(preprocessor) -> None:
    source = create_text_document("module-input", "Module input", "Stone moves.")
    poem = preprocessor.process_document(source)

    module_input = ModuleInput.from_poem_document(poem)

    assert module_input.poem_document is poem
    assert module_input.document is source
    assert module_input.tokens == poem.tokens
    assert module_input.preprocessing == poem.preprocessing


def test_content_and_function_pos_sets_cannot_overlap() -> None:
    with pytest.raises(ValueError, match="cannot overlap"):
        PreprocessingConfiguration(
            content_pos_tags=("NOUN", "DET"),
            function_pos_tags=("DET",),
        )


def test_poem_document_rejects_inconsistent_processing_coverage(
    preprocessor,
) -> None:
    source = create_text_document("bad-coverage", "Bad coverage", "Stone.")
    poem = preprocessor.process_document(source)

    with pytest.raises(ValueError, match="coverage"):
        replace(
            poem.coverage,
            total_token_count=poem.coverage.total_token_count + 1,
        )
