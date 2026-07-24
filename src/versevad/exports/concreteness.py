"""Stable UTF-8 CSV and JSON exports for concreteness results."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Iterable

from versevad.lexical_semantic.concreteness import ConcretenessAnalysisResult


def _csv_bytes(
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Not JSON serializable: {type(value)!r}")


def export_concreteness_json(result: ConcretenessAnalysisResult) -> bytes:
    return (
        json.dumps(
            asdict(result),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            default=_json_default,
        )
        + "\n"
    ).encode("utf-8")


def export_concreteness_summary_csv(
    result: ConcretenessAnalysisResult,
) -> bytes:
    summary = result.summary
    statistics = summary.statistics
    rows = [
        {
            "section": "descriptive_statistics",
            "metric": "mean",
            "value": statistics.mean,
            "unit_or_scale": "source 1-5",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "Population summary of matched normative ratings.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "median",
            "value": statistics.median,
            "unit_or_scale": "source 1-5",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "Population summary of matched normative ratings.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "population_standard_deviation",
            "value": statistics.population_standard_deviation,
            "unit_or_scale": "source-scale points",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "Population, not sample, standard deviation.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "minimum",
            "value": statistics.minimum,
            "unit_or_scale": "source 1-5",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "",
        },
        {
            "section": "descriptive_statistics",
            "metric": "first_quartile",
            "value": statistics.first_quartile,
            "unit_or_scale": "source 1-5",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "Inclusive quartile method.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "third_quartile",
            "value": statistics.third_quartile,
            "unit_or_scale": "source 1-5",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "Inclusive quartile method.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "interquartile_range",
            "value": summary.interquartile_range,
            "unit_or_scale": "source-scale points",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "Third quartile minus first quartile.",
        },
        {
            "section": "descriptive_statistics",
            "metric": "maximum",
            "value": statistics.maximum,
            "unit_or_scale": "source 1-5",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": "",
        },
        {
            "section": "coverage",
            "metric": "rated_token_coverage",
            "value": summary.token_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.rated_token_count} of "
                f"{summary.eligible_token_count} eligible tokens"
            ),
            "note": "Unmatched tokens remain missing rather than neutral.",
        },
        {
            "section": "coverage",
            "metric": "rated_unique_word_coverage",
            "value": summary.unique_type_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.rated_unique_type_count} of "
                f"{summary.eligible_unique_type_count} unique normalized "
                "surface types"
            ),
            "note": "The denominator is observed surface types, not lemma types.",
        },
        {
            "section": "configured_bands",
            "metric": "highly_concrete_proportion",
            "value": summary.highly_concrete_proportion,
            "unit_or_scale": "proportion",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": (
                f"VerseVAD orientation band: rating >= "
                f"{summary.highly_concrete_min:g}; not a source-paper category."
            ),
        },
        {
            "section": "configured_bands",
            "metric": "highly_abstract_proportion",
            "value": summary.highly_abstract_proportion,
            "unit_or_scale": "proportion",
            "denominator": f"{summary.rated_token_count} rated token occurrences",
            "note": (
                f"VerseVAD orientation band: rating <= "
                f"{summary.highly_abstract_max:g}; not a source-paper category."
            ),
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


def _group_row(group) -> dict[str, object]:
    statistics = group.statistics
    return {
        "scope": group.scope,
        "scope_id": group.scope_id,
        "ordinal": group.ordinal,
        "label": group.label,
        "source_text": group.source_text,
        "eligible_token_count": group.eligible_token_count,
        "rated_token_count": group.rated_token_count,
        "unmatched_token_count": group.unmatched_token_count,
        "token_coverage": group.token_coverage,
        "eligible_unique_type_count": group.eligible_unique_type_count,
        "rated_unique_type_count": group.rated_unique_type_count,
        "unique_type_coverage": group.unique_type_coverage,
        "mean": statistics.mean,
        "median": statistics.median,
        "population_standard_deviation": statistics.population_standard_deviation,
        "minimum": statistics.minimum,
        "first_quartile": statistics.first_quartile,
        "third_quartile": statistics.third_quartile,
        "interquartile_range": group.interquartile_range,
        "maximum": statistics.maximum,
    }


GROUP_FIELDS = [
    "scope",
    "scope_id",
    "ordinal",
    "label",
    "source_text",
    "eligible_token_count",
    "rated_token_count",
    "unmatched_token_count",
    "token_coverage",
    "eligible_unique_type_count",
    "rated_unique_type_count",
    "unique_type_coverage",
    "mean",
    "median",
    "population_standard_deviation",
    "minimum",
    "first_quartile",
    "third_quartile",
    "interquartile_range",
    "maximum",
]


def export_concreteness_by_structure_csv(
    result: ConcretenessAnalysisResult,
) -> bytes:
    return _csv_bytes(
        GROUP_FIELDS,
        (
            _group_row(group)
            for group in (*result.line_summaries, *result.stanza_summaries)
        ),
    )


def export_concreteness_by_pos_csv(
    result: ConcretenessAnalysisResult,
) -> bytes:
    return _csv_bytes(
        GROUP_FIELDS,
        (_group_row(group) for group in result.part_of_speech_summaries),
    )


def export_concreteness_terms_csv(
    result: ConcretenessAnalysisResult,
) -> bytes:
    concrete_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.most_concrete_terms, start=1)
    }
    abstract_rank = {
        term.lookup_form: index
        for index, term in enumerate(result.most_abstract_terms, start=1)
    }
    fields = [
        "source_term",
        "lookup_form",
        "rating",
        "source_rating_standard_deviation",
        "rated_token_occurrences",
        "expression_occurrences",
        "surface_forms",
        "part_of_speech_tags",
        "source_row",
        "source_is_multiword",
        "source_percent_known",
        "most_concrete_rank",
        "most_abstract_rank",
    ]
    rows = []
    for term in result.term_summaries:
        row = asdict(term)
        row["surface_forms"] = " | ".join(term.surface_forms)
        row["part_of_speech_tags"] = " | ".join(term.part_of_speech_tags)
        row["most_concrete_rank"] = concrete_rank.get(term.lookup_form, "")
        row["most_abstract_rank"] = abstract_rank.get(term.lookup_form, "")
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_concreteness_token_audit_csv(
    result: ConcretenessAnalysisResult,
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
        "match_group_id",
        "match_group_token_ids",
        "matched_source_term",
        "matched_lookup_form",
        "source_row",
        "source_is_multiword",
        "rating",
        "source_rating_standard_deviation",
        "source_unknown_count",
        "source_rater_count",
        "source_percent_known",
        "source_subtlex_count",
        "reason",
    ]
    rows = []
    for item in result.token_audit:
        row = asdict(item)
        row["match_method"] = item.match_method.value
        row["match_group_token_ids"] = " | ".join(item.match_group_token_ids)
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_concreteness_bundle(
    result: ConcretenessAnalysisResult,
) -> dict[str, bytes]:
    return {
        "concreteness_summary.csv": export_concreteness_summary_csv(result),
        "concreteness_by_structure.csv": (
            export_concreteness_by_structure_csv(result)
        ),
        "concreteness_by_pos.csv": export_concreteness_by_pos_csv(result),
        "concreteness_terms.csv": export_concreteness_terms_csv(result),
        "concreteness_token_audit.csv": (
            export_concreteness_token_audit_csv(result)
        ),
        "concreteness_result.json": export_concreteness_json(result),
    }
