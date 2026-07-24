"""Stable UTF-8 CSV and JSON exports for Stage 5 pronunciation evidence."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Iterable

from versevad.prosody.pronunciation import PronunciationAnalysisResult


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


def export_pronunciation_json(result: PronunciationAnalysisResult) -> bytes:
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


def export_pronunciation_summary_csv(
    result: PronunciationAnalysisResult,
) -> bytes:
    summary = result.summary
    word_stats = summary.syllables_per_resolved_word
    line_stats = summary.syllables_per_complete_line
    rows = [
        {
            "section": "syllables",
            "metric": "mean_syllables_per_resolved_word",
            "value": word_stats.mean,
            "unit_or_scale": "syllables per resolved lexical token",
            "denominator": f"{summary.resolved_token_count} resolved tokens",
            "note": "",
        },
        {
            "section": "syllables",
            "metric": "median_syllables_per_resolved_word",
            "value": word_stats.median,
            "unit_or_scale": "syllables per resolved lexical token",
            "denominator": f"{summary.resolved_token_count} resolved tokens",
            "note": "",
        },
        {
            "section": "syllables",
            "metric": "mean_syllables_per_complete_line",
            "value": line_stats.mean,
            "unit_or_scale": "syllables per complete physical line",
            "denominator": f"{summary.complete_line_count} complete lines",
            "note": "Incomplete lines remain missing rather than undercounted.",
        },
        {
            "section": "syllables",
            "metric": "median_syllables_per_complete_line",
            "value": line_stats.median,
            "unit_or_scale": "syllables per complete physical line",
            "denominator": f"{summary.complete_line_count} complete lines",
            "note": "Incomplete lines remain missing rather than undercounted.",
        },
        {
            "section": "lexical_stress",
            "metric": "stress_density",
            "value": summary.stress_density,
            "unit_or_scale": "proportion of resolved syllables",
            "denominator": f"{summary.total_resolved_syllables} resolved syllables",
            "note": (
                "Primary and secondary lexical stress combined; this is not "
                "performed rhythm or meter."
            ),
        },
        {
            "section": "coverage",
            "metric": "resolved_token_coverage",
            "value": summary.token_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.resolved_token_count} of "
                f"{summary.eligible_token_count} eligible lexical tokens"
            ),
            "note": "Unmatched and materially ambiguous tokens remain missing.",
        },
        {
            "section": "coverage",
            "metric": "resolved_unique_type_coverage",
            "value": summary.unique_type_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.resolved_unique_type_count} of "
                f"{summary.eligible_unique_type_count} normalized observed forms"
            ),
            "note": "Observed forms, not lemmas.",
        },
        {
            "section": "coverage",
            "metric": "complete_line_coverage",
            "value": summary.complete_line_coverage,
            "unit_or_scale": "proportion",
            "denominator": (
                f"{summary.complete_line_count} of "
                f"{summary.eligible_line_count} lines containing lexical tokens"
            ),
            "note": "A complete line has every eligible lexical token resolved.",
        },
        {
            "section": "ambiguity",
            "metric": "ambiguous_dictionary_tokens",
            "value": summary.ambiguous_token_count,
            "unit_or_scale": "token occurrences",
            "denominator": f"{summary.eligible_token_count} eligible tokens",
            "note": "No dictionary alternative was silently selected.",
        },
        {
            "section": "ambiguity",
            "metric": "out_of_dictionary_tokens",
            "value": summary.unmatched_token_count,
            "unit_or_scale": "token occurrences",
            "denominator": f"{summary.eligible_token_count} eligible tokens",
            "note": "No fallback pronunciation was fabricated.",
        },
        {
            "section": "configuration",
            "metric": "configuration_id",
            "value": result.configuration.configuration_id,
            "unit_or_scale": "stable local identifier",
            "denominator": "",
            "note": "",
        },
        {
            "section": "method_warning",
            "metric": "scope_notice",
            "value": (
                "Dictionary-based North American pronunciation, syllable, and "
                "lexical-stress evidence; not meter, rhyme, or performed scansion."
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


def export_pronunciation_lines_csv(
    result: PronunciationAnalysisResult,
) -> bytes:
    fields = [
        "line_id",
        "line_number",
        "stanza_number",
        "source_text",
        "eligible_token_count",
        "resolved_token_count",
        "ambiguous_token_count",
        "unmatched_token_count",
        "source_without_marked_vowel_count",
        "resolution_coverage",
        "is_complete",
        "syllable_count",
        "lexical_stress_sequence",
        "compact_stress_sequence",
        "primary_stress_count",
        "secondary_stress_count",
        "unstressed_syllable_count",
        "stress_density",
    ]
    return _csv_bytes(fields, (asdict(item) for item in result.line_summaries))


def export_pronunciation_types_csv(
    result: PronunciationAnalysisResult,
) -> bytes:
    fields = [
        "lookup_form",
        "surface_forms",
        "token_occurrences",
        "resolved_occurrences",
        "statuses",
        "dictionary_candidate_count",
        "candidate_phones",
        "resolved_syllable_count",
        "resolved_stress_pattern",
    ]
    rows = []
    for item in result.type_summaries:
        row = asdict(item)
        row["surface_forms"] = " | ".join(item.surface_forms)
        row["statuses"] = " | ".join(item.statuses)
        row["candidate_phones"] = " | ".join(item.candidate_phones)
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_pronunciation_token_audit_csv(
    result: PronunciationAnalysisResult,
) -> bytes:
    fields = [
        "token_id",
        "token_position",
        "surface_form",
        "normalized_form",
        "lookup_form",
        "part_of_speech",
        "line_number",
        "stanza_number",
        "context",
        "is_lexical",
        "is_proper_noun",
        "eligible",
        "resolved",
        "status",
        "dictionary_source_term",
        "dictionary_candidate_count",
        "dictionary_candidate_phones",
        "dictionary_candidate_stresses",
        "dictionary_candidate_syllable_counts",
        "dictionary_source_lines",
        "resolved_phones",
        "resolved_stress_pattern",
        "resolved_syllable_count",
        "confidence_label",
        "override_note",
        "reason",
    ]
    rows = []
    for item in result.token_audit:
        row = asdict(item)
        row["status"] = item.status.value
        row["dictionary_candidate_phones"] = " | ".join(
            item.dictionary_candidate_phones
        )
        row["dictionary_candidate_stresses"] = " | ".join(
            item.dictionary_candidate_stresses
        )
        row["dictionary_candidate_syllable_counts"] = " | ".join(
            str(value) for value in item.dictionary_candidate_syllable_counts
        )
        row["dictionary_source_lines"] = " | ".join(
            str(value) for value in item.dictionary_source_lines
        )
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_pronunciation_bundle(
    result: PronunciationAnalysisResult,
) -> dict[str, bytes]:
    return {
        "pronunciation_summary.csv": export_pronunciation_summary_csv(result),
        "pronunciation_lines.csv": export_pronunciation_lines_csv(result),
        "pronunciation_types.csv": export_pronunciation_types_csv(result),
        "pronunciation_token_audit.csv": export_pronunciation_token_audit_csv(result),
        "pronunciation_result.json": export_pronunciation_json(result),
    }
