"""Transactional SQLite repository for local projects and corpus results."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Iterator, Mapping

from versevad import __version__
from versevad.application import WorkspaceAnalysis, unmatched_views, vad_cumulative_views


SCHEMA_VERSION = 2
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def default_database_path() -> Path:
    configured = os.environ.get("VERSEVAD_DATABASE_PATH")
    if configured:
        return Path(configured).expanduser()
    return PROJECT_ROOT / "projects" / "versevad.sqlite3"


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


@dataclass(frozen=True)
class ProjectRecord:
    project_id: str
    title: str
    description: str
    researcher: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CorpusTextImport:
    title: str
    source_name: str
    relative_path: str
    original_text: str


@dataclass(frozen=True)
class CorpusTextRecord:
    text_id: str
    text_version_id: str
    project_id: str
    title: str
    source_name: str
    relative_path: str
    author: str
    collection: str
    date_label: str
    genre: str
    notes: str
    custom_metadata: Mapping[str, object]
    original_text: str
    text_sha256: str
    imported_at: str
    updated_at: str


@dataclass(frozen=True)
class CorpusMetricRecord:
    run_id: str
    text_id: str
    text_version_id: str
    title: str
    author: str
    collection: str
    date_label: str
    genre: str
    lexicon_id: str
    lexicon: str
    value_kind: str
    metric: str
    dimension: str
    category: str
    weighting: str
    scale: str
    denominator: str
    value: float | None
    observations: int
    matched_tokens: int
    lexical_tokens: int
    coverage: float | None
    completed_at: str
    analysis_view: str = "all_matched"


@dataclass(frozen=True)
class CorpusBatchRecord:
    batch_id: str
    project_id: str
    status: str
    text_ids: tuple[str, ...]
    lexicon_ids: tuple[str, ...]
    phrase_policy: str
    minimum_match_requirement: int
    stopword_mode: str
    protected_stopwords: tuple[str, ...]
    custom_stopword_additions: tuple[str, ...]
    custom_stopword_removals: tuple[str, ...]
    created_at: str
    completed_at: str | None
    error_message: str


@dataclass(frozen=True)
class UnmatchedQcRecord:
    project_id: str
    text_id: str
    text_title: str
    lexicon_id: str
    lexicon: str
    normalized_form: str
    display_form: str
    frequency: int
    pos: str
    proposed_lemma: str
    example_line: int
    example_context: str
    status: str
    note: str
    proposed_mapping: str
    note_id: str | None
    updated_at: str | None


_MIGRATION_1 = """
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    researcher TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE texts (
    text_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    source_name TEXT NOT NULL,
    relative_path TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    collection_name TEXT NOT NULL DEFAULT '',
    date_label TEXT NOT NULL DEFAULT '',
    genre TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    custom_metadata_json TEXT NOT NULL DEFAULT '{}',
    active_text_version_id TEXT REFERENCES text_versions(text_version_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, relative_path)
);

CREATE TABLE text_versions (
    text_version_id TEXT PRIMARY KEY,
    text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    text_sha256 TEXT NOT NULL,
    source_encoding TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    UNIQUE(text_id, text_sha256)
);

CREATE TABLE corpus_batches (
    batch_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    status TEXT NOT NULL CHECK(status IN ('pending', 'complete', 'failed')),
    text_ids_json TEXT NOT NULL,
    lexicon_ids_json TEXT NOT NULL,
    phrase_policy TEXT NOT NULL,
    minimum_match_requirement INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE analysis_runs (
    run_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    text_version_id TEXT NOT NULL REFERENCES text_versions(text_version_id),
    batch_id TEXT REFERENCES corpus_batches(batch_id),
    status TEXT NOT NULL CHECK(status IN ('complete', 'failed')),
    scenario_id TEXT NOT NULL,
    phrase_policy TEXT NOT NULL,
    minimum_match_requirement INTEGER NOT NULL,
    lexicon_ids_json TEXT NOT NULL,
    software_version TEXT NOT NULL,
    run_signature TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    completed_at TEXT NOT NULL
);

CREATE TABLE analysis_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES analysis_runs(run_id) ON DELETE CASCADE,
    lexicon_id TEXT NOT NULL,
    lexicon_display_name TEXT NOT NULL,
    value_kind TEXT NOT NULL,
    metric TEXT NOT NULL,
    dimension TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    weighting TEXT NOT NULL DEFAULT '',
    scale TEXT NOT NULL DEFAULT '',
    denominator TEXT NOT NULL,
    value REAL,
    observations INTEGER NOT NULL,
    matched_tokens INTEGER NOT NULL,
    lexical_tokens INTEGER NOT NULL,
    coverage REAL
);

CREATE TABLE unmatched_observations (
    observation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL REFERENCES analysis_runs(run_id) ON DELETE CASCADE,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    lexicon_id TEXT NOT NULL,
    lexicon_display_name TEXT NOT NULL,
    normalized_form TEXT NOT NULL,
    display_form TEXT NOT NULL,
    frequency INTEGER NOT NULL,
    pos TEXT NOT NULL,
    proposed_lemma TEXT NOT NULL,
    example_line INTEGER NOT NULL,
    example_context TEXT NOT NULL
);

CREATE TABLE unmatched_notes (
    note_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    text_id TEXT NOT NULL REFERENCES texts(text_id) ON DELETE CASCADE,
    lexicon_id TEXT NOT NULL,
    normalized_form TEXT NOT NULL,
    display_form TEXT NOT NULL,
    status TEXT NOT NULL,
    note TEXT NOT NULL,
    proposed_mapping TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(project_id, text_id, lexicon_id, normalized_form)
);

CREATE INDEX idx_texts_project ON texts(project_id);
CREATE INDEX idx_versions_text ON text_versions(text_id, imported_at);
CREATE INDEX idx_runs_project_text ON analysis_runs(project_id, text_id, completed_at);
CREATE INDEX idx_batches_project ON corpus_batches(project_id, completed_at);
CREATE INDEX idx_metrics_run ON analysis_metrics(run_id);
CREATE INDEX idx_unmatched_run ON unmatched_observations(run_id);
CREATE INDEX idx_notes_lookup ON unmatched_notes(project_id, text_id, lexicon_id, normalized_form);
"""

_MIGRATION_2 = """
ALTER TABLE analysis_metrics
ADD COLUMN analysis_view TEXT NOT NULL DEFAULT 'all_matched';

ALTER TABLE corpus_batches
ADD COLUMN stopword_mode TEXT NOT NULL DEFAULT 'standard';

ALTER TABLE corpus_batches
ADD COLUMN protected_stopwords_json TEXT NOT NULL DEFAULT '[]';

ALTER TABLE corpus_batches
ADD COLUMN custom_stopword_additions_json TEXT NOT NULL DEFAULT '[]';

ALTER TABLE corpus_batches
ADD COLUMN custom_stopword_removals_json TEXT NOT NULL DEFAULT '[]';
"""


class ProjectRepository:
    """Own the local SQLite database and its explicit migrations."""

    def __init__(self, database_path: Path | str | None = None) -> None:
        self.database_path = Path(database_path or default_database_path()).resolve()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            current = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
            ).fetchone()[0]
            if current > SCHEMA_VERSION:
                raise RuntimeError(
                    "This project database was created by a newer VerseVAD version. "
                    "No data was changed."
                )
            if current < 1:
                connection.executescript(_MIGRATION_1)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (1, _now()),
                )
                current = 1
            if current < 2:
                connection.executescript(_MIGRATION_2)
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (2, _now()),
                )

    def schema_version(self) -> int:
        self.initialize()
        with self._connect() as connection:
            return int(
                connection.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
                ).fetchone()[0]
            )

    def create_project(
        self,
        title: str,
        *,
        description: str = "",
        researcher: str = "",
    ) -> ProjectRecord:
        title = title.strip()
        if not title:
            raise ValueError("Enter a project title.")
        self.initialize()
        now = _now()
        project = ProjectRecord(_id("project"), title, description.strip(), researcher.strip(), now, now)
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO projects(project_id, title, description, researcher, created_at, updated_at) "
                "VALUES (:project_id, :title, :description, :researcher, :created_at, :updated_at)",
                asdict(project),
            )
        return project

    @staticmethod
    def _project(row: sqlite3.Row) -> ProjectRecord:
        return ProjectRecord(**dict(row))

    def list_projects(self) -> tuple[ProjectRecord, ...]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT project_id, title, description, researcher, created_at, updated_at "
                "FROM projects ORDER BY updated_at DESC, title COLLATE NOCASE"
            ).fetchall()
        return tuple(self._project(row) for row in rows)

    def get_project(self, project_id: str) -> ProjectRecord:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT project_id, title, description, researcher, created_at, updated_at "
                "FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown project: {project_id}")
        return self._project(row)

    def delete_project(self, project_id: str, *, confirmation_title: str) -> None:
        """Delete exactly one project after an exact, case-sensitive title check."""

        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT title FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Unknown project: {project_id}")
            if confirmation_title != row["title"]:
                raise ValueError(
                    "The confirmation text does not exactly match the project title."
                )
            cursor = connection.execute(
                "DELETE FROM projects WHERE project_id = ?",
                (project_id,),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("VerseVAD could not delete the selected project.")

    @staticmethod
    def _batch(row: sqlite3.Row) -> CorpusBatchRecord:
        values = dict(row)
        values["text_ids"] = tuple(json.loads(values.pop("text_ids_json")))
        values["lexicon_ids"] = tuple(json.loads(values.pop("lexicon_ids_json")))
        values["protected_stopwords"] = tuple(
            json.loads(values.pop("protected_stopwords_json"))
        )
        values["custom_stopword_additions"] = tuple(
            json.loads(values.pop("custom_stopword_additions_json"))
        )
        values["custom_stopword_removals"] = tuple(
            json.loads(values.pop("custom_stopword_removals_json"))
        )
        return CorpusBatchRecord(**values)

    def begin_corpus_batch(
        self,
        project_id: str,
        *,
        text_ids: Iterable[str],
        lexicon_ids: Iterable[str],
        phrase_policy: str,
        minimum_match_requirement: int,
        stopword_mode: str = "standard",
        protected_stopwords: Iterable[str] = (),
        custom_stopword_additions: Iterable[str] = (),
        custom_stopword_removals: Iterable[str] = (),
    ) -> CorpusBatchRecord:
        """Create a pending comparison batch; pending results stay off dashboards."""

        selected_texts = tuple(dict.fromkeys(text_ids))
        selected_lexicons = tuple(dict.fromkeys(lexicon_ids))
        protected = tuple(dict.fromkeys(protected_stopwords))
        additions = tuple(dict.fromkeys(custom_stopword_additions))
        removals = tuple(dict.fromkeys(custom_stopword_removals))
        if not selected_texts:
            raise ValueError("Select at least one corpus text to analyze.")
        if not selected_lexicons:
            raise ValueError("Select at least one lexicon.")
        if minimum_match_requirement < 1:
            raise ValueError("The minimum matched-item setting must be at least 1.")
        self.initialize()
        batch_id = _id("batch")
        now = _now()
        with self._connect() as connection:
            project = connection.execute(
                "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
            ).fetchone()
            if project is None:
                raise KeyError(f"Unknown project: {project_id}")
            placeholders = ",".join("?" for _ in selected_texts)
            found = connection.execute(
                f"SELECT text_id FROM texts WHERE project_id = ? AND text_id IN ({placeholders})",
                (project_id, *selected_texts),
            ).fetchall()
            if {row["text_id"] for row in found} != set(selected_texts):
                raise ValueError("One or more selected texts do not belong to this project.")
            connection.execute(
                """
                INSERT INTO corpus_batches(
                    batch_id, project_id, status, text_ids_json, lexicon_ids_json,
                    phrase_policy, minimum_match_requirement, stopword_mode,
                    protected_stopwords_json, custom_stopword_additions_json,
                    custom_stopword_removals_json, created_at
                ) VALUES (?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    project_id,
                    json.dumps(selected_texts),
                    json.dumps(selected_lexicons),
                    phrase_policy,
                    minimum_match_requirement,
                    stopword_mode,
                    json.dumps(protected),
                    json.dumps(additions),
                    json.dumps(removals),
                    now,
                ),
            )
        return self.get_batch(batch_id)

    def get_batch(self, batch_id: str) -> CorpusBatchRecord:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT batch_id, project_id, status, text_ids_json, lexicon_ids_json,
                       phrase_policy, minimum_match_requirement, stopword_mode,
                       protected_stopwords_json, custom_stopword_additions_json,
                       custom_stopword_removals_json, created_at, completed_at,
                       error_message
                FROM corpus_batches WHERE batch_id = ?
                """,
                (batch_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown corpus batch: {batch_id}")
        return self._batch(row)

    def finish_corpus_batch(
        self,
        batch_id: str,
        *,
        error_message: str | None = None,
    ) -> CorpusBatchRecord:
        self.initialize()
        now = _now()
        status = "failed" if error_message else "complete"
        with self._connect() as connection:
            batch = connection.execute(
                "SELECT project_id, status, text_ids_json FROM corpus_batches WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()
            if batch is None:
                raise KeyError(f"Unknown corpus batch: {batch_id}")
            if batch["status"] != "pending":
                raise ValueError("This corpus batch is already immutable and cannot be changed.")
            if status == "complete":
                expected = len(json.loads(batch["text_ids_json"]))
                actual = connection.execute(
                    "SELECT COUNT(DISTINCT text_id) FROM analysis_runs WHERE batch_id = ? AND status = 'complete'",
                    (batch_id,),
                ).fetchone()[0]
                if actual != expected:
                    raise ValueError(
                        "The corpus batch does not contain one completed run per selected text."
                    )
            connection.execute(
                """
                UPDATE corpus_batches
                SET status = ?, completed_at = ?, error_message = ?
                WHERE batch_id = ?
                """,
                (status, now, (error_message or "").strip(), batch_id),
            )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?",
                (now, batch["project_id"]),
            )
        return self.get_batch(batch_id)

    def import_texts(
        self,
        project_id: str,
        items: Iterable[CorpusTextImport],
    ) -> tuple[CorpusTextRecord, ...]:
        self.initialize()
        imported = tuple(items)
        if not imported:
            raise ValueError("Choose a folder containing at least one UTF-8 .txt file.")
        now = _now()
        with self._connect() as connection:
            if connection.execute(
                "SELECT 1 FROM projects WHERE project_id = ?", (project_id,)
            ).fetchone() is None:
                raise KeyError(f"Unknown project: {project_id}")
            for item in imported:
                title = item.title.strip()
                if not title or not item.original_text.strip():
                    raise ValueError("Every imported text needs a title and nonblank content.")
                relative_path = item.relative_path.replace("\\", "/").lstrip("/")
                if not relative_path or ".." in Path(relative_path).parts:
                    raise ValueError("A corpus filename contained an unsafe relative path.")
                row = connection.execute(
                    "SELECT text_id FROM texts WHERE project_id = ? AND relative_path = ?",
                    (project_id, relative_path),
                ).fetchone()
                text_id = row["text_id"] if row else _id("text")
                if row is None:
                    connection.execute(
                        "INSERT INTO texts(text_id, project_id, title, source_name, relative_path, "
                        "created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (text_id, project_id, title, item.source_name, relative_path, now, now),
                    )
                else:
                    connection.execute(
                        "UPDATE texts SET title = ?, source_name = ?, updated_at = ? WHERE text_id = ?",
                        (title, item.source_name, now, text_id),
                    )
                digest = hashlib.sha256(item.original_text.encode("utf-8")).hexdigest()
                version = connection.execute(
                    "SELECT text_version_id FROM text_versions WHERE text_id = ? AND text_sha256 = ?",
                    (text_id, digest),
                ).fetchone()
                text_version_id = version["text_version_id"] if version else _id("version")
                if version is None:
                    connection.execute(
                        "INSERT INTO text_versions(text_version_id, text_id, original_text, text_sha256, "
                        "source_encoding, imported_at) VALUES (?, ?, ?, ?, 'utf-8', ?)",
                        (text_version_id, text_id, item.original_text, digest, now),
                    )
                connection.execute(
                    "UPDATE texts SET active_text_version_id = ?, updated_at = ? WHERE text_id = ?",
                    (text_version_id, now, text_id),
                )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?", (now, project_id)
            )
        return self.list_texts(project_id)

    @staticmethod
    def _text(row: sqlite3.Row) -> CorpusTextRecord:
        values = dict(row)
        values["custom_metadata"] = json.loads(values.pop("custom_metadata_json"))
        return CorpusTextRecord(**values)

    def list_texts(self, project_id: str) -> tuple[CorpusTextRecord, ...]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT t.text_id, v.text_version_id, t.project_id, t.title, t.source_name,
                       t.relative_path, t.author, t.collection_name AS collection,
                       t.date_label, t.genre, t.notes, t.custom_metadata_json,
                       v.original_text, v.text_sha256, v.imported_at, t.updated_at
                FROM texts t
                JOIN text_versions v ON v.text_version_id = t.active_text_version_id
                WHERE t.project_id = ?
                ORDER BY t.title COLLATE NOCASE, t.relative_path COLLATE NOCASE
                """,
                (project_id,),
            ).fetchall()
        return tuple(self._text(row) for row in rows)

    def get_text(self, text_id: str) -> CorpusTextRecord:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT t.text_id, v.text_version_id, t.project_id, t.title, t.source_name,
                       t.relative_path, t.author, t.collection_name AS collection,
                       t.date_label, t.genre, t.notes, t.custom_metadata_json,
                       v.original_text, v.text_sha256, v.imported_at, t.updated_at
                FROM texts t
                JOIN text_versions v ON v.text_version_id = t.active_text_version_id
                WHERE t.text_id = ?
                """,
                (text_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Unknown text: {text_id}")
        return self._text(row)

    def update_text_metadata(
        self,
        text_id: str,
        *,
        title: str,
        author: str = "",
        collection: str = "",
        date_label: str = "",
        genre: str = "",
        notes: str = "",
        custom_metadata: Mapping[str, object] | None = None,
    ) -> CorpusTextRecord:
        if not title.strip():
            raise ValueError("A corpus text title cannot be blank.")
        self.initialize()
        now = _now()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE texts SET title = ?, author = ?, collection_name = ?, date_label = ?,
                    genre = ?, notes = ?, custom_metadata_json = ?, updated_at = ?
                WHERE text_id = ?
                """,
                (
                    title.strip(),
                    author.strip(),
                    collection.strip(),
                    date_label.strip(),
                    genre.strip(),
                    notes.strip(),
                    json.dumps(dict(custom_metadata or {}), ensure_ascii=False, sort_keys=True),
                    now,
                    text_id,
                ),
            )
            if cursor.rowcount != 1:
                raise KeyError(f"Unknown text: {text_id}")
            project_id = connection.execute(
                "SELECT project_id FROM texts WHERE text_id = ?", (text_id,)
            ).fetchone()[0]
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?", (now, project_id)
            )
        return self.get_text(text_id)

    @staticmethod
    def _manifest(workspace: WorkspaceAnalysis) -> dict[str, object]:
        stopword_policy = next(
            (
                result.stopword_policy
                for result in workspace.results
                if result.stopword_policy is not None
            ),
            None,
        )
        return {
            "software_version": __version__,
            "text_version_id": workspace.document.text_version_id,
            "text_sha256": workspace.document.text_sha256,
            "scenario_id": workspace.comparison.scenario_id,
            "phrase_policy": workspace.request.phrase_policy.value,
            "minimum_match_requirement": workspace.request.minimum_match_requirement,
            "stopword_policy": (
                {
                    "mode": stopword_policy.mode.value,
                    "source": stopword_policy.source,
                    "library_version": stopword_policy.library_version,
                    "list_version": stopword_policy.list_version,
                    "standard_word_count": stopword_policy.standard_word_count,
                    "standard_list_sha256": stopword_policy.standard_list_sha256,
                    "active_words": stopword_policy.active_words,
                    "active_list_sha256": stopword_policy.active_list_sha256,
                    "protected_words": stopword_policy.protected_words,
                    "custom_additions": stopword_policy.custom_additions,
                    "custom_removals": stopword_policy.custom_removals,
                }
                if stopword_policy is not None
                else None
            ),
            "lexicons": [
                {
                    "lexicon_id": result.lexicon_metadata.lexicon_id,
                    "source_sha256": result.lexicon_validation.source_sha256,
                    "adapter_version": result.lexicon_metadata.adapter_version,
                    "source_scale_min": result.lexicon_metadata.source_scale_min,
                    "source_scale_max": result.lexicon_metadata.source_scale_max,
                    "normalization_formula": result.lexicon_metadata.normalization_formula,
                }
                for result in workspace.results
            ],
        }

    @staticmethod
    def _metric_rows(workspace: WorkspaceAnalysis) -> list[tuple]:
        rows = []
        view_key = {
            "All matched tokens": "all_matched",
            "Stopwords excluded": "stopwords_excluded",
        }
        cumulative = {
            (row.lexicon_id, view_key[row.analysis_view], row.dimension): row
            for row in vad_cumulative_views(workspace)
        }
        for result in workspace.results:
            metadata = result.lexicon_metadata
            common = (
                metadata.lexicon_id,
                metadata.display_name,
                metadata.value_kind.value,
            )
            all_coverage = result.coverage.lexical_token_coverage
            all_denominator = f"{result.coverage.total_lexical_tokens} lexical tokens"
            rows.append(
                (
                    *common,
                    "all_matched",
                    "coverage",
                    "",
                    "",
                    "token",
                    "proportion",
                    all_denominator,
                    all_coverage,
                    result.coverage.matched_token_count,
                    result.coverage.matched_token_count,
                    result.coverage.total_lexical_tokens,
                    all_coverage,
                )
            )
            if result.stopword_coverage is not None:
                filtered_coverage = result.stopword_coverage.lexical_token_coverage
                rows.append(
                    (
                        *common,
                        "stopwords_excluded",
                        "coverage",
                        "",
                        "",
                        "token",
                        "proportion",
                        (
                            f"{result.stopword_coverage.eligible_token_count} "
                            "eligible non-stopword tokens"
                        ),
                        filtered_coverage,
                        result.stopword_coverage.matched_token_count,
                        result.stopword_coverage.matched_token_count,
                        result.stopword_coverage.eligible_token_count,
                        filtered_coverage,
                    )
                )
            if result.vad_summary is not None:
                summary = result.vad_summary
                groups = (
                    (
                        "all_matched",
                        "token",
                        "normalized_0_1",
                        summary.token_weighted_normalized,
                        result.coverage.matched_token_count,
                        result.coverage.total_lexical_tokens,
                        all_coverage,
                    ),
                    (
                        "all_matched",
                        "type",
                        "normalized_0_1",
                        summary.type_weighted_normalized,
                        result.coverage.matched_token_count,
                        result.coverage.total_lexical_tokens,
                        all_coverage,
                    ),
                    (
                        "all_matched",
                        "token",
                        "source",
                        summary.token_weighted_original,
                        result.coverage.matched_token_count,
                        result.coverage.total_lexical_tokens,
                        all_coverage,
                    ),
                    (
                        "all_matched",
                        "type",
                        "source",
                        summary.type_weighted_original,
                        result.coverage.matched_token_count,
                        result.coverage.total_lexical_tokens,
                        all_coverage,
                    ),
                )
                filtered_groups = ()
                if result.stopword_coverage is not None:
                    filtered_groups = (
                        (
                            "stopwords_excluded",
                            "token",
                            "normalized_0_1",
                            summary.stopword_excluded_token_weighted_normalized,
                            result.stopword_coverage.matched_token_count,
                            result.stopword_coverage.eligible_token_count,
                            result.stopword_coverage.lexical_token_coverage,
                        ),
                        (
                            "stopwords_excluded",
                            "type",
                            "normalized_0_1",
                            summary.stopword_excluded_type_weighted_normalized,
                            result.stopword_coverage.matched_token_count,
                            result.stopword_coverage.eligible_token_count,
                            result.stopword_coverage.lexical_token_coverage,
                        ),
                        (
                            "stopwords_excluded",
                            "token",
                            "source",
                            summary.stopword_excluded_token_weighted_original,
                            result.stopword_coverage.matched_token_count,
                            result.stopword_coverage.eligible_token_count,
                            result.stopword_coverage.lexical_token_coverage,
                        ),
                        (
                            "stopwords_excluded",
                            "type",
                            "source",
                            summary.stopword_excluded_type_weighted_original,
                            result.stopword_coverage.matched_token_count,
                            result.stopword_coverage.eligible_token_count,
                            result.stopword_coverage.lexical_token_coverage,
                        ),
                    )
                for (
                    analysis_view,
                    weighting,
                    scale,
                    statistics,
                    matched_tokens,
                    lexical_tokens,
                    coverage,
                ) in (*groups, *filtered_groups):
                    if statistics is None:
                        continue
                    for dimension, values in statistics.by_dimension().items():
                        rows.append(
                            (
                                *common,
                                analysis_view,
                                "vad_mean",
                                dimension,
                                "",
                                weighting,
                                scale,
                                f"{values.count} included matched observations",
                                values.mean,
                                values.count,
                                matched_tokens,
                                lexical_tokens,
                                coverage,
                            )
                        )
                        rows.append(
                            (
                                *common,
                                analysis_view,
                                "vad_standard_deviation",
                                dimension,
                                "",
                                weighting,
                                scale,
                                f"{values.count} included matched observations",
                                values.population_standard_deviation,
                                values.count,
                                matched_tokens,
                                lexical_tokens,
                                coverage,
                            )
                        )
                for analysis_view in ("all_matched", "stopwords_excluded"):
                    for dimension in ("valence", "arousal", "dominance"):
                        totals = cumulative.get(
                            (metadata.lexicon_id, analysis_view, dimension)
                        )
                        if totals is None:
                            continue
                        cumulative_values = (
                            ("vad_rating_total", "normalized_0_1_sum", totals.rating_total),
                            (
                                "vad_above_midpoint_load",
                                "midpoint_deviation_sum",
                                totals.above_midpoint_deviation,
                            ),
                            (
                                "vad_below_midpoint_load",
                                "midpoint_deviation_sum",
                                totals.below_midpoint_deviation,
                            ),
                            (
                                "vad_net_midpoint_load",
                                "midpoint_deviation_sum",
                                totals.net_midpoint_deviation,
                            ),
                            (
                                "vad_absolute_midpoint_load",
                                "midpoint_deviation_sum",
                                totals.absolute_midpoint_deviation,
                            ),
                        )
                        matched_tokens = (
                            result.coverage.matched_token_count
                            if analysis_view == "all_matched"
                            else result.stopword_coverage.matched_token_count
                        )
                        for metric, scale, value in cumulative_values:
                            rows.append(
                                (
                                    *common,
                                    analysis_view,
                                    metric,
                                    dimension,
                                    "",
                                    "token",
                                    scale,
                                    (
                                        f"{totals.matched_observations} included "
                                        "matched observations"
                                    ),
                                    value,
                                    totals.matched_observations,
                                    matched_tokens,
                                    totals.lexical_tokens,
                                    totals.lexical_coverage,
                                )
                            )
            for statistics in result.category_statistics:
                rows.append(
                    (
                        *common,
                        "all_matched",
                        "association_rate",
                        "",
                        statistics.category,
                        "token",
                        "proportion",
                        all_denominator,
                        statistics.proportion_of_lexical_tokens,
                        statistics.associated_token_count,
                        result.coverage.matched_token_count,
                        result.coverage.total_lexical_tokens,
                        all_coverage,
                    )
                )
            for statistics in result.intensity_statistics:
                rows.extend(
                    (
                        (
                            *common,
                            "all_matched",
                            "intensity_prevalence",
                            "",
                            statistics.category,
                            "token",
                            "proportion",
                            all_denominator,
                            statistics.prevalence_among_lexical_tokens,
                            statistics.matched_token_occurrences,
                            result.coverage.matched_token_count,
                            result.coverage.total_lexical_tokens,
                            all_coverage,
                        ),
                        (
                            *common,
                            "all_matched",
                            "intensity_mean",
                            "",
                            statistics.category,
                            "token",
                            "source_0_1",
                            (
                                f"{statistics.matched_token_occurrences} supplied "
                                "matched pairs"
                            ),
                            statistics.token_weighted.mean,
                            statistics.matched_token_occurrences,
                            result.coverage.matched_token_count,
                            result.coverage.total_lexical_tokens,
                            all_coverage,
                        ),
                    )
                )
        return rows

    def save_analysis(
        self,
        project_id: str,
        text_id: str,
        workspace: WorkspaceAnalysis,
        *,
        batch_id: str | None = None,
    ) -> str:
        """Atomically persist a completed immutable corpus analysis."""

        self.initialize()
        text = self.get_text(text_id)
        if text.project_id != project_id:
            raise ValueError("The selected text does not belong to this project.")
        if text.text_sha256 != workspace.document.text_sha256:
            raise ValueError("The analysis does not match the active preserved text version.")
        if workspace.document.text_id != text.text_id:
            raise ValueError("The analysis text identity does not match the selected corpus text.")
        if workspace.document.text_version_id != text.text_version_id:
            raise ValueError("The analysis does not identify the active preserved text version.")
        run_id = _id("run")
        now = _now()
        manifest = self._manifest(workspace)
        signature_source = json.dumps(manifest, sort_keys=True, ensure_ascii=False)
        signature = hashlib.sha256(signature_source.encode("utf-8")).hexdigest()
        metric_rows = self._metric_rows(workspace)
        unmatched = unmatched_views(workspace)
        with self._connect() as connection:
            if batch_id is not None:
                batch = connection.execute(
                    "SELECT project_id, status FROM corpus_batches WHERE batch_id = ?",
                    (batch_id,),
                ).fetchone()
                if batch is None or batch["project_id"] != project_id:
                    raise ValueError("The corpus batch does not belong to this project.")
                if batch["status"] != "pending":
                    raise ValueError("The corpus batch is no longer accepting results.")
            connection.execute(
                """
                INSERT INTO analysis_runs(
                    run_id, project_id, text_id, text_version_id, batch_id, status, scenario_id,
                    phrase_policy, minimum_match_requirement, lexicon_ids_json,
                    software_version, run_signature, manifest_json, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, 'complete', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    project_id,
                    text_id,
                    text.text_version_id,
                    batch_id,
                    workspace.comparison.scenario_id,
                    workspace.request.phrase_policy.value,
                    workspace.request.minimum_match_requirement,
                    json.dumps(workspace.request.lexicon_ids),
                    __version__,
                    signature,
                    json.dumps(manifest, ensure_ascii=False, sort_keys=True),
                    now,
                    now,
                ),
            )
            connection.executemany(
                """
                INSERT INTO analysis_metrics(
                    run_id, lexicon_id, lexicon_display_name, value_kind, analysis_view, metric,
                    dimension, category, weighting, scale, denominator, value,
                    observations, matched_tokens, lexical_tokens, coverage
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [(run_id, *row) for row in metric_rows],
            )
            connection.executemany(
                """
                INSERT INTO unmatched_observations(
                    run_id, project_id, text_id, lexicon_id, lexicon_display_name,
                    normalized_form, display_form, frequency, pos, proposed_lemma,
                    example_line, example_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        project_id,
                        text_id,
                        row.lexicon_id,
                        row.lexicon,
                        row.normalized_form,
                        row.surface,
                        row.frequency,
                        row.pos,
                        row.proposed_lemma,
                        row.example_line,
                        row.example_context,
                    )
                    for row in unmatched
                ],
            )
            connection.execute(
                "UPDATE projects SET updated_at = ? WHERE project_id = ?", (now, project_id)
            )
        return run_id

    @staticmethod
    def _visible_run_ids(
        connection: sqlite3.Connection,
        project_id: str,
    ) -> tuple[str, ...]:
        """Return one internally consistent completed batch when available."""

        batch = connection.execute(
            """
            SELECT batch_id FROM corpus_batches
            WHERE project_id = ? AND status = 'complete'
            ORDER BY completed_at DESC, rowid DESC LIMIT 1
            """,
            (project_id,),
        ).fetchone()
        if batch is not None:
            rows = connection.execute(
                """
                SELECT run_id FROM analysis_runs
                WHERE batch_id = ? AND status = 'complete'
                ORDER BY text_id, completed_at
                """,
                (batch["batch_id"],),
            ).fetchall()
            return tuple(row["run_id"] for row in rows)
        rows = connection.execute(
            """
            WITH ranked AS (
                SELECT run_id, ROW_NUMBER() OVER (
                    PARTITION BY text_id ORDER BY completed_at DESC, rowid DESC
                ) AS rank_number
                FROM analysis_runs
                WHERE project_id = ? AND status = 'complete' AND batch_id IS NULL
            )
            SELECT run_id FROM ranked WHERE rank_number = 1
            """,
            (project_id,),
        ).fetchall()
        return tuple(row["run_id"] for row in rows)

    def list_latest_metrics(self, project_id: str) -> tuple[CorpusMetricRecord, ...]:
        self.initialize()
        with self._connect() as connection:
            run_ids = self._visible_run_ids(connection, project_id)
            if not run_ids:
                return ()
            placeholders = ",".join("?" for _ in run_ids)
            rows = connection.execute(
                f"""
                SELECT r.run_id, r.text_id, r.text_version_id, t.title, t.author,
                       t.collection_name AS collection, t.date_label, t.genre,
                       m.lexicon_id, m.lexicon_display_name AS lexicon, m.value_kind,
                       m.analysis_view, m.metric, m.dimension, m.category, m.weighting, m.scale,
                       m.denominator, m.value, m.observations, m.matched_tokens, m.lexical_tokens,
                       m.coverage, r.completed_at
                FROM analysis_runs r
                JOIN analysis_metrics m ON m.run_id = r.run_id
                JOIN texts t ON t.text_id = r.text_id
                WHERE r.run_id IN ({placeholders})
                ORDER BY t.title COLLATE NOCASE, m.lexicon_display_name, m.metric,
                         m.dimension, m.category, m.weighting, m.scale
                """,
                run_ids,
            ).fetchall()
        return tuple(CorpusMetricRecord(**dict(row)) for row in rows)

    def latest_methodology(self, project_id: str) -> Mapping[str, object]:
        """Return one recorded manifest from the latest visible complete batch."""

        self.initialize()
        with self._connect() as connection:
            run_ids = self._visible_run_ids(connection, project_id)
            if not run_ids:
                return {}
            row = connection.execute(
                "SELECT manifest_json FROM analysis_runs WHERE run_id = ?",
                (run_ids[0],),
            ).fetchone()
        return json.loads(row["manifest_json"]) if row is not None else {}

    def upsert_unmatched_note(
        self,
        *,
        project_id: str,
        text_id: str,
        lexicon_id: str,
        normalized_form: str,
        display_form: str,
        status: str,
        note: str,
        proposed_mapping: str = "",
    ) -> str:
        allowed = {"unreviewed", "reviewed", "needs mapping", "accepted gap"}
        if status not in allowed:
            raise ValueError(f"Unknown quality-control status: {status}")
        normalized_form = normalized_form.strip()
        if not normalized_form:
            raise ValueError("An unmatched note needs a word or normalized form.")
        self.initialize()
        now = _now()
        with self._connect() as connection:
            owner = connection.execute(
                "SELECT project_id FROM texts WHERE text_id = ?", (text_id,)
            ).fetchone()
            if owner is None or owner["project_id"] != project_id:
                raise ValueError("The unmatched item does not belong to this project.")
            existing = connection.execute(
                """
                SELECT note_id, created_at FROM unmatched_notes
                WHERE project_id = ? AND text_id = ? AND lexicon_id = ? AND normalized_form = ?
                """,
                (project_id, text_id, lexicon_id, normalized_form),
            ).fetchone()
            note_id = existing["note_id"] if existing else _id("note")
            created_at = existing["created_at"] if existing else now
            connection.execute(
                """
                INSERT INTO unmatched_notes(
                    note_id, project_id, text_id, lexicon_id, normalized_form,
                    display_form, status, note, proposed_mapping, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(project_id, text_id, lexicon_id, normalized_form)
                DO UPDATE SET display_form = excluded.display_form,
                              status = excluded.status,
                              note = excluded.note,
                              proposed_mapping = excluded.proposed_mapping,
                              updated_at = excluded.updated_at
                """,
                (
                    note_id,
                    project_id,
                    text_id,
                    lexicon_id,
                    normalized_form,
                    display_form,
                    status,
                    note.strip(),
                    proposed_mapping.strip(),
                    created_at,
                    now,
                ),
            )
        return note_id

    def list_latest_unmatched(self, project_id: str) -> tuple[UnmatchedQcRecord, ...]:
        self.initialize()
        with self._connect() as connection:
            run_ids = self._visible_run_ids(connection, project_id)
            if not run_ids:
                return ()
            placeholders = ",".join("?" for _ in run_ids)
            rows = connection.execute(
                f"""
                SELECT o.project_id, o.text_id, t.title AS text_title, o.lexicon_id,
                       o.lexicon_display_name AS lexicon, o.normalized_form,
                       o.display_form, o.frequency, o.pos, o.proposed_lemma,
                       o.example_line, o.example_context,
                       COALESCE(n.status, 'unreviewed') AS status,
                       COALESCE(n.note, '') AS note,
                       COALESCE(n.proposed_mapping, '') AS proposed_mapping,
                       n.note_id, n.updated_at
                FROM unmatched_observations o
                JOIN texts t ON t.text_id = o.text_id
                LEFT JOIN unmatched_notes n
                  ON n.project_id = o.project_id AND n.text_id = o.text_id
                 AND n.lexicon_id = o.lexicon_id
                 AND n.normalized_form = o.normalized_form
                WHERE o.run_id IN ({placeholders})
                ORDER BY t.title COLLATE NOCASE, o.lexicon_display_name,
                         o.frequency DESC, o.display_form COLLATE NOCASE
                """,
                run_ids,
            ).fetchall()
        return tuple(UnmatchedQcRecord(**dict(row)) for row in rows)
