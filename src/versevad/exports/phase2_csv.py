"""Stable UTF-8 CSV bundle for Phase 2 multi-lexicon results."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

from versevad import __version__
from versevad.exports.csv_export import _atomic_write_csv
from versevad.models import CrossLexiconComparison, Phase2AnalysisResult


MATCH_FIELDS = [
    "analysis_id",
    "scenario_id",
    "phrase_policy",
    "text_id",
    "text_version_id",
    "lexicon_id",
    "match_id",
    "token_ids",
    "surface_span",
    "start_token_position",
    "end_token_position",
    "line_number",
    "stanza_number",
    "match_method",
    "selection",
    "matched_term",
    "matched_lookup_form",
    "source_rows",
    "included",
    "suppressed_by_match_id",
    "reason",
    "source_valence",
    "source_arousal",
    "source_dominance",
    "normalized_valence",
    "normalized_arousal",
    "normalized_dominance",
    "associations",
    "intensities",
]


def _score(scores: object, dimension: str) -> float | str:
    return getattr(scores, dimension) if scores is not None else ""


def _match_rows(results: tuple[Phase2AnalysisResult, ...]) -> Iterable[dict[str, object]]:
    for result in results:
        token_map = {token.token_id: token for token in result.tokens}
        for match in result.matches:
            yield {
                "analysis_id": result.analysis_id,
                "scenario_id": result.scenario_id,
                "phrase_policy": result.phrase_policy.value,
                "text_id": result.document.text_id,
                "text_version_id": result.document.text_version_id,
                "lexicon_id": match.lexicon_id,
                "match_id": match.match_id,
                "token_ids": " | ".join(match.token_ids),
                "surface_span": " ".join(
                    token_map[token_id].surface_form for token_id in match.token_ids
                ),
                "start_token_position": match.start_token_position,
                "end_token_position": match.end_token_position,
                "line_number": match.line_number,
                "stanza_number": match.stanza_number,
                "match_method": match.method.value,
                "selection": match.selection.value,
                "matched_term": match.matched_term or "",
                "matched_lookup_form": match.matched_lookup_form or "",
                "source_rows": " | ".join(str(row) for row in match.source_rows),
                "included": match.included,
                "suppressed_by_match_id": match.suppressed_by_match_id or "",
                "reason": match.reason,
                "source_valence": _score(match.original_scores, "valence"),
                "source_arousal": _score(match.original_scores, "arousal"),
                "source_dominance": _score(match.original_scores, "dominance"),
                "normalized_valence": _score(match.normalized_scores, "valence"),
                "normalized_arousal": _score(match.normalized_scores, "arousal"),
                "normalized_dominance": _score(match.normalized_scores, "dominance"),
                "associations": " | ".join(match.associations),
                "intensities": json.dumps(dict(match.intensities), sort_keys=True),
            }


def _coverage_rows(results: tuple[Phase2AnalysisResult, ...]) -> list[dict[str, object]]:
    return [
        {
            "analysis_id": result.analysis_id,
            "scenario_id": result.scenario_id,
            "phrase_policy": result.phrase_policy.value,
            "text_id": result.document.text_id,
            "text_version_id": result.document.text_version_id,
            "lexicon_id": result.lexicon_metadata.lexicon_id,
            "value_kind": result.lexicon_metadata.value_kind.value,
            **asdict(result.coverage),
        }
        for result in results
    ]


def _vad_rows(results: tuple[Phase2AnalysisResult, ...]) -> list[dict[str, object]]:
    rows = []
    for result in results:
        if result.vad_summary is None:
            continue
        groups = (
            ("token", "source", result.vad_summary.token_weighted_original),
            ("type", "source", result.vad_summary.type_weighted_original),
            ("token", "normalized_0_1", result.vad_summary.token_weighted_normalized),
            ("type", "normalized_0_1", result.vad_summary.type_weighted_normalized),
        )
        for weighting, scale, group in groups:
            for dimension, stats in group.by_dimension().items():
                rows.append(
                    {
                        "analysis_id": result.analysis_id,
                        "lexicon_id": result.lexicon_metadata.lexicon_id,
                        "weighting": weighting,
                        "scale": scale,
                        "dimension": dimension,
                        **asdict(stats),
                        "minimum_match_requirement": result.vad_summary.minimum_match_requirement,
                        "is_sparse": result.vad_summary.is_sparse,
                    }
                )
    return rows


def _category_rows(results: tuple[Phase2AnalysisResult, ...]) -> list[dict[str, object]]:
    rows = []
    for result in results:
        for stats in result.category_statistics:
            row = asdict(stats)
            row["analysis_id"] = result.analysis_id
            row["lexicon_id"] = result.lexicon_metadata.lexicon_id
            row["line_distribution"] = json.dumps(row["line_distribution"])
            row["stanza_distribution"] = json.dumps(row["stanza_distribution"])
            row["top_contributing_terms"] = json.dumps(row["top_contributing_terms"])
            rows.append(row)
    return rows


def _intensity_rows(results: tuple[Phase2AnalysisResult, ...]) -> list[dict[str, object]]:
    rows = []
    for result in results:
        for stats in result.intensity_statistics:
            rows.append(
                {
                    "analysis_id": result.analysis_id,
                    "lexicon_id": result.lexicon_metadata.lexicon_id,
                    "category": stats.category,
                    "matched_word_emotion_pairs": stats.matched_word_emotion_pairs,
                    "matched_token_occurrences": stats.matched_token_occurrences,
                    "prevalence_among_lexical_tokens": stats.prevalence_among_lexical_tokens,
                    "prevalence_among_emotion_intensity_matches": (
                        stats.prevalence_among_emotion_intensity_matches
                    ),
                    **{
                        f"token_{key}": value
                        for key, value in asdict(stats.token_weighted).items()
                    },
                    **{
                        f"type_{key}": value
                        for key, value in asdict(stats.type_weighted).items()
                    },
                    "line_distribution": json.dumps(stats.line_distribution),
                    "stanza_distribution": json.dumps(stats.stanza_distribution),
                    "top_contributing_terms": json.dumps(
                        [asdict(item) for item in stats.top_contributing_terms]
                    ),
                }
            )
    return rows


def _manifest_rows(results: tuple[Phase2AnalysisResult, ...]) -> list[dict[str, object]]:
    return [
        {
            "software_version": __version__,
            "analysis_id": result.analysis_id,
            "scenario_id": result.scenario_id,
            "phrase_policy": result.phrase_policy.value,
            "text_id": result.document.text_id,
            "text_version_id": result.document.text_version_id,
            "text_sha256": result.document.text_sha256,
            "lexicon_id": result.lexicon_metadata.lexicon_id,
            "display_name": result.lexicon_metadata.display_name,
            "family": result.lexicon_metadata.family,
            "lexicon_version": result.lexicon_metadata.version,
            "value_kind": result.lexicon_metadata.value_kind.value,
            "source_sha256": result.lexicon_validation.source_sha256,
            "adapter_version": result.lexicon_metadata.adapter_version,
            "source_scale_min": result.lexicon_metadata.source_scale_min,
            "source_scale_max": result.lexicon_metadata.source_scale_max,
            "normalization_formula": result.lexicon_metadata.normalization_formula,
            "phrase_support": result.lexicon_metadata.phrase_support,
            "preprocessing_recipe": result.preprocessing.recipe_id,
            "pipeline_name": result.preprocessing.pipeline_name,
            "pipeline_version": result.preprocessing.pipeline_version,
            "total_source_rows": result.lexicon_validation.total_rows,
            "usable_source_entries": result.lexicon_validation.usable_entries,
            "source_phrase_entries": result.lexicon_validation.phrase_entries,
            "source_loaded_at_utc": result.lexicon_validation.loaded_at_utc,
            "warnings": " | ".join(result.warnings),
        }
        for result in results
    ]


def export_phase2_csv(
    results: Iterable[Phase2AnalysisResult],
    comparison: CrossLexiconComparison,
    output_directory: Path,
) -> tuple[Path, ...]:
    """Export independent results side by side; no consensus field is created."""

    result_tuple = tuple(results)
    if not result_tuple:
        raise ValueError("At least one Phase 2 result is required for export.")
    output_directory = Path(output_directory)
    paths = {
        "matches": output_directory / "phase2_match_audit.csv",
        "coverage": output_directory / "phase2_coverage.csv",
        "vad": output_directory / "phase2_vad_summary.csv",
        "categories": output_directory / "phase2_emotion_associations.csv",
        "intensity": output_directory / "phase2_emotion_intensity.csv",
        "comparison": output_directory / "phase2_cross_lexicon_comparison.csv",
        "manifest": output_directory / "phase2_manifest.csv",
    }
    _atomic_write_csv(paths["matches"], MATCH_FIELDS, _match_rows(result_tuple))
    coverage = _coverage_rows(result_tuple)
    _atomic_write_csv(paths["coverage"], list(coverage[0]), coverage)
    vad = _vad_rows(result_tuple)
    _atomic_write_csv(
        paths["vad"],
        list(vad[0]) if vad else ["analysis_id", "lexicon_id"],
        vad,
    )
    categories = _category_rows(result_tuple)
    _atomic_write_csv(
        paths["categories"],
        list(categories[0]) if categories else ["analysis_id", "lexicon_id"],
        categories,
    )
    intensities = _intensity_rows(result_tuple)
    _atomic_write_csv(
        paths["intensity"],
        list(intensities[0]) if intensities else ["analysis_id", "lexicon_id"],
        intensities,
    )
    comparison_rows = [asdict(metric) for metric in comparison.metrics]
    for row in comparison_rows:
        row["value_kind"] = row["value_kind"].value
        row["comparison_id"] = comparison.comparison_id
        row["phrase_policy"] = comparison.phrase_policy.value
    _atomic_write_csv(paths["comparison"], list(comparison_rows[0]), comparison_rows)
    manifest = _manifest_rows(result_tuple)
    _atomic_write_csv(paths["manifest"], list(manifest[0]), manifest)
    return tuple(paths.values())
