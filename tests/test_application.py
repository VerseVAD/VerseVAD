import csv
import io
import zipfile

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
    emotion_association_views,
    emotion_intensity_views,
    match_views,
    overview_notes,
    run_workspace_analysis,
    scholar_summary_csv,
    unmatched_views,
    vad_views,
)
from versevad.models import PhrasePolicy
from versevad.phase2_validation import (
    phase2_synthetic_emotion_lexicon,
    phase2_synthetic_intensity_lexicon,
    phase2_synthetic_vad_lexicon,
)
from versevad.preprocessing import create_text_document


@pytest.fixture
def synthetic_workspace(preprocessor) -> WorkspaceAnalysis:
    document = create_text_document(
        "friendly-summary", "Friendly summary", "Fear joy dark night."
    )
    results = (
        analyze_lexicon(document, phase2_synthetic_vad_lexicon(), preprocessor),
        analyze_lexicon(document, phase2_synthetic_emotion_lexicon(), preprocessor),
        analyze_lexicon(document, phase2_synthetic_intensity_lexicon(), preprocessor),
    )
    request = AnalysisRequest(
        project_name="Test workspace",
        title=document.title,
        original_text=document.original_text,
        lexicon_ids=tuple(result.lexicon_metadata.lexicon_id for result in results),
    )
    return WorkspaceAnalysis(request, document, results, compare_lexicons(results))


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
    assert len(workspace.results) == 1
    assert workspace.results[0].lexicon_validation.source_sha256.startswith("42c71881")
    assert workspace.results[0].coverage.phrase_match_count >= 1


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
    assert len(vad) == 1
    assert vad[0].normalized_valence is not None
    assert vad[0].original_scale == "1 to 9"
    associations = emotion_association_views(synthetic_workspace)
    fear = next(row for row in associations if row.category == "fear")
    assert fear.token_count == 1
    assert fear.rate_per_lexical_token == pytest.approx(0.25)
    intensities = emotion_intensity_views(synthetic_workspace)
    fear_intensity = next(row for row in intensities if row.category == "fear")
    assert fear_intensity.mean_matched_intensity == pytest.approx(0.6)
    assert any("not expected to sum" in note for note in overview_notes(synthetic_workspace))


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
        "Normalized VAD",
        "Emotion association",
        "Emotion intensity",
    }
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
        start_here = bundle.read("START_HERE.txt").decode("utf-8")
        assert "lexical evidence" in start_here
