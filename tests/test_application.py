import csv
import io
import json
import zipfile
from dataclasses import replace

import pytest

from versevad.analysis.phase2 import analyze_lexicon, compare_lexicons
from versevad.application import (
    AnalysisRequest,
    TextImportError,
    WorkspaceAnalysis,
    WorkspaceAnalysisError,
    coverage_views,
    csv_reading_guide,
    decode_uploaded_text,
    detailed_export_zip,
    detailed_part_of_speech_views_for_tokens,
    emotion_association_views,
    emotion_intensity_views,
    match_views,
    overview_notes,
    part_of_speech_views,
    part_of_speech_views_for_tokens,
    run_workspace_analysis,
    scholar_summary_csv,
    sentiment_association_views,
    unmatched_views,
    vad_views,
)
from versevad.models import PhrasePolicy
from versevad.phase2_validation import (
    phase2_synthetic_emotion_lexicon,
    phase2_synthetic_intensity_lexicon,
    phase2_synthetic_vad_lexicon,
)
from versevad.preprocessing import (
    PreparedPoemPreprocessor,
    SpacyEnglishPreprocessor,
    create_text_document,
)
from tests.test_pronunciation import _module as synthetic_pronunciation_module


@pytest.fixture
def synthetic_workspace(preprocessor) -> WorkspaceAnalysis:
    document = create_text_document(
        "friendly-summary", "Friendly summary", "Fear joy dark night."
    )
    poem_document = preprocessor.process_document(document)
    prepared = PreparedPoemPreprocessor(poem_document)
    results = (
        analyze_lexicon(document, phase2_synthetic_vad_lexicon(), prepared),
        analyze_lexicon(document, phase2_synthetic_emotion_lexicon(), prepared),
        analyze_lexicon(document, phase2_synthetic_intensity_lexicon(), prepared),
    )
    request = AnalysisRequest(
        project_name="Test workspace",
        title=document.title,
        original_text=document.original_text,
        lexicon_ids=tuple(result.lexicon_metadata.lexicon_id for result in results),
    )
    return WorkspaceAnalysis(
        request,
        document,
        results,
        compare_lexicons(results),
        poem_document,
    )


def _csv_rows(content: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content.decode("utf-8-sig"))))


def test_text_file_import_preserves_unicode_and_line_endings() -> None:
    content = "Stone’s edge\r\nSecond line.\r\n".encode("utf-8")
    assert decode_uploaded_text("poem.TXT", content) == content.decode("utf-8")


def test_text_file_import_rejects_unsupported_or_invalid_files() -> None:
    with pytest.raises(TextImportError, match="plain-text"):
        decode_uploaded_text("poem.docx", b"not a Word file")
    with pytest.raises(TextImportError, match="UTF-8"):
        decode_uploaded_text("poem.txt", b"\xff\xfe")
    with pytest.raises(TextImportError, match="ordinary plain-text"):
        decode_uploaded_text("poem.txt", b"abc\x00def")


def test_workspace_analysis_preserves_text_and_runs_selected_real_source(preprocessor) -> None:
    original = "A bit of bright night.\n"
    request = AnalysisRequest(
        project_name="Private reading",
        title="Working title",
        original_text=original,
        lexicon_ids=("nrc_vad_v2_1",),
        phrase_policy=PhrasePolicy.PHRASE_PREFERRED,
    )
    workspace = run_workspace_analysis(request, preprocessor=preprocessor)
    assert workspace.document.original_text == original
    assert workspace.poem_document is not None
    assert workspace.poem_document.source is workspace.document
    assert workspace.poem_document.tokens == workspace.results[0].tokens
    assert len(workspace.results) == 1
    assert workspace.results[0].lexicon_validation.source_sha256.startswith("42c71881")
    assert workspace.results[0].coverage.phrase_match_count >= 1


def test_workspace_poetry_id_reuses_completed_vad_and_has_no_json_export(
    preprocessor,
) -> None:
    request = AnalysisRequest(
        project_name="PoetryID workspace",
        title="Profile evidence",
        original_text="joy love peace light happy calm strong",
        lexicon_ids=("nrc_vad_v1",),
        include_poetry_id=True,
    )

    workspace = run_workspace_analysis(request, preprocessor=preprocessor)

    assert workspace.poetry_id is not None
    assert workspace.poetry_id.status == "complete"
    assert {row.source_analysis_id for row in workspace.poetry_id.assignments} == {
        workspace.results[0].analysis_id
    }
    assert {row.weighting_mode for row in workspace.poetry_id.assignments} == {
        "token",
        "type",
    }
    with zipfile.ZipFile(io.BytesIO(detailed_export_zip(workspace))) as bundle:
        poetry_id_files = {
            name for name in bundle.namelist() if name.startswith("poetry_id_")
        }
        assert poetry_id_files == {
            "poetry_id_summary.csv",
            "poetry_id_neighbors.csv",
            "poetry_id_lexical_character.csv",
            "poetry_id_methodology.csv",
            "poetry_id_archetype_map.csv",
            "poetry_id_vad_scales.csv",
            "poetry_id_report.txt",
        }
        assert not any(name.endswith(".json") for name in poetry_id_files)


def test_workspace_preprocesses_once_for_multiple_lexicons() -> None:
    class CountingPreprocessor:
        def __init__(self) -> None:
            self.delegate = SpacyEnglishPreprocessor()
            self.document_calls = 0
            self.token_calls = 0

        @property
        def metadata(self):
            return self.delegate.metadata

        def process_document(self, document):
            self.document_calls += 1
            return self.delegate.process_document(document)

        def process(self, document):
            self.token_calls += 1
            return self.delegate.process(document)

    processor = CountingPreprocessor()
    request = AnalysisRequest(
        project_name="Shared processing",
        title="One representation",
        original_text="Bright night.",
        lexicon_ids=("nrc_vad_v1", "nrc_emotion_v0_92"),
    )

    workspace = run_workspace_analysis(request, preprocessor=processor)

    assert processor.document_calls == 1
    assert processor.token_calls == 0
    assert workspace.poem_document is not None
    assert all(
        result.tokens == workspace.poem_document.tokens
        for result in workspace.results
    )


def test_workspace_requires_title_text_and_lexicon(preprocessor) -> None:
    base = dict(project_name="Temporary", title="Poem", original_text="Stone.")
    with pytest.raises(WorkspaceAnalysisError, match="title"):
        run_workspace_analysis(
            AnalysisRequest(**{**base, "title": "", "lexicon_ids": ("nrc_vad_v1",)}),
            preprocessor=preprocessor,
        )
    with pytest.raises(WorkspaceAnalysisError, match="Paste a poem"):
        run_workspace_analysis(
            AnalysisRequest(**{**base, "original_text": "", "lexicon_ids": ("nrc_vad_v1",)}),
            preprocessor=preprocessor,
        )
    with pytest.raises(WorkspaceAnalysisError, match="at least one"):
        run_workspace_analysis(
            AnalysisRequest(**base, lexicon_ids=()), preprocessor=preprocessor
        )


def test_readable_views_keep_constructs_and_denominators_separate(
    synthetic_workspace,
) -> None:
    coverage = coverage_views(synthetic_workspace)
    assert len(coverage) == 3
    assert all(row.lexical_tokens == 4 for row in coverage)
    vad = vad_views(synthetic_workspace)
    assert len(vad) == 2
    assert {row.analysis_view for row in vad} == {
        "All matched tokens",
        "Stopwords excluded",
    }
    assert vad[0].normalized_valence is not None
    assert vad[0].original_scale == "1 to 9"
    associations = emotion_association_views(synthetic_workspace)
    assert {row.category for row in associations} <= {
        "anger",
        "anticipation",
        "disgust",
        "fear",
        "joy",
        "sadness",
        "surprise",
        "trust",
    }
    assert not {"positive", "negative"} & {row.category for row in associations}
    fear = next(row for row in associations if row.category == "fear")
    assert fear.token_count == 1
    assert fear.rate_per_lexical_token == pytest.approx(0.25)
    sentiments = sentiment_association_views(synthetic_workspace)
    assert {row.category for row in sentiments} == {"positive", "negative"}
    pos_rows = part_of_speech_views(synthetic_workspace)
    assert sum(row.token_count for row in pos_rows) == 4
    assert sum(row.share_of_lexical_tokens for row in pos_rows) == pytest.approx(1.0)
    assert all(row.lexical_token_denominator == 4 for row in pos_rows)
    assert all(row.category != "Proper Noun" for row in pos_rows)
    intensities = emotion_intensity_views(synthetic_workspace)
    fear_intensity = next(row for row in intensities if row.category == "fear")
    assert fear_intensity.mean_matched_intensity == pytest.approx(0.6)
    assert any("not expected to sum" in note for note in overview_notes(synthetic_workspace))


def test_part_of_speech_profile_merges_common_and_proper_nouns(
    synthetic_workspace,
) -> None:
    source_tokens = synthetic_workspace.results[0].tokens[:2]
    tokens = (
        replace(
            source_tokens[0],
            part_of_speech="NOUN",
            normalized_form="river",
        ),
        replace(
            source_tokens[1],
            part_of_speech="PROPN",
            normalized_form="raven",
        ),
    )
    rows = part_of_speech_views_for_tokens(tokens)
    assert len(rows) == 1
    assert rows[0].tag == "NOUN + PROPN"
    assert rows[0].category == "Noun"
    assert rows[0].token_count == 2
    assert rows[0].share_of_lexical_tokens == 1.0
    assert rows[0].unique_type_count == 2
    detailed = detailed_part_of_speech_views_for_tokens(tokens)
    assert {row.tag for row in detailed} == {"NOUN", "PROPN"}
    assert {row.category for row in detailed} == {"Common Noun", "Proper Noun"}


def test_part_of_speech_profile_merges_main_and_auxiliary_verbs(
    synthetic_workspace,
) -> None:
    source_tokens = synthetic_workspace.results[0].tokens[:2]
    tokens = (
        replace(
            source_tokens[0],
            part_of_speech="VERB",
            normalized_form="sing",
        ),
        replace(
            source_tokens[1],
            part_of_speech="AUX",
            normalized_form="be",
        ),
    )
    rows = part_of_speech_views_for_tokens(tokens)
    assert len(rows) == 1
    assert rows[0].tag == "VERB + AUX"
    assert rows[0].category == "Verb"
    assert rows[0].token_count == 2
    assert rows[0].share_of_lexical_tokens == 1.0
    detailed = detailed_part_of_speech_views_for_tokens(tokens)
    assert {row.tag for row in detailed} == {"VERB", "AUX"}
    assert {row.category for row in detailed} == {
        "Main Verb",
        "Auxiliary or Copular Verb",
    }


def test_match_and_unmatched_views_are_plain_language_drilldowns(synthetic_workspace) -> None:
    matches = match_views(synthetic_workspace)
    phrase = next(row for row in matches if row.surface == "dark night" and row.status == "included")
    assert phrase.method == "exact_phrase"
    assert "V " in phrase.value
    unmatched = unmatched_views(synthetic_workspace)
    assert any(row.surface.casefold() == "joy" for row in unmatched)
    assert all(row.example_context for row in unmatched)


def test_scholar_summary_and_guide_are_excel_friendly(synthetic_workspace) -> None:
    summary = scholar_summary_csv(synthetic_workspace)
    guide = csv_reading_guide()
    assert summary.startswith(b"\xef\xbb\xbf")
    assert guide.startswith(b"\xef\xbb\xbf")
    summary_rows = _csv_rows(summary)
    assert {row["section"] for row in summary_rows} >= {
        "Coverage",
        "Part of speech",
        "Normalized VAD",
        "Cumulative normative lexical load",
        "Stopword sensitivity",
        "Emotion association",
        "Sentiment association",
        "Emotion intensity",
    }
    vad_metrics = [
        row["metric"] for row in summary_rows if row["section"] == "Normalized VAD"
    ]
    assert any("token-weighted" in metric for metric in vad_metrics)
    assert any("type-weighted" in metric for metric in vad_metrics)
    guide_rows = _csv_rows(guide)
    assert guide_rows[0]["file"] == "scholar_summary.csv"
    assert any(row["file"] == "phase2_match_audit.csv" for row in guide_rows)


def test_detailed_download_starts_with_friendly_files_and_retains_audit(
    synthetic_workspace,
) -> None:
    archive = detailed_export_zip(synthetic_workspace)
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = set(bundle.namelist())
        assert "START_HERE.txt" in names
        assert "scholar_summary.csv" in names
        assert "csv_reading_guide.csv" in names
        assert "phase2_match_audit.csv" in names
        assert "phase2_manifest.csv" in names
        assert "phase2_results.json" in names
        assert "poem_document.json" in names
        poem_document = json.loads(bundle.read("poem_document.json"))
        assert poem_document["source"]["original_text"] == "Fear joy dark night."
        assert poem_document["configuration"]["preserve_original_text"] is True
        assert poem_document["coverage"]["total_token_count"] > 0
        assert any(
            unit["kind"] == "line"
            for unit in poem_document["structural_units"]
        )
        start_here = bundle.read("START_HERE.txt").decode("utf-8")
        assert "lexical evidence" in start_here
        assert "poem_document.json" in start_here


def test_workspace_can_run_pronunciation_without_an_affective_lexicon(
    tmp_path,
    preprocessor,
) -> None:
    request = AnalysisRequest(
        project_name="Pronunciation-only workspace",
        title="Stage 5",
        original_text="stone rings\nstone quorvax",
        lexicon_ids=(),
        include_pronunciation=True,
    )
    workspace = run_workspace_analysis(
        request,
        preprocessor=preprocessor,
        resource_root=tmp_path,
        pronunciation_module=synthetic_pronunciation_module(tmp_path),
    )

    assert workspace.results == ()
    assert workspace.pronunciation is not None
    assert workspace.pronunciation.summary.resolved_token_count == 3
    summary_rows = _csv_rows(scholar_summary_csv(workspace))
    assert any(
        row["section"] == "Pronunciation and prosody foundation"
        for row in summary_rows
    )
    with zipfile.ZipFile(io.BytesIO(detailed_export_zip(workspace))) as bundle:
        names = set(bundle.namelist())
        assert "pronunciation_summary.csv" in names
        assert "pronunciation_lines.csv" in names
        assert "pronunciation_token_audit.csv" in names
        assert "pronunciation_result.json" in names


def test_workspace_can_run_meter_and_automatically_include_pronunciation(
    tmp_path,
    preprocessor,
) -> None:
    tetrameter = "the stone the stone the stone the stone"
    request = AnalysisRequest(
        project_name="Meter-only workspace",
        title="Stage 6",
        original_text="\n".join((tetrameter,) * 4),
        lexicon_ids=(),
        include_meter=True,
    )

    workspace = run_workspace_analysis(
        request,
        preprocessor=preprocessor,
        resource_root=tmp_path,
        pronunciation_module=synthetic_pronunciation_module(tmp_path),
    )

    assert workspace.results == ()
    assert workspace.pronunciation is not None
    assert workspace.meter is not None
    assert workspace.meter.summary.closest_candidate_label == "Iambic tetrameter"
    assert workspace.meter.summary.closest_candidate_kind == (
        "fixed pattern and foot count"
    )
    with zipfile.ZipFile(io.BytesIO(detailed_export_zip(workspace))) as bundle:
        names = set(bundle.namelist())
        assert "meter_summary.csv" in names
        assert "meter_candidates.csv" in names
        assert "meter_schemes.csv" not in names
        assert "meter_lines.csv" in names
        assert "meter_alignment_operations.csv" in names
        assert "meter_result.json" in names


def test_workspace_can_run_phonology_and_automatically_include_pronunciation(
    tmp_path,
    preprocessor,
) -> None:
    request = AnalysisRequest(
        project_name="Rhyme-only workspace",
        title="Stage 7",
        original_text="bright cat\nsilver night\nsoftly hat\nstone bright",
        lexicon_ids=(),
        include_phonology=True,
    )

    workspace = run_workspace_analysis(
        request,
        preprocessor=preprocessor,
        resource_root=tmp_path,
        pronunciation_module=synthetic_pronunciation_module(tmp_path),
    )

    assert workspace.results == ()
    assert workspace.pronunciation is not None
    assert workspace.phonology is not None
    assert workspace.phonology.summary.whole_poem_rhyme_scheme == "ABAB"
    summary_rows = _csv_rows(scholar_summary_csv(workspace))
    assert any(
        row["section"] == "Rhyme and phonological patterns"
        and row["metric"] == "Whole-poem end-rhyme scheme"
        for row in summary_rows
    )
    with zipfile.ZipFile(io.BytesIO(detailed_export_zip(workspace))) as bundle:
        names = set(bundle.namelist())
        assert {
            "rhyme_summary.csv",
            "rhyme_stanzas.csv",
            "rhyme_lines.csv",
            "rhyme_pairs.csv",
            "rhyme_internal.csv",
            "phonological_sounds.csv",
            "rhyme_result.json",
        } <= names


def test_workspace_can_run_lexical_style_without_external_resources(
    tmp_path,
    preprocessor,
) -> None:
    request = AnalysisRequest(
        project_name="Lexical-style-only workspace",
        title="Lexical style",
        original_text="red blue red\ngreen blue\n\nyellow red",
        lexicon_ids=(),
        include_lexical_style=True,
    )

    workspace = run_workspace_analysis(
        request,
        preprocessor=preprocessor,
        resource_root=tmp_path,
    )

    assert workspace.results == ()
    assert workspace.lexical_style is not None
    assert workspace.lexical_style.summary.lexical_token_count == 7
    assert [
        item.word_count for item in workspace.lexical_style.line_summaries
    ] == [3, 2, 0, 2]
    summary_rows = _csv_rows(scholar_summary_csv(workspace))
    assert any(
        row["section"] == "Lexical diversity and word counts"
        and row["metric"] == "Lexical token count"
        for row in summary_rows
    )
    with zipfile.ZipFile(io.BytesIO(detailed_export_zip(workspace))) as bundle:
        assert {
            "lexical_style_summary.csv",
            "lexical_style_word_lengths.csv",
            "lexical_style_lines.csv",
            "lexical_style_stanzas.csv",
            "lexical_style_token_audit.csv",
            "lexical_style_result.json",
        } <= set(bundle.namelist())
