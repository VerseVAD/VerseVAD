"""CSV chart data and narrative Word exports for PoetryID results."""

from __future__ import annotations

import csv
import io
from typing import Iterable

from versevad.exports.docx_report import REPORT_PROFILES, build_narrative_report
from versevad.exports.module_manifest import export_module_manifest_csv
from versevad.poetry_id import ARCHETYPES, PoetryIDAnalysisResult


def _csv_bytes(
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def _assignment_key(row) -> str:
    return (
        f"{row.source_lexicon_id}:{row.analysis_view}:{row.weighting_mode}"
    )


def export_poetry_id_summary_csv(result: PoetryIDAnalysisResult) -> bytes:
    fields = [
        "result_status",
        "assignment_id",
        "source_analysis_id",
        "source_lexicon_id",
        "source_lexicon_name",
        "source_lexicon_version",
        "source_adapter_version",
        "analysis_view",
        "weighting_mode",
        "valence",
        "arousal",
        "dominance",
        "valence_level",
        "arousal_level",
        "dominance_level",
        "categorical_archetype_id",
        "categorical_archetype_name",
        "short_descriptor",
        "nearest_centroid_archetype_id",
        "nearest_centroid_archetype_name",
        "categorical_centroid_match",
        "categorical_centroid_distance",
        "neighbor_margin",
        "confidence_label",
        "confidence_explanation",
        "boundary_dimensions",
        "coverage_assessment",
        "matched_token_count",
        "eligible_token_count",
        "token_coverage",
        "matched_type_count",
        "eligible_type_count",
        "type_coverage",
        "weighted_vad_observation_count",
        "narrative_summary",
        "interpretive_caution",
        "unavailable_reason",
        "unavailable_message",
    ]
    rows: list[dict[str, object]] = []
    for item in result.assignments:
        rows.append(
            {
                "result_status": result.status,
                "assignment_id": _assignment_key(item),
                "source_analysis_id": item.source_analysis_id,
                "source_lexicon_id": item.source_lexicon_id,
                "source_lexicon_name": item.source_lexicon_name,
                "source_lexicon_version": item.source_lexicon_version,
                "source_adapter_version": item.source_adapter_version,
                "analysis_view": item.analysis_view,
                "weighting_mode": item.weighting_mode,
                "valence": item.vad.valence,
                "arousal": item.vad.arousal,
                "dominance": item.vad.dominance,
                "valence_level": item.valence_level.value,
                "arousal_level": item.arousal_level.value,
                "dominance_level": item.dominance_level.value,
                "categorical_archetype_id": (
                    item.categorical_archetype.archetype_id
                ),
                "categorical_archetype_name": (
                    item.categorical_archetype.name
                ),
                "short_descriptor": (
                    item.categorical_archetype.short_descriptor
                ),
                "nearest_centroid_archetype_id": (
                    item.nearest_centroid_archetype.archetype_id
                ),
                "nearest_centroid_archetype_name": (
                    item.nearest_centroid_archetype.name
                ),
                "categorical_centroid_match": item.categorical_match,
                "categorical_centroid_distance": item.centroid_distance,
                "neighbor_margin": item.confidence.neighbor_margin,
                "confidence_label": item.confidence.label,
                "confidence_explanation": item.confidence.explanation,
                "boundary_dimensions": " | ".join(
                    item.confidence.boundary_dimensions
                ),
                "coverage_assessment": (
                    item.confidence.coverage_assessment
                ),
                "matched_token_count": item.coverage.matched_token_count,
                "eligible_token_count": item.coverage.eligible_token_count,
                "token_coverage": item.coverage.token_coverage,
                "matched_type_count": item.coverage.matched_type_count,
                "eligible_type_count": item.coverage.eligible_type_count,
                "type_coverage": item.coverage.type_coverage,
                "weighted_vad_observation_count": (
                    item.coverage.weighted_vad_observation_count
                ),
                "narrative_summary": item.narrative_summary,
                "interpretive_caution": (
                    item.categorical_archetype.interpretive_caution
                ),
                "unavailable_reason": "",
                "unavailable_message": "",
            }
        )
    for item in result.unavailable:
        rows.append(
            {
                "result_status": "unavailable",
                "assignment_id": (
                    f"{item.source_lexicon_id}:{item.analysis_view}:"
                    f"{item.weighting_mode}"
                ),
                "source_lexicon_id": item.source_lexicon_id,
                "source_lexicon_name": item.source_lexicon_name,
                "analysis_view": item.analysis_view,
                "weighting_mode": item.weighting_mode,
                "unavailable_reason": item.reason,
                "unavailable_message": item.message,
            }
        )
    return _csv_bytes(fields, rows)


def export_poetry_id_neighbors_csv(result: PoetryIDAnalysisResult) -> bytes:
    fields = [
        "assignment_id",
        "source_lexicon_id",
        "analysis_view",
        "weighting_mode",
        "rank",
        "archetype_id",
        "archetype_name",
        "distance",
        "relative_affinity",
        "affinity_note",
        "is_categorical_assignment",
        "is_nearest_centroid",
    ]
    rows = []
    for item in result.assignments:
        for neighbor in item.neighbors:
            rows.append(
                {
                    "assignment_id": _assignment_key(item),
                    "source_lexicon_id": item.source_lexicon_id,
                    "analysis_view": item.analysis_view,
                    "weighting_mode": item.weighting_mode,
                    "rank": neighbor.rank,
                    "archetype_id": neighbor.archetype_id,
                    "archetype_name": neighbor.archetype_name,
                    "distance": neighbor.distance,
                    "relative_affinity": neighbor.affinity,
                    "affinity_note": (
                        "Inverse-distance affinities normalized across all "
                        "27 profiles; not probabilities."
                    ),
                    "is_categorical_assignment": (
                        neighbor.archetype_id
                        == item.categorical_archetype.archetype_id
                    ),
                    "is_nearest_centroid": neighbor.rank == 1,
                }
            )
    return _csv_bytes(fields, rows)


def export_poetry_id_lexical_character_csv(
    result: PoetryIDAnalysisResult,
) -> bytes:
    fields = [
        "dimension_id",
        "source_module",
        "configuration_id",
        "weighting_mode",
        "count",
        "mean",
        "median",
        "population_standard_deviation",
        "minimum",
        "first_quartile",
        "third_quartile",
        "maximum",
        "coverage",
        "unit",
        "level",
        "display_label",
        "low_max",
        "high_min",
        "note",
    ]
    rows = []
    for item in result.lexical_character:
        stats = item.statistics
        rows.append(
            {
                "dimension_id": item.dimension_id,
                "source_module": item.source_module,
                "configuration_id": item.configuration_id,
                "weighting_mode": item.weighting_mode,
                "count": stats.count,
                "mean": stats.mean,
                "median": stats.median,
                "population_standard_deviation": (
                    stats.population_standard_deviation
                ),
                "minimum": stats.minimum,
                "first_quartile": stats.first_quartile,
                "third_quartile": stats.third_quartile,
                "maximum": stats.maximum,
                "coverage": item.coverage,
                "unit": item.unit,
                "level": item.level.value,
                "display_label": item.display_label,
                "low_max": item.low_max,
                "high_min": item.high_min,
                "note": (
                    "Secondary lexical character; does not alter the VAD "
                    "archetype assignment."
                ),
            }
        )
    return _csv_bytes(fields, rows)


def export_poetry_id_methodology_csv(
    result: PoetryIDAnalysisResult,
) -> bytes:
    profile = result.configuration.threshold_profile
    fields = ["section", "item", "value", "note"]
    rows: list[dict[str, object]] = [
        {
            "section": "method",
            "item": "dependency",
            "value": "completed normalized source-specific VAD results",
            "note": (
                "PoetryID does not tokenize, load a VAD lexicon, or calculate "
                "VAD scores independently."
            ),
        },
        {
            "section": "method",
            "item": "distance",
            "value": result.configuration.distance_metric,
            "note": "Euclidean distance across normalized V, A, and D.",
        },
        {
            "section": "method",
            "item": "affinity",
            "value": "inverse distance normalized across 27 centroids",
            "note": "Relative affinities are not probabilities.",
        },
        {
            "section": "method",
            "item": "categorical_rule",
            "value": "low <= low_max; high >= high_min; otherwise moderate",
            "note": "Boundary inclusivity is explicit.",
        },
        {
            "section": "threshold_profile",
            "item": "profile_id",
            "value": profile.profile_id,
            "note": profile.name,
        },
        {
            "section": "threshold_profile",
            "item": "configuration_version",
            "value": profile.configuration_version,
            "note": profile.normalization_basis,
        },
        {
            "section": "configuration",
            "item": "configuration_id",
            "value": result.configuration.configuration_id,
            "note": "",
        },
        {
            "section": "configuration",
            "item": "minimum_matched_tokens",
            "value": result.configuration.minimum_matched_tokens,
            "note": "",
        },
        {
            "section": "configuration",
            "item": "minimum_matched_types",
            "value": result.configuration.minimum_matched_types,
            "note": "",
        },
        {
            "section": "interpretation",
            "item": "scholarly_caution",
            "value": (
                "nearest candidate lexical-affective profile under the "
                "selected rules"
            ),
            "note": (
                "Not a declaration of the poem's emotion, speaker psychology, "
                "authorial intent, or reader response."
            ),
        },
    ]
    for dimension, band in profile.dimensions.items():
        rows.extend(
            (
                {
                    "section": "threshold",
                    "item": f"{dimension}.low_max",
                    "value": band.low_max,
                    "note": "Inclusive upper boundary for low.",
                },
                {
                    "section": "threshold",
                    "item": f"{dimension}.high_min",
                    "value": band.high_min,
                    "note": "Inclusive lower boundary for high.",
                },
                {
                    "section": "centroid",
                    "item": f"{dimension}.low",
                    "value": band.low_centroid,
                    "note": "",
                },
                {
                    "section": "centroid",
                    "item": f"{dimension}.moderate",
                    "value": band.moderate_centroid,
                    "note": "",
                },
                {
                    "section": "centroid",
                    "item": f"{dimension}.high",
                    "value": band.high_centroid,
                    "note": "",
                },
            )
        )
    return _csv_bytes(fields, rows)


def export_poetry_id_archetype_map_csv(
    result: PoetryIDAnalysisResult,
) -> bytes:
    profile = result.configuration.threshold_profile
    fields = [
        "archetype_id",
        "archetype_name",
        "valence_level",
        "arousal_level",
        "dominance_level",
        "valence_centroid",
        "arousal_centroid",
        "dominance_centroid",
        "short_descriptor",
        "summary",
        "interpretive_caution",
    ]
    rows = []
    for item in ARCHETYPES:
        rows.append(
            {
                "archetype_id": item.archetype_id,
                "archetype_name": item.name,
                "valence_level": item.valence_level.value,
                "arousal_level": item.arousal_level.value,
                "dominance_level": item.dominance_level.value,
                "valence_centroid": profile.dimensions["valence"].centroid(
                    item.valence_level
                ),
                "arousal_centroid": profile.dimensions["arousal"].centroid(
                    item.arousal_level
                ),
                "dominance_centroid": profile.dimensions["dominance"].centroid(
                    item.dominance_level
                ),
                "short_descriptor": item.short_descriptor,
                "summary": item.summary,
                "interpretive_caution": item.interpretive_caution,
            }
        )
    return _csv_bytes(fields, rows)


def export_poetry_id_vad_scales_csv(
    result: PoetryIDAnalysisResult,
) -> bytes:
    fields = [
        "assignment_id",
        "source_lexicon_id",
        "analysis_view",
        "weighting_mode",
        "dimension",
        "score",
        "classified_level",
        "low_max",
        "high_min",
        "low_centroid",
        "moderate_centroid",
        "high_centroid",
        "distance_to_nearest_boundary",
    ]
    rows = []
    profile = result.configuration.threshold_profile
    for item in result.assignments:
        for dimension in ("valence", "arousal", "dominance"):
            band = profile.dimensions[dimension]
            score = getattr(item.vad, dimension)
            rows.append(
                {
                    "assignment_id": _assignment_key(item),
                    "source_lexicon_id": item.source_lexicon_id,
                    "analysis_view": item.analysis_view,
                    "weighting_mode": item.weighting_mode,
                    "dimension": dimension,
                    "score": score,
                    "classified_level": getattr(
                        item, f"{dimension}_level"
                    ).value,
                    "low_max": band.low_max,
                    "high_min": band.high_min,
                    "low_centroid": band.low_centroid,
                    "moderate_centroid": band.moderate_centroid,
                    "high_centroid": band.high_centroid,
                    "distance_to_nearest_boundary": min(
                        abs(score - band.low_max),
                        abs(score - band.high_min),
                    ),
                }
            )
    return _csv_bytes(fields, rows)


def export_poetry_id_bundle(
    result: PoetryIDAnalysisResult,
    *,
    text_title: str = "",
) -> dict[str, bytes]:
    """Return PoetryID's complete CSV and narrative Word export bundle."""

    bundle = {
        "poetry_id_summary.csv": export_poetry_id_summary_csv(result),
        "poetry_id_neighbors.csv": export_poetry_id_neighbors_csv(result),
        "poetry_id_lexical_character.csv": (
            export_poetry_id_lexical_character_csv(result)
        ),
        "poetry_id_methodology.csv": (
            export_poetry_id_methodology_csv(result)
        ),
        "poetry_id_archetype_map.csv": (
            export_poetry_id_archetype_map_csv(result)
        ),
        "poetry_id_vad_scales.csv": export_poetry_id_vad_scales_csv(result),
        "poetry_id_manifest.csv": export_module_manifest_csv(result),
    }
    report_rows = [
        {
            "section": (
                f"{item.source_lexicon_name} · {item.analysis_view} · "
                f"{item.weighting_mode}"
            ),
            "metric": "nearest_candidate_profile",
            "value": item.categorical_archetype.name,
            "unit_or_scale": item.categorical_archetype.short_descriptor,
            "denominator": (
                f"{item.coverage.matched_token_count} of "
                f"{item.coverage.eligible_token_count} eligible tokens"
            ),
            "note": (
                f"Confidence: {item.confidence.label}. "
                f"{item.narrative_summary} "
                f"{item.categorical_archetype.interpretive_caution}"
            ),
        }
        for item in result.assignments
    ]
    report_rows.extend(
        {
            "section": "unavailable evidence",
            "metric": item.analysis_view or "analysis",
            "value": "unavailable",
            "unit_or_scale": "",
            "denominator": "",
            "note": item.message,
        }
        for item in result.unavailable
    )
    bundle["poetry_id_report.docx"] = build_narrative_report(
        profile=REPORT_PROFILES["poetry_id"],
        summary_rows=report_rows,
        companion_csv_files=tuple(bundle),
        text_title=text_title,
        text_id=result.module_result.text_id,
        result_id=result.module_result.result_id,
        warnings=tuple(
            warning.message for warning in result.module_result.warnings
        ),
        additional_paragraphs=(
            "PoetryID reports a nearest candidate lexical-affective profile, not "
            "the poem's emotion. Relative affinities are inverse-distance "
            "summaries, not probabilities.",
        ),
    )
    return bundle


__all__ = [
    "export_poetry_id_archetype_map_csv",
    "export_poetry_id_bundle",
    "export_poetry_id_lexical_character_csv",
    "export_poetry_id_methodology_csv",
    "export_poetry_id_neighbors_csv",
    "export_poetry_id_summary_csv",
    "export_poetry_id_vad_scales_csv",
]
