"""Auditable CSV exports for Phase 1 analysis results."""

from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Mapping

from versevad import __version__
from versevad.models import AnalysisResult


TOKEN_AUDIT_FIELDS = [
    "analysis_id",
    "scenario_id",
    "text_id",
    "text_version_id",
    "token_id",
    "section_number",
    "stanza_number",
    "line_number",
    "token_position",
    "sentence_number",
    "token_position_in_sentence",
    "character_start",
    "character_end",
    "surface_form",
    "lowercase_form",
    "punctuation_stripped_form",
    "normalized_form",
    "part_of_speech",
    "lemma",
    "normalized_lemma",
    "morphological_features",
    "is_punctuation",
    "is_numeric",
    "is_proper_noun",
    "is_stopword",
    "context",
    "preprocessing_warnings",
    "lexicon_id",
    "match_method",
    "matched_term",
    "source_row",
    "included",
    "match_reason",
    "source_valence",
    "source_arousal",
    "source_dominance",
    "normalized_valence",
    "normalized_arousal",
    "normalized_dominance",
]


def _atomic_write_csv(
    destination: Path,
    fieldnames: list[str],
    rows: Iterable[Mapping[str, object]],
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8-sig",
            newline="",
            prefix=f".{destination.stem}-",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            writer = csv.DictWriter(temporary, fieldnames=fieldnames, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_name, destination)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def _score_value(scores: object, dimension: str) -> float | str:
    return getattr(scores, dimension) if scores is not None else ""


def _token_audit_rows(result: AnalysisResult) -> Iterable[dict[str, object]]:
    match_map = result.match_map()
    for token in result.tokens:
        match = match_map[token.token_id]
        yield {
            "analysis_id": result.analysis_id,
            "scenario_id": result.scenario_id,
            "text_id": token.text_id,
            "text_version_id": token.text_version_id,
            "token_id": token.token_id,
            "section_number": token.section_number,
            "stanza_number": token.stanza_number,
            "line_number": token.line_number,
            "token_position": token.token_position,
            "sentence_number": token.sentence_number or "",
            "token_position_in_sentence": token.token_position_in_sentence or "",
            "character_start": token.character_start,
            "character_end": token.character_end,
            "surface_form": token.surface_form,
            "lowercase_form": token.lowercase_form,
            "punctuation_stripped_form": token.punctuation_stripped_form,
            "normalized_form": token.normalized_form,
            "part_of_speech": token.part_of_speech,
            "lemma": token.lemma,
            "normalized_lemma": token.normalized_lemma,
            "morphological_features": token.morphological_features,
            "is_punctuation": token.is_punctuation,
            "is_numeric": token.is_numeric,
            "is_proper_noun": token.is_proper_noun,
            "is_stopword": token.is_stopword,
            "context": token.context,
            "preprocessing_warnings": " | ".join(token.preprocessing_warnings),
            "lexicon_id": match.lexicon_id,
            "match_method": match.method.value,
            "matched_term": match.matched_term or "",
            "source_row": match.source_row or "",
            "included": match.included,
            "match_reason": match.reason,
            "source_valence": _score_value(match.original_scores, "valence"),
            "source_arousal": _score_value(match.original_scores, "arousal"),
            "source_dominance": _score_value(match.original_scores, "dominance"),
            "normalized_valence": _score_value(match.normalized_scores, "valence"),
            "normalized_arousal": _score_value(match.normalized_scores, "arousal"),
            "normalized_dominance": _score_value(match.normalized_scores, "dominance"),
        }


def _summary_rows(result: AnalysisResult) -> Iterable[dict[str, object]]:
    groups = (
        ("token", "source", result.vad_summary.token_weighted_original),
        ("type", "source", result.vad_summary.type_weighted_original),
        ("token", "normalized_0_1", result.vad_summary.token_weighted_normalized),
        ("type", "normalized_0_1", result.vad_summary.type_weighted_normalized),
    )
    for weighting, scale, group in groups:
        for dimension, stats in group.by_dimension().items():
            values = asdict(stats)
            yield {
                "analysis_id": result.analysis_id,
                "scenario_id": result.scenario_id,
                "lexicon_id": result.lexicon_metadata.lexicon_id,
                "weighting": weighting,
                "scale": scale,
                "dimension": dimension,
                **values,
                "minimum_match_requirement": (
                    result.vad_summary.minimum_match_requirement
                ),
                "is_sparse": result.vad_summary.is_sparse,
            }


def export_analysis_csv(result: AnalysisResult, output_directory: Path) -> tuple[Path, ...]:
    """Write a traceable four-file CSV bundle and return the created paths."""

    output_directory = Path(output_directory)
    audit_path = output_directory / "token_audit.csv"
    coverage_path = output_directory / "coverage.csv"
    summary_path = output_directory / "vad_summary.csv"
    manifest_path = output_directory / "analysis_manifest.csv"

    audit_rows = list(_token_audit_rows(result))
    _atomic_write_csv(audit_path, TOKEN_AUDIT_FIELDS, audit_rows)

    coverage_row = {
        "analysis_id": result.analysis_id,
        "scenario_id": result.scenario_id,
        "text_id": result.document.text_id,
        "text_version_id": result.document.text_version_id,
        "lexicon_id": result.lexicon_metadata.lexicon_id,
        **asdict(result.coverage),
    }
    _atomic_write_csv(coverage_path, list(coverage_row), [coverage_row])

    summary_rows = list(_summary_rows(result))
    _atomic_write_csv(summary_path, list(summary_rows[0]), summary_rows)

    manifest_rows = [
        {"field": "analysis_id", "value": result.analysis_id},
        {"field": "scenario_id", "value": result.scenario_id},
        {"field": "software_version", "value": __version__},
        {"field": "text_id", "value": result.document.text_id},
        {"field": "text_version_id", "value": result.document.text_version_id},
        {"field": "text_sha256", "value": result.document.text_sha256},
        {"field": "lexicon_id", "value": result.lexicon_metadata.lexicon_id},
        {"field": "lexicon_version", "value": result.lexicon_metadata.version},
        {"field": "lexicon_sha256", "value": result.lexicon_validation.source_sha256},
        {"field": "adapter_version", "value": result.lexicon_metadata.adapter_version},
        {"field": "source_scale_min", "value": result.lexicon_metadata.source_scale_min},
        {"field": "source_scale_max", "value": result.lexicon_metadata.source_scale_max},
        {
            "field": "normalization_formula",
            "value": result.lexicon_metadata.normalization_formula,
        },
        {"field": "preprocessing_recipe", "value": result.preprocessing.recipe_id},
        {"field": "pipeline_name", "value": result.preprocessing.pipeline_name},
        {"field": "pipeline_version", "value": result.preprocessing.pipeline_version},
        {"field": "warnings", "value": " | ".join(result.warnings)},
    ]
    _atomic_write_csv(manifest_path, ["field", "value"], manifest_rows)
    return audit_path, coverage_path, summary_path, manifest_path
