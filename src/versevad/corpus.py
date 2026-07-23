"""Framework-independent corpus import, analysis, and collection summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Iterable, Sequence

from versevad.application import (
    AnalysisRequest,
    TextImportError,
    decode_uploaded_text,
    run_workspace_analysis,
)
from versevad.db import (
    CorpusBatchRecord,
    CorpusMetricRecord,
    CorpusTextImport,
    ProjectRepository,
)
from versevad.models import PhrasePolicy, StopwordMode
from versevad.preprocessing import SpacyEnglishPreprocessor, TextPreprocessor
from versevad.stopwords import DEFAULT_PROTECTED_WORDS


MAX_CORPUS_FILES = 5_000
MAX_CORPUS_BYTES = 250 * 1024 * 1024


@dataclass(frozen=True)
class CorpusImportSummary:
    files: tuple[CorpusTextImport, ...]
    total_bytes: int


@dataclass(frozen=True)
class CorpusVadProfile:
    """Two defensible collection means kept side by side."""

    lexicon_id: str
    lexicon: str
    analysis_view: str
    dimension: str
    works_included: int
    works_omitted: int
    matched_observations: int
    lexical_tokens: int
    token_weighted_volume_mean: float
    work_weighted_volume_mean: float
    work_minus_token_difference: float
    volume_coverage: float | None


def decode_corpus_files(
    files: Iterable[tuple[str, bytes]],
) -> CorpusImportSummary:
    """Validate a browser-selected folder and preserve every UTF-8 text separately."""

    supplied = tuple(files)
    if not supplied:
        raise TextImportError("Choose a folder containing at least one UTF-8 .txt file.")
    if len(supplied) > MAX_CORPUS_FILES:
        raise TextImportError(
            f"This folder contains more than {MAX_CORPUS_FILES:,} text files. "
            "Split it into smaller research projects before importing."
        )
    total_bytes = sum(len(content) for _, content in supplied)
    if total_bytes > MAX_CORPUS_BYTES:
        raise TextImportError(
            "This folder is larger than VerseVAD's 250 MB import safety limit. "
            "Split it into smaller research projects before importing."
        )
    imported: list[CorpusTextImport] = []
    seen_paths: set[str] = set()
    for raw_name, content in supplied:
        relative_path = raw_name.replace("\\", "/").lstrip("/")
        path = PurePosixPath(relative_path)
        if not relative_path or ".." in path.parts:
            raise TextImportError("A selected filename contained an unsafe relative path.")
        if path.suffix.casefold() != ".txt":
            raise TextImportError(
                f"{relative_path} is not a .txt file. Only UTF-8 plain text is imported."
            )
        key = relative_path.casefold()
        if key in seen_paths:
            raise TextImportError(f"The selected folder contains a duplicate path: {relative_path}")
        seen_paths.add(key)
        try:
            original_text = decode_uploaded_text(path.name, content)
        except TextImportError as error:
            raise TextImportError(f"{relative_path}: {error}") from error
        if not original_text.strip():
            raise TextImportError(f"{relative_path} is blank, so the folder was not imported.")
        imported.append(
            CorpusTextImport(
                title=path.stem,
                source_name=path.name,
                relative_path=relative_path,
                original_text=original_text,
            )
        )
    imported.sort(key=lambda item: item.relative_path.casefold())
    return CorpusImportSummary(tuple(imported), total_bytes)


def corpus_vad_profiles(
    metrics: Sequence[CorpusMetricRecord],
    *,
    total_works: int | None = None,
) -> tuple[CorpusVadProfile, ...]:
    """Compute token- and work-weighted collection VAD profiles.

    Token-weighted collection means reconstruct a pooled matched-observation mean.
    Work-weighted means average the eligible poem-level token means. Missing poem
    scores stay missing and are reported as omitted, never changed to 0.5 or zero.
    """

    selected = tuple(
        row
        for row in metrics
        if row.metric == "vad_mean"
        and row.weighting == "token"
        and row.scale == "normalized_0_1"
        and row.value is not None
        and row.observations > 0
    )
    if total_works is None:
        total_works = len({row.text_id for row in metrics})
    grouped: dict[tuple[str, str, str, str], list[CorpusMetricRecord]] = {}
    for row in selected:
        grouped.setdefault(
            (row.lexicon_id, row.lexicon, row.analysis_view, row.dimension),
            [],
        ).append(row)
    profiles = []
    for (lexicon_id, lexicon, analysis_view, dimension), rows in grouped.items():
        observations = sum(row.observations for row in rows)
        work_mean = sum(float(row.value) for row in rows) / len(rows)
        token_mean = (
            sum(float(row.value) * row.observations for row in rows) / observations
        )
        lexical_tokens = sum(row.lexical_tokens for row in rows)
        matched_tokens = sum(row.matched_tokens for row in rows)
        coverage = matched_tokens / lexical_tokens if lexical_tokens else None
        profiles.append(
            CorpusVadProfile(
                lexicon_id=lexicon_id,
                lexicon=lexicon,
                analysis_view=analysis_view,
                dimension=dimension,
                works_included=len(rows),
                works_omitted=max(total_works - len(rows), 0),
                matched_observations=observations,
                lexical_tokens=lexical_tokens,
                token_weighted_volume_mean=token_mean,
                work_weighted_volume_mean=work_mean,
                work_minus_token_difference=work_mean - token_mean,
                volume_coverage=coverage,
            )
        )
    return tuple(
        sorted(
            profiles,
            key=lambda row: (
                row.lexicon.casefold(),
                row.analysis_view,
                row.dimension,
            ),
        )
    )


def analyze_corpus(
    repository: ProjectRepository,
    project_id: str,
    *,
    lexicon_ids: Sequence[str],
    text_ids: Sequence[str] | None = None,
    phrase_policy: PhrasePolicy = PhrasePolicy.PHRASE_PREFERRED,
    minimum_match_requirement: int = 3,
    stopword_mode: StopwordMode = StopwordMode.STANDARD,
    protected_stopwords: Sequence[str] = DEFAULT_PROTECTED_WORDS,
    custom_stopword_additions: Sequence[str] = (),
    custom_stopword_removals: Sequence[str] = (),
    preprocessor: TextPreprocessor | None = None,
    progress: Callable[[int, int, str], None] | None = None,
) -> CorpusBatchRecord:
    """Analyze each work independently and publish comparisons only as a full batch."""

    project = repository.get_project(project_id)
    available = repository.list_texts(project_id)
    selected_ids = tuple(text_ids) if text_ids is not None else tuple(
        text.text_id for text in available
    )
    selected_set = set(selected_ids)
    selected = tuple(text for text in available if text.text_id in selected_set)
    if len(selected) != len(selected_set):
        raise ValueError("One or more selected texts do not belong to this project.")
    batch = repository.begin_corpus_batch(
        project_id,
        text_ids=(text.text_id for text in selected),
        lexicon_ids=lexicon_ids,
        phrase_policy=phrase_policy.value,
        minimum_match_requirement=minimum_match_requirement,
        stopword_mode=stopword_mode.value,
        protected_stopwords=protected_stopwords,
        custom_stopword_additions=custom_stopword_additions,
        custom_stopword_removals=custom_stopword_removals,
    )
    processor = preprocessor or SpacyEnglishPreprocessor()
    total = len(selected)
    try:
        for position, text in enumerate(selected, start=1):
            if progress is not None:
                progress(position - 1, total, text.title)
            workspace = run_workspace_analysis(
                AnalysisRequest(
                    project_name=project.title,
                    title=text.title,
                    original_text=text.original_text,
                    lexicon_ids=tuple(lexicon_ids),
                    phrase_policy=phrase_policy,
                    minimum_match_requirement=minimum_match_requirement,
                    text_id=text.text_id,
                    text_version_id=text.text_version_id,
                    stopword_mode=stopword_mode,
                    protected_stopwords=tuple(protected_stopwords),
                    custom_stopword_additions=tuple(custom_stopword_additions),
                    custom_stopword_removals=tuple(custom_stopword_removals),
                ),
                preprocessor=processor,
            )
            repository.save_analysis(
                project_id,
                text.text_id,
                workspace,
                batch_id=batch.batch_id,
            )
            if progress is not None:
                progress(position, total, text.title)
    except Exception as error:
        repository.finish_corpus_batch(batch.batch_id, error_message=str(error))
        raise
    return repository.finish_corpus_batch(batch.batch_id)
