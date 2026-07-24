from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

from versevad.analysis.phase2 import analyze_lexicon, compare_lexicons
from versevad.application import AnalysisRequest, WorkspaceAnalysis
from versevad.corpus import analyze_corpus, corpus_vad_profiles, decode_corpus_files
from versevad.db import CorpusTextImport, ProjectRepository
from versevad.models import PhrasePolicy
from versevad.phase2_validation import phase2_synthetic_vad_lexicon
from versevad.preprocessing import create_text_document


def _workspace(text, preprocessor) -> WorkspaceAnalysis:
    document = replace(
        create_text_document(text.text_id, text.title, text.original_text),
        text_version_id=text.text_version_id,
    )
    result = analyze_lexicon(
        document,
        phase2_synthetic_vad_lexicon(),
        preprocessor,
        phrase_policy=PhrasePolicy.UNIGRAM_ONLY,
    )
    request = AnalysisRequest(
        project_name="Synthetic corpus",
        title=text.title,
        original_text=text.original_text,
        lexicon_ids=(result.lexicon_metadata.lexicon_id,),
        phrase_policy=PhrasePolicy.UNIGRAM_ONLY,
        text_id=text.text_id,
        text_version_id=text.text_version_id,
    )
    return WorkspaceAnalysis(request, document, (result,), compare_lexicons((result,)))


def test_folder_decode_preserves_relative_paths_and_text() -> None:
    summary = decode_corpus_files(
        (
            ("Volume/Second poem.txt", b"Dark.\r\n"),
            ("Volume/First poem.txt", b"Bright.\n"),
        )
    )
    assert [item.relative_path for item in summary.files] == [
        "Volume/First poem.txt",
        "Volume/Second poem.txt",
    ]
    assert summary.files[1].original_text == "Dark.\r\n"
    assert summary.total_bytes == 15


def test_sqlite_import_versions_and_metadata_are_preserved(tmp_path) -> None:
    repository = ProjectRepository(tmp_path / "versevad.sqlite3")
    assert repository.schema_version() == 4
    project = repository.create_project("Jeffers test", researcher="Researcher")
    original = CorpusTextImport("Poem", "poem.txt", "book/poem.txt", "Bright.\n")
    first = repository.import_texts(project.project_id, (original,))[0]
    same = repository.import_texts(project.project_id, (original,))[0]
    assert same.text_version_id == first.text_version_id
    changed = repository.import_texts(
        project.project_id,
        (CorpusTextImport("Poem", "poem.txt", "book/poem.txt", "Bright!\n"),),
    )[0]
    assert changed.text_id == first.text_id
    assert changed.text_version_id != first.text_version_id
    assert changed.original_text == "Bright!\n"
    updated = repository.update_text_metadata(
        changed.text_id,
        title="Poem title",
        author="Robinson Jeffers",
        collection="Volume",
        date_label="1925",
        genre="lyric",
        notes="Editorial note",
        custom_metadata={"sequence": 3},
    )
    assert updated.collection == "Volume"
    assert updated.custom_metadata == {"sequence": 3}
    with sqlite3.connect(repository.database_path) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM text_versions WHERE text_id = ?", (first.text_id,)
        ).fetchone()[0] == 2


def test_completed_batch_persists_metrics_loads_and_unmatched_notes(
    tmp_path,
    preprocessor,
) -> None:
    repository = ProjectRepository(tmp_path / "versevad.sqlite3")
    project = repository.create_project("Corpus")
    texts = repository.import_texts(
        project.project_id,
        (
            CorpusTextImport(
                "Long bright",
                "long.txt",
                "long.txt",
                " ".join(["Bright"] * 10) + " mystery.",
            ),
            CorpusTextImport("Short dark", "short.txt", "short.txt", "Dark."),
        ),
    )
    batch = repository.begin_corpus_batch(
        project.project_id,
        text_ids=(text.text_id for text in texts),
        lexicon_ids=("synthetic_vad_phase2",),
        phrase_policy=PhrasePolicy.UNIGRAM_ONLY.value,
        minimum_match_requirement=3,
    )
    for text in texts:
        repository.save_analysis(
            project.project_id,
            text.text_id,
            _workspace(text, preprocessor),
            batch_id=batch.batch_id,
        )
    assert repository.list_latest_metrics(project.project_id) == ()
    completed = repository.finish_corpus_batch(batch.batch_id)
    assert completed.status == "complete"
    with pytest.raises(ValueError, match="immutable"):
        repository.finish_corpus_batch(batch.batch_id)

    metrics = repository.list_latest_metrics(project.project_id)
    assert any(row.metric == "vad_absolute_midpoint_load" for row in metrics)
    valence = next(
        row
        for row in corpus_vad_profiles(metrics, total_works=2)
        if row.dimension == "valence" and row.analysis_view == "all_matched"
    )
    assert valence.matched_observations == 11
    assert valence.token_weighted_volume_mean == pytest.approx(9 / 11)
    assert valence.work_weighted_volume_mean == pytest.approx((0.875 + 0.25) / 2)
    assert abs(valence.work_minus_token_difference) > 0.25

    unmatched = repository.list_latest_unmatched(project.project_id)
    mystery = next(row for row in unmatched if row.normalized_form == "mystery")
    note_id = repository.upsert_unmatched_note(
        project_id=project.project_id,
        text_id=mystery.text_id,
        lexicon_id=mystery.lexicon_id,
        normalized_form=mystery.normalized_form,
        display_form=mystery.display_form,
        status="needs mapping",
        note="Check historical usage.",
        proposed_mapping="mystery",
    )
    refreshed = next(
        row
        for row in repository.list_latest_unmatched(project.project_id)
        if row.normalized_form == "mystery"
    )
    assert refreshed.note_id == note_id
    assert refreshed.status == "needs mapping"
    assert refreshed.note == "Check historical usage."


def test_corpus_service_runs_each_preserved_work_and_completes_batch(
    tmp_path,
    preprocessor,
) -> None:
    repository = ProjectRepository(tmp_path / "versevad.sqlite3")
    project = repository.create_project("End-to-end corpus")
    repository.import_texts(
        project.project_id,
        (
            CorpusTextImport("First", "first.txt", "first.txt", "Bright blood."),
            CorpusTextImport("Second", "second.txt", "second.txt", "Dark night."),
        ),
    )
    batch = analyze_corpus(
        repository,
        project.project_id,
        lexicon_ids=("nrc_vad_v1",),
        preprocessor=preprocessor,
    )
    assert batch.status == "complete"
    metrics = repository.list_latest_metrics(project.project_id)
    assert {row.title for row in metrics} == {"First", "Second"}
    assert any(row.metric == "vad_mean" and row.weighting == "token" for row in metrics)
    assert {row.analysis_view for row in metrics if row.metric == "vad_mean"} == {
        "all_matched",
        "stopwords_excluded",
    }


def test_project_deletion_requires_exact_title_and_is_scoped(tmp_path) -> None:
    repository = ProjectRepository(tmp_path / "versevad.sqlite3")
    first = repository.create_project("Delete this project")
    second = repository.create_project("Keep this project")
    repository.import_texts(
        first.project_id,
        (CorpusTextImport("First", "first.txt", "first.txt", "Bright."),),
    )
    repository.import_texts(
        second.project_id,
        (CorpusTextImport("Second", "second.txt", "second.txt", "Dark."),),
    )

    with pytest.raises(ValueError, match="exactly match"):
        repository.delete_project(first.project_id, confirmation_title="delete this project")

    repository.delete_project(
        first.project_id,
        confirmation_title="Delete this project",
    )

    assert [project.project_id for project in repository.list_projects()] == [
        second.project_id
    ]
    assert repository.list_texts(second.project_id)[0].title == "Second"
    with pytest.raises(KeyError, match="Unknown project"):
        repository.get_project(first.project_id)
