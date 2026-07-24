from __future__ import annotations

import io
import zipfile

from versevad.corpus import (
    CorpusAnalysisConfiguration,
    analyze_corpus,
    corpus_module_category_profiles,
)
from versevad.db import CorpusTextImport, ProjectRepository
from versevad.poetry_id import PoetryIDConfiguration


def test_poetry_id_corpus_reuses_modules_and_keeps_compatible_distributions(
    tmp_path,
    preprocessor,
) -> None:
    repository = ProjectRepository(tmp_path / "versevad.sqlite3")
    project = repository.create_project("PoetryID corpus")
    texts = repository.import_texts(
        project.project_id,
        (
            CorpusTextImport(
                "First",
                "first.txt",
                "first.txt",
                "joy love peace light happy calm strong",
            ),
            CorpusTextImport(
                "Second",
                "second.txt",
                "second.txt",
                "fear dark pain grief weak loss cold",
            ),
        ),
    )

    batch = analyze_corpus(
        repository,
        project.project_id,
        lexicon_ids=("nrc_vad_v1",),
        text_ids=tuple(row.text_id for row in texts),
        module_configuration=CorpusAnalysisConfiguration(
            include_poetry_id=True,
            poetry_id_configuration=PoetryIDConfiguration(
                vad_lexicon_ids=("nrc_vad_v1",),
            ),
        ),
        preprocessor=preprocessor,
    )

    assert batch.status == "complete"
    assert batch.module_names == ("poetry_id",)
    results = repository.list_module_results_for_batch(
        project.project_id,
        batch.batch_id,
    )
    assert len(results) == 2
    assert {row.module_name for row in results} == {"poetry_id"}

    metrics = repository.list_module_metrics_for_batch(
        project.project_id,
        batch.batch_id,
    )
    categories = corpus_module_category_profiles(metrics)
    archetype_rows = [
        row
        for row in categories
        if row.metric_id == "poetry_id.categorical_archetype_id"
    ]
    assert {row.weighting for row in archetype_rows} == {"token", "type"}
    assert {row.scope_id for row in archetype_rows} == {
        "nrc_vad_v1:all_matched"
    }

    archive = repository.build_module_artifact_zip(
        results[0].run_id,
        "poetry_id",
    )
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = {
            name for name in bundle.namelist() if name.startswith("poetry_id_")
        }
        assert "poetry_id_summary.csv" in names
        assert "poetry_id_report.txt" in names
        assert not any(name.endswith(".json") for name in names)
