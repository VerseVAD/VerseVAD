"""Stable UTF-8 CSV bundle for Phase 2 multi-lexicon results."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict
from enum import Enum
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
    "normalized_span",
    "lemma_span",
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
    "included_in_all_matched",
    "included_in_stopword_excluded",
    "stopword_status",
    "stopword_exclusion_reason",
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


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Not JSON serializable: {type(value)!r}")


def _atomic_write_json(destination: Path, payload: object) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{destination.stem}-",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
            json.dump(
                payload,
                temporary,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
                default=_json_default,
            )
            temporary.write("\n")
        os.replace(temporary_name, destination)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


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
                "normalized_span": " ".join(
                    token_map[token_id].normalized_form for token_id in match.token_ids
                ),
                "lemma_span": " ".join(
                    token_map[token_id].lemma for token_id in match.token_ids
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
                "included_in_all_matched": match.included,
                "included_in_stopword_excluded": match.included_in_stopword_view,
                "stopword_status": match.stopword_status,
                "stopword_exclusion_reason": match.stopword_exclusion_reason,
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
    rows: list[dict[str, object]] = []
    for result in results:
        common = {
            "analysis_id": result.analysis_id,
            "scenario_id": result.scenario_id,
            "phrase_policy": result.phrase_policy.value,
            "text_id": result.document.text_id,
            "text_version_id": result.document.text_version_id,
            "lexicon_id": result.lexicon_metadata.lexicon_id,
            "value_kind": result.lexicon_metadata.value_kind.value,
        }
        rows.append(
            {
                **common,
                "analysis_view": "all_matched",
                **asdict(result.coverage),
            }
        )
        if result.stopword_coverage is not None:
            filtered = asdict(result.stopword_coverage)
            rows.append(
                {
                    **common,
                    "analysis_view": "stopwords_excluded",
                    **filtered,
                }
            )
    return rows


def _vad_rows(results: tuple[Phase2AnalysisResult, ...]) -> list[dict[str, object]]:
    rows = []
    for result in results:
        if result.vad_summary is None:
            continue
        summary = result.vad_summary
        groups = (
            ("all_matched", "token", "source", summary.token_weighted_original),
            ("all_matched", "type", "source", summary.type_weighted_original),
            ("all_matched", "token", "normalized_0_1", summary.token_weighted_normalized),
            ("all_matched", "type", "normalized_0_1", summary.type_weighted_normalized),
            (
                "stopwords_excluded",
                "token",
                "source",
                summary.stopword_excluded_token_weighted_original,
            ),
            (
                "stopwords_excluded",
                "type",
                "source",
                summary.stopword_excluded_type_weighted_original,
            ),
            (
                "stopwords_excluded",
                "token",
                "normalized_0_1",
                summary.stopword_excluded_token_weighted_normalized,
            ),
            (
                "stopwords_excluded",
                "type",
                "normalized_0_1",
                summary.stopword_excluded_type_weighted_normalized,
            ),
        )
        for analysis_view, weighting, scale, group in groups:
            if group is None:
                continue
            for dimension, stats in group.by_dimension().items():
                rows.append(
                    {
                        "analysis_id": result.analysis_id,
                        "lexicon_id": result.lexicon_metadata.lexicon_id,
                        "analysis_view": analysis_view,
                        "weighting": weighting,
                        "scale": scale,
                        "dimension": dimension,
                        **asdict(stats),
                        "minimum_match_requirement": summary.minimum_match_requirement,
                        "is_sparse": (
                            summary.is_sparse
                            if analysis_view == "all_matched"
                            else summary.stopword_excluded_is_sparse
                        ),
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
            "stopword_mode": (
                result.stopword_policy.mode.value if result.stopword_policy else ""
            ),
            "stopword_source": (
                result.stopword_policy.source if result.stopword_policy else ""
            ),
            "stopword_library_version": (
                result.stopword_policy.library_version if result.stopword_policy else ""
            ),
            "stopword_list_version": (
                result.stopword_policy.list_version if result.stopword_policy else ""
            ),
            "standard_stopword_count": (
                result.stopword_policy.standard_word_count if result.stopword_policy else ""
            ),
            "standard_stopword_sha256": (
                result.stopword_policy.standard_list_sha256 if result.stopword_policy else ""
            ),
            "active_stopword_count": (
                len(result.stopword_policy.active_words) if result.stopword_policy else ""
            ),
            "active_stopword_sha256": (
                result.stopword_policy.active_list_sha256 if result.stopword_policy else ""
            ),
            "active_stopwords": (
                json.dumps(result.stopword_policy.active_words)
                if result.stopword_policy
                else ""
            ),
            "protected_stopwords": (
                json.dumps(result.stopword_policy.protected_words)
                if result.stopword_policy
                else ""
            ),
            "custom_stopword_additions": (
                json.dumps(result.stopword_policy.custom_additions)
                if result.stopword_policy
                else ""
            ),
            "custom_stopword_removals": (
                json.dumps(result.stopword_policy.custom_removals)
                if result.stopword_policy
                else ""
            ),
            "excluded_matched_stopword_observations": (
                result.stopword_coverage.excluded_matched_observation_count
                if result.stopword_coverage
                else ""
            ),
            "excluded_matched_stopword_types": (
                result.stopword_coverage.excluded_matched_type_count
                if result.stopword_coverage
                else ""
            ),
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
        "json": output_directory / "phase2_results.json",
    }
    _atomic_write_csv(paths["matches"], MATCH_FIELDS, _match_rows(result_tuple))
    coverage = _coverage_rows(result_tuple)
    coverage_fields = list(
        dict.fromkeys(key for row in coverage for key in row)
    )
    _atomic_write_csv(paths["coverage"], coverage_fields, coverage)
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
    payload = {
        "results": [asdict(result) for result in result_tuple],
        "comparison": asdict(comparison),
    }
    _atomic_write_json(paths["json"], payload)
    return tuple(paths.values())
