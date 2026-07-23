from io import BytesIO

from openpyxl import load_workbook

from versevad.db import (
    CorpusMetricRecord,
    CorpusTextRecord,
    ProjectRecord,
    UnmatchedQcRecord,
)
from versevad.exports.corpus_excel import (
    CORPUS_WORKBOOK_API_VERSION,
    build_corpus_workbook,
)


def test_corpus_excel_is_readable_and_contains_both_collection_views() -> None:
    project = ProjectRecord("project-1", "Jeffers volume", "", "Scholar", "now", "now")
    text = CorpusTextRecord(
        "text-1",
        "version-1",
        project.project_id,
        "Poem",
        "poem.txt",
        "poem.txt",
        "Robinson Jeffers",
        "Volume",
        "1925",
        "lyric",
        "",
        {},
        "Bright.",
        "abc123",
        "now",
        "now",
    )

    def metric(name: str, value: float, *, weighting: str = "token") -> CorpusMetricRecord:
        return CorpusMetricRecord(
            "run-1",
            text.text_id,
            text.text_version_id,
            text.title,
            text.author,
            text.collection,
            text.date_label,
            text.genre,
            "vad-test",
            "VAD test",
            "vad",
            name,
            "valence",
            "",
            weighting,
            "normalized_0_1" if name == "vad_mean" else "midpoint_deviation_sum",
            "1 included matched observation",
            value,
            1,
            1,
            1,
            1.0,
            "now",
        )

    metrics = (
        metric("vad_mean", 0.875),
        metric("vad_mean", 0.875, weighting="type"),
        metric("vad_absolute_midpoint_load", 0.375),
    )
    unmatched = (
        UnmatchedQcRecord(
            project.project_id,
            text.text_id,
            text.title,
            "vad-test",
            "VAD test",
            "mystery",
            "mystery",
            1,
            "NOUN",
            "mystery",
            1,
            "Bright mystery.",
            "needs mapping",
            "Review historical sense.",
            "",
            "note-1",
            "now",
        ),
    )
    content = build_corpus_workbook(project, (text,), metrics, unmatched)
    workbook = load_workbook(BytesIO(content), data_only=False)
    assert workbook.sheetnames == [
        "START HERE",
        "Corpus profiles",
        "Work VAD",
        "Cumulative load",
        "Coverage and emotion",
        "Unmatched QC",
        "Text metadata",
    ]
    assert workbook["START HERE"]["A1"].value == "VerseVAD corpus workbook"
    profile_headers = [cell.value for cell in workbook["Corpus profiles"][4]]
    assert "Token-weighted volume mean" in profile_headers
    assert "Work-weighted volume mean" in profile_headers
    assert workbook["Corpus profiles"]["I5"].value == 0.875
    assert workbook["Corpus profiles"]["B5"].value == "All Matched"
    assert workbook["Corpus profiles"]["I5"].value == 0.875
    assert workbook["Unmatched QC"]["K5"].value == "Review historical sense."
    assert workbook["Text metadata"]["I5"].value == "abc123"

    methodology_content = build_corpus_workbook(
        project,
        (text,),
        metrics,
        unmatched,
        methodology={
            "software_version": "0.5.0.dev0",
            "scenario_id": "scenario-test",
            "phrase_policy": "phrase_preferred",
            "minimum_match_requirement": 1,
            "stopword_policy": {
                "mode": "standard",
                "source": "spaCy English STOP_WORDS",
                "library_version": "3.8.14",
                "list_version": "test-list",
                "active_list_sha256": "abc123",
                "protected_words": ("not", "never"),
                "custom_additions": (),
                "custom_removals": (),
            },
        },
    )
    methodology_workbook = load_workbook(
        BytesIO(methodology_content),
        data_only=False,
    )
    assert CORPUS_WORKBOOK_API_VERSION == 2
    assert methodology_workbook.sheetnames[-1] == "Methodology"
    methodology_rows = {
        row[0].value: row[1].value
        for row in methodology_workbook["Methodology"].iter_rows(min_row=5)
        if row[0].value
    }
    assert methodology_rows["Stopword source"] == "spaCy English STOP_WORDS"
    assert methodology_rows["Protected words"] == "not, never"
