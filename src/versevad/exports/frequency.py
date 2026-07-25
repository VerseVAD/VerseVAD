"""Stable UTF-8 CSV and narrative Word exports for SUBTLEX-US results."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict
from typing import Iterable

from versevad.exports.docx_report import build_narrative_report_from_summary_csv
from versevad.exports.module_manifest import export_module_manifest_csv
from versevad.lexical_semantic.frequency import FrequencyAnalysisResult


def _csv_bytes(
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def export_frequency_summary_csv(result: FrequencyAnalysisResult) -> bytes:
    summary = result.summary
    stats = summary.statistics
    denominator = f"{summary.matched_token_count} matched eligible token occurrences"
    rows = [
        {
            "section": "descriptive_statistics",
            "metric": "median_zipf",
            "value": stats.median,
            "unit_or_scale": "SUBTLEX-US Zipf",
            "denominator": denominator,
            "note": "Primary token-weighted summary; the scale is logarithmic.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "mean_zipf",
            "value": stats.mean,
            "unit_or_scale": "SUBTLEX-US Zipf",
            "denominator": denominator,
            "note": "Rare outliers can pull this mean downward.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "population_standard_deviation",
            "value": stats.population_standard_deviation,
            "unit_or_scale": "Zipf points",
            "denominator": denominator,
            "note": "Population, not sample, standard deviation.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "minimum_zipf",
            "value": stats.minimum,
            "unit_or_scale": "SUBTLEX-US Zipf",
            "denominator": denominator,
            "note": "",
        },
        {
            "section": "descriptive_statistics",
            "metric": "first_quartile_zipf",
            "value": stats.first_quartile,
            "unit_or_scale": "SUBTLEX-US Zipf",
            "denominator": denominator,
            "note": "Inclusive quartile method.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "third_quartile_zipf",
            "value": stats.third_quartile,
            "unit_or_scale": "SUBTLEX-US Zipf",
            "denominator": denominator,
            "note": "Inclusive quartile method.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "interquartile_range",
            "value": summary.interquartile_range,
            "unit_or_scale": "Zipf points",
            "denominator": denominator,
            "note": "Third quartile minus first quartile.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "maximum_zipf",
            "value": stats.maximum,
            "unit_or_scale": "SUBTLEX-US Zipf",
            "denominator": denominator,
            "note": "",
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
            "note": "Unmatched words remain missing rather than Zipf zero.",
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


def export_frequency_distribution_csv(
    result: FrequencyAnalysisResult,
) -> bytes:
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
            "Configurable VerseVAD orientation band, not a universal category."
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
        "median_zipf": stats.median,
        "mean_zipf": stats.mean,
        "population_standard_deviation": stats.population_standard_deviation,
        "minimum_zipf": stats.minimum,
        "first_quartile_zipf": stats.first_quartile,
        "third_quartile_zipf": stats.third_quartile,
        "interquartile_range": group.interquartile_range,
        "maximum_zipf": stats.maximum,
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
    "median_zipf",
    "mean_zipf",
    "population_standard_deviation",
    "minimum_zipf",
    "first_quartile_zipf",
    "third_quartile_zipf",
    "interquartile_range",
    "maximum_zipf",
]


def export_frequency_by_structure_csv(
    result: FrequencyAnalysisResult,
) -> bytes:
    return _csv_bytes(
        GROUP_FIELDS,
        (
            _group_row(group)
            for group in (*result.line_summaries, *result.stanza_summaries)
        ),
    )


def export_frequency_by_pos_csv(result: FrequencyAnalysisResult) -> bytes:
    return _csv_bytes(
        GROUP_FIELDS,
        (_group_row(group) for group in result.part_of_speech_summaries),
    )


def export_frequency_terms_csv(result: FrequencyAnalysisResult) -> bytes:
    low_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.lowest_frequency_terms, start=1)
    }
    high_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.highest_frequency_terms, start=1)
    }
    tail_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.rare_word_tail, start=1)
    }
    fields = [
        "source_term",
        "lookup_form",
        "zipf_value",
        "frequency_count",
        "frequency_per_million",
        "contextual_diversity_count",
        "contextual_diversity_percent",
        "matched_token_occurrences",
        "surface_forms",
        "part_of_speech_tags",
        "source_row",
        "dominant_source_pos",
        "lowest_frequency_rank",
        "highest_frequency_rank",
        "rare_tail_rank",
    ]
    rows = []
    for term in result.term_summaries:
        row = asdict(term)
        row["surface_forms"] = " | ".join(term.surface_forms)
        row["part_of_speech_tags"] = " | ".join(term.part_of_speech_tags)
        row["lowest_frequency_rank"] = low_rank.get(term.lookup_form, "")
        row["highest_frequency_rank"] = high_rank.get(term.lookup_form, "")
        row["rare_tail_rank"] = tail_rank.get(term.lookup_form, "")
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_frequency_token_audit_csv(
    result: FrequencyAnalysisResult,
) -> bytes:
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
        "zipf_value",
        "frequency_count",
        "frequency_per_million",
        "contextual_diversity_count",
        "contextual_diversity_percent",
        "lowercase_frequency_count",
        "lowercase_contextual_diversity_count",
        "dominant_source_pos",
        "dominant_source_pos_frequency",
        "dominant_source_pos_proportion",
        "reason",
    ]
    rows = []
    for item in result.token_audit:
        row = asdict(item)
        row["match_method"] = item.match_method.value
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_frequency_bundle(
    result: FrequencyAnalysisResult,
    *,
    text_title: str = "",
) -> dict[str, bytes]:
    bundle = {
        "frequency_summary.csv": export_frequency_summary_csv(result),
        "frequency_distribution.csv": export_frequency_distribution_csv(result),
        "frequency_by_structure.csv": export_frequency_by_structure_csv(result),
        "frequency_by_pos.csv": export_frequency_by_pos_csv(result),
        "frequency_terms.csv": export_frequency_terms_csv(result),
        "frequency_token_audit.csv": export_frequency_token_audit_csv(result),
        "frequency_manifest.csv": export_module_manifest_csv(result),
    }
    bundle["frequency_report.docx"] = build_narrative_report_from_summary_csv(
        "frequency",
        bundle["frequency_summary.csv"],
        companion_csv_files=tuple(bundle),
        text_title=text_title,
        text_id=result.module_result.text_id,
        result_id=result.module_result.result_id,
        warnings=tuple(
            warning.message for warning in result.module_result.warnings
        ),
    )
    return bundle
