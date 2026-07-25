"""Stable UTF-8 CSV and narrative Word exports for AoA results."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict
from typing import Iterable

from versevad.exports.docx_report import build_narrative_report_from_summary_csv
from versevad.exports.module_manifest import export_module_manifest_csv
from versevad.lexical_semantic.aoa import AoAAnalysisResult


def _csv_bytes(
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def export_aoa_summary_csv(result: AoAAnalysisResult) -> bytes:
    summary = result.summary
    stats = summary.statistics
    denominator = f"{summary.matched_token_count} matched eligible token occurrences"
    rows = [
        {
            "section": "descriptive_statistics",
            "metric": "mean_normative_aoa",
            "value": stats.mean,
            "unit_or_scale": "source mean age in years",
            "denominator": denominator,
            "note": "Mean of matched source Rating.Mean values.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "median_normative_aoa",
            "value": stats.median,
            "unit_or_scale": "source mean age in years",
            "denominator": denominator,
            "note": "Token-weighted median of matched source means.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "population_standard_deviation",
            "value": stats.population_standard_deviation,
            "unit_or_scale": "years",
            "denominator": denominator,
            "note": (
                "Dispersion among the poem's matched source means; distinct from "
                "each source entry's rater standard deviation."
            ),
        },
        {
            "section": "descriptive_statistics",
            "metric": "minimum_normative_aoa",
            "value": stats.minimum,
            "unit_or_scale": "source mean age in years",
            "denominator": denominator,
            "note": "",
        },
        {
            "section": "descriptive_statistics",
            "metric": "first_quartile_normative_aoa",
            "value": stats.first_quartile,
            "unit_or_scale": "source mean age in years",
            "denominator": denominator,
            "note": "Inclusive quartile method.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "third_quartile_normative_aoa",
            "value": stats.third_quartile,
            "unit_or_scale": "source mean age in years",
            "denominator": denominator,
            "note": "Inclusive quartile method.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "interquartile_range",
            "value": summary.interquartile_range,
            "unit_or_scale": "years",
            "denominator": denominator,
            "note": "Third quartile minus first quartile.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "maximum_normative_aoa",
            "value": stats.maximum,
            "unit_or_scale": "source mean age in years",
            "denominator": denominator,
            "note": "",
        },
        {
            "section": "source_response_evidence",
            "metric": "mean_source_rating_standard_deviation",
            "value": summary.source_standard_deviation_statistics.mean,
            "unit_or_scale": "source-rating years",
            "denominator": (
                f"{summary.source_standard_deviation_statistics.count} matched "
                "token occurrences with available source Rating.SD"
            ),
            "note": "Source rater dispersion, not poem-level token dispersion.",
        },
        {
            "section": "source_response_evidence",
            "metric": "minimum_source_numeric_responses",
            "value": summary.minimum_source_numeric_responses,
            "unit_or_scale": "numeric source responses",
            "denominator": denominator,
            "note": "Minimum OccurNum among represented ratings.",
        },
        {
            "section": "source_response_evidence",
            "metric": "low_response_token_count",
            "value": summary.low_response_token_count,
            "unit_or_scale": "token occurrences",
            "denominator": denominator,
            "note": "Represented ratings based on fewer than five numeric responses.",
        },
        {
            "section": "coverage",
            "metric": "matched_token_coverage",
            "value": summary.token_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.matched_token_count} of "
                f"{summary.eligible_token_count} eligible tokens"
            ),
            "note": "Unmatched and source-unrated words remain missing.",
        },
        {
            "section": "coverage",
            "metric": "matched_unique_word_coverage",
            "value": summary.unique_type_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.matched_unique_type_count} of "
                f"{summary.eligible_unique_type_count} normalized surface types"
            ),
            "note": "Observed surface types, not lemma types.",
        },
        {
            "section": "coverage",
            "metric": "source_unrated_token_count",
            "value": summary.source_unrated_token_count,
            "unit_or_scale": "token occurrences",
            "denominator": f"{summary.eligible_token_count} eligible tokens",
            "note": "The spelling exists in the source but Rating.Mean is NA.",
        },
        {
            "section": "configuration",
            "metric": "analysis_scope",
            "value": summary.scope_label,
            "unit_or_scale": "configured eligibility scope",
            "denominator": "",
            "note": "",
        },
        {
            "section": "provenance",
            "metric": "resource_sha256",
            "value": result.resource_status.source_sha256,
            "unit_or_scale": "SHA-256",
            "denominator": "",
            "note": result.resource_status.display_name,
        },
        {
            "section": "provenance",
            "metric": "configuration_id",
            "value": result.configuration.configuration_id,
            "unit_or_scale": "stable local identifier",
            "denominator": "",
            "note": "",
        },
        {
            "section": "method_warning",
            "metric": "non_diagnostic_notice",
            "value": (
                "Age-of-acquisition results describe lexical patterns and are "
                "not diagnostic of cognitive impairment or decline."
            ),
            "unit_or_scale": "required warning",
            "denominator": "",
            "note": "",
        },
    ]
    return _csv_bytes(
        [
            "section",
            "metric",
            "value",
            "unit_or_scale",
            "denominator",
            "note",
        ],
        rows,
    )


def export_aoa_distribution_csv(result: AoAAnalysisResult) -> bytes:
    fields = [
        "band_id",
        "label",
        "lower_bound",
        "lower_inclusive",
        "upper_bound",
        "upper_inclusive",
        "token_count",
        "proportion",
        "denominator",
        "note",
    ]
    rows = []
    for band in result.summary.bands:
        row = asdict(band)
        row["denominator"] = (
            f"{result.summary.matched_token_count} matched token occurrences"
        )
        row["note"] = (
            "Configurable VerseVAD orientation band, not a source-paper category."
        )
        rows.append(row)
    return _csv_bytes(fields, rows)


def _group_row(group) -> dict[str, object]:
    stats = group.statistics
    return {
        "scope": group.scope,
        "scope_id": group.scope_id,
        "ordinal": group.ordinal,
        "label": group.label,
        "source_text": group.source_text,
        "eligible_token_count": group.eligible_token_count,
        "matched_token_count": group.matched_token_count,
        "unmatched_token_count": group.unmatched_token_count,
        "token_coverage": group.token_coverage,
        "eligible_unique_type_count": group.eligible_unique_type_count,
        "matched_unique_type_count": group.matched_unique_type_count,
        "unique_type_coverage": group.unique_type_coverage,
        "mean_normative_aoa": stats.mean,
        "median_normative_aoa": stats.median,
        "population_standard_deviation": stats.population_standard_deviation,
        "minimum_normative_aoa": stats.minimum,
        "first_quartile_normative_aoa": stats.first_quartile,
        "third_quartile_normative_aoa": stats.third_quartile,
        "interquartile_range": group.interquartile_range,
        "maximum_normative_aoa": stats.maximum,
    }


GROUP_FIELDS = [
    "scope",
    "scope_id",
    "ordinal",
    "label",
    "source_text",
    "eligible_token_count",
    "matched_token_count",
    "unmatched_token_count",
    "token_coverage",
    "eligible_unique_type_count",
    "matched_unique_type_count",
    "unique_type_coverage",
    "mean_normative_aoa",
    "median_normative_aoa",
    "population_standard_deviation",
    "minimum_normative_aoa",
    "first_quartile_normative_aoa",
    "third_quartile_normative_aoa",
    "interquartile_range",
    "maximum_normative_aoa",
]


def export_aoa_by_structure_csv(result: AoAAnalysisResult) -> bytes:
    return _csv_bytes(
        GROUP_FIELDS,
        (
            _group_row(group)
            for group in (*result.line_summaries, *result.stanza_summaries)
        ),
    )


def export_aoa_by_pos_csv(result: AoAAnalysisResult) -> bytes:
    return _csv_bytes(
        GROUP_FIELDS,
        (_group_row(group) for group in result.part_of_speech_summaries),
    )


def export_aoa_terms_csv(result: AoAAnalysisResult) -> bytes:
    early_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.earliest_acquired_terms, start=1)
    }
    late_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.latest_acquired_terms, start=1)
    }
    fields = [
        "source_term",
        "lookup_form",
        "mean_age",
        "source_rating_standard_deviation",
        "source_occurrence_total",
        "source_numeric_response_count",
        "source_unknown_response_count",
        "source_numeric_response_proportion",
        "matched_token_occurrences",
        "surface_forms",
        "part_of_speech_tags",
        "source_row",
        "earliest_acquired_rank",
        "latest_acquired_rank",
    ]
    rows = []
    for term in result.term_summaries:
        row = asdict(term)
        row["surface_forms"] = " | ".join(term.surface_forms)
        row["part_of_speech_tags"] = " | ".join(term.part_of_speech_tags)
        row["earliest_acquired_rank"] = early_rank.get(term.lookup_form, "")
        row["latest_acquired_rank"] = late_rank.get(term.lookup_form, "")
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_aoa_relationships_csv(result: AoAAnalysisResult) -> bytes:
    fields = [
        "relationship_id",
        "other_module",
        "other_metric",
        "pair_count",
        "coefficient",
        "method",
        "weighting",
        "note",
    ]
    return _csv_bytes(fields, (asdict(item) for item in result.relationships))


def export_aoa_token_audit_csv(result: AoAAnalysisResult) -> bytes:
    fields = [
        "token_id",
        "token_position",
        "surface_form",
        "normalized_form",
        "lemma",
        "normalized_lemma",
        "part_of_speech",
        "line_number",
        "stanza_number",
        "context",
        "is_lexical",
        "is_proper_noun",
        "eligible",
        "included",
        "match_method",
        "matched_source_term",
        "matched_lookup_form",
        "source_row",
        "mean_age",
        "source_rating_standard_deviation",
        "source_occurrence_total",
        "source_numeric_response_count",
        "source_unknown_response_count",
        "source_numeric_response_proportion",
        "source_dunno_value",
        "source_frequency_per_million",
        "reason",
    ]
    rows = []
    for item in result.token_audit:
        row = asdict(item)
        row["match_method"] = item.match_method.value
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_aoa_bundle(
    result: AoAAnalysisResult,
    *,
    text_title: str = "",
) -> dict[str, bytes]:
    bundle = {
        "aoa_summary.csv": export_aoa_summary_csv(result),
        "aoa_distribution.csv": export_aoa_distribution_csv(result),
        "aoa_by_structure.csv": export_aoa_by_structure_csv(result),
        "aoa_by_pos.csv": export_aoa_by_pos_csv(result),
        "aoa_terms.csv": export_aoa_terms_csv(result),
        "aoa_relationships.csv": export_aoa_relationships_csv(result),
        "aoa_token_audit.csv": export_aoa_token_audit_csv(result),
        "aoa_manifest.csv": export_module_manifest_csv(result),
    }
    bundle["aoa_report.docx"] = build_narrative_report_from_summary_csv(
        "aoa",
        bundle["aoa_summary.csv"],
        companion_csv_files=tuple(bundle),
        text_title=text_title,
        text_id=result.module_result.text_id,
        result_id=result.module_result.result_id,
        warnings=tuple(
            warning.message for warning in result.module_result.warnings
        ),
    )
    return bundle
