from __future__ import annotations

import csv
import io
import zipfile

from docx import Document

from versevad.db import CorpusTextRecord, ProjectRecord
from versevad.exports.corpus_csv import build_corpus_export_bundle


def test_corpus_export_contains_csv_data_and_word_report_only() -> None:
    project = ProjectRecord(
        project_id="project-export",
        title="Export Project",
        description="Synthetic export fixture",
        researcher="Researcher",
        created_at="2026-07-25T00:00:00+00:00",
        updated_at="2026-07-25T00:00:00+00:00",
    )
    text = CorpusTextRecord(
        text_id="text-export",
        text_version_id="text-export:v1",
        project_id=project.project_id,
        title="Fixture",
        source_name="fixture.txt",
        relative_path="fixture.txt",
        author="",
        collection="",
        date_label="",
        genre="",
        notes="",
        custom_metadata={},
        original_text="The full text stays in the project database.",
        text_sha256="a" * 64,
        imported_at="2026-07-25T00:00:00+00:00",
        updated_at="2026-07-25T00:00:00+00:00",
    )

    first = build_corpus_export_bundle(project, (text,), (), ())
    second = build_corpus_export_bundle(project, (text,), (), ())

    assert first == second
    with zipfile.ZipFile(io.BytesIO(first)) as archive:
        names = set(archive.namelist())
        assert "corpus_report.docx" in names
        assert "corpus_works.csv" in names
        assert "corpus_methodology.csv" in names
        assert not any(
            name.endswith((".json", ".txt", ".xlsx"))
            for name in names
        )
        rows = list(
            csv.DictReader(
                io.StringIO(
                    archive.read("corpus_works.csv").decode("utf-8-sig")
                )
            )
        )
        assert rows[0]["title"] == "Fixture"
        assert "original_text" not in rows[0]
        report = archive.read("corpus_report.docx")
        assert report.startswith(b"PK")
        document = Document(io.BytesIO(report))
        text_content = "\n".join(
            paragraph.text for paragraph in document.paragraphs
        )
        assert "VerseVAD Corpus Report" in text_content
        assert "Scope and interpretation" in text_content
        assert "Companion data files" in text_content
