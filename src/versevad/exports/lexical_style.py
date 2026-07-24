"""Stable UTF-8 CSV and JSON exports for lexical-style results."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from enum import Enum
from typing import Iterable

from versevad.lexical_style import LexicalStyleAnalysisResult


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
    raise TypeError(f"Not JSON serializable: {type(value)!r}")


def export_lexical_style_json(result: LexicalStyleAnalysisResult) -> bytes:
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


def export_lexical_style_summary_csv(
    result: LexicalStyleAnalysisResult,
) -> bytes:
    summary = result.summary
    configuration = result.configuration
    lexical_denominator = (
        f"{summary.lexical_token_count} shared-preprocessing lexical tokens"
    )
    length_denominator = (
        f"{summary.word_length_observation_count} lexical tokens with one or more "
        "Unicode alphabetic characters"
    )
    rows = [
        {
            "section": "direct_observation",
            "metric": "lexical_token_count",
            "value": summary.lexical_token_count,
            "unit_or_scale": "lexical tokens",
            "denominator": "complete preserved text",
            "note": (
                "Uses the shared preprocessing word unit; punctuation and numeric "
                "tokens are excluded."
            ),
        },
        {
            "section": "direct_observation",
            "metric": "normalized_surface_type_count",
            "value": summary.normalized_surface_type_count,
            "unit_or_scale": "normalized observed surface types",
            "denominator": lexical_denominator,
            "note": "No lemma is silently substituted for an observed surface form.",
        },
        {
            "section": "lexical_diversity",
            "metric": "surface_type_token_ratio",
            "value": summary.surface_type_token_ratio,
            "unit_or_scale": "proportion",
            "denominator": lexical_denominator,
            "note": (
                "Descriptive support only; plain type-token ratio is sensitive to "
                "text length."
            ),
        },
        {
            "section": "lexical_diversity",
            "metric": "moving_average_type_token_ratio",
            "value": summary.mattr,
            "unit_or_scale": "mean overlapping-window TTR",
            "denominator": (
                f"{summary.mattr_window_count} overlapping windows of "
                f"{configuration.mattr_window_size} lexical tokens"
            ),
            "note": (
                "Compare only results using the same window and word-unit policy; "
                "missing means the text is shorter than the configured window."
            ),
        },
        {
            "section": "lexical_diversity",
            "metric": "hypergeometric_distribution_diversity",
            "value": summary.hdd,
            "unit_or_scale": "expected distinct-type proportion",
            "denominator": (
                f"without-replacement samples of "
                f"{configuration.hdd_sample_size} lexical tokens"
            ),
            "note": (
                "Compare only results using the same sample size and word-unit "
                "policy; missing means the text is shorter than the configured sample."
            ),
        },
        {
            "section": "lexical_diversity",
            "metric": "measure_of_textual_lexical_diversity",
            "value": summary.mtld,
            "unit_or_scale": "mean lexical-token factor length",
            "denominator": (
                f"forward and reverse factorization at TTR threshold "
                f"{configuration.mtld_threshold}"
            ),
            "note": (
                "A larger value indicates longer token sequences before the "
                "configured diversity threshold is crossed; short texts remain "
                "methodologically fragile."
            ),
        },
        {
            "section": "word_length",
            "metric": "mean_alphabetic_characters_per_lexical_token",
            "value": summary.mean_alphabetic_characters_per_token,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "Punctuation marks inside a surface token are not characters here.",
        },
        {
            "section": "word_length",
            "metric": "median_alphabetic_characters_per_lexical_token",
            "value": summary.median_alphabetic_characters_per_token,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "",
        },
        {
            "section": "word_length",
            "metric": "population_standard_deviation_alphabetic_characters",
            "value": summary.population_standard_deviation_alphabetic_characters,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "Population, not sample, standard deviation.",
        },
        {
            "section": "word_length",
            "metric": "minimum_alphabetic_characters",
            "value": summary.minimum_alphabetic_characters,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "",
        },
        {
            "section": "word_length",
            "metric": "first_quartile_alphabetic_characters",
            "value": summary.first_quartile_alphabetic_characters,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "Inclusive quartile method.",
        },
        {
            "section": "word_length",
            "metric": "third_quartile_alphabetic_characters",
            "value": summary.third_quartile_alphabetic_characters,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "Inclusive quartile method.",
        },
        {
            "section": "word_length",
            "metric": "maximum_alphabetic_characters",
            "value": summary.maximum_alphabetic_characters,
            "unit_or_scale": "Unicode alphabetic characters",
            "denominator": length_denominator,
            "note": "",
        },
        {
            "section": "structural_word_counts",
            "metric": "line_word_count_mean",
            "value": summary.nonblank_line_word_count_statistics.mean,
            "unit_or_scale": "lexical tokens per nonblank physical line",
            "denominator": f"{summary.nonblank_line_count} nonblank physical lines",
            "note": "Blank structural separator lines remain in the line export.",
        },
        {
            "section": "structural_word_counts",
            "metric": "line_word_count_median",
            "value": summary.nonblank_line_word_count_statistics.median,
            "unit_or_scale": "lexical tokens per nonblank physical line",
            "denominator": f"{summary.nonblank_line_count} nonblank physical lines",
            "note": "",
        },
        {
            "section": "structural_word_counts",
            "metric": "stanza_word_count_mean",
            "value": summary.stanza_word_count_statistics.mean,
            "unit_or_scale": "lexical tokens per stanza",
            "denominator": f"{summary.stanza_count} stanzas",
            "note": "",
        },
        {
            "section": "structural_word_counts",
            "metric": "stanza_word_count_median",
            "value": summary.stanza_word_count_statistics.median,
            "unit_or_scale": "lexical tokens per stanza",
            "denominator": f"{summary.stanza_count} stanzas",
            "note": "",
        },
        {
            "section": "configuration",
            "metric": "configuration_id",
            "value": configuration.configuration_id,
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


def export_lexical_style_word_lengths_csv(
    result: LexicalStyleAnalysisResult,
) -> bytes:
    rows = (
        {
            **asdict(item),
            "denominator": (
                f"{result.summary.word_length_observation_count} lexical tokens "
                "with alphabetic-character lengths"
            ),
        }
        for item in result.word_length_distribution
    )
    return _csv_bytes(
        [
            "alphabetic_character_count",
            "token_count",
            "token_proportion",
            "denominator",
        ],
        rows,
    )


STRUCTURAL_FIELDS = [
    "scope",
    "scope_id",
    "ordinal",
    "label",
    "source_text",
    "is_blank",
    "line_count",
    "word_count",
    "normalized_surface_type_count",
    "surface_type_token_ratio",
    "mean_alphabetic_characters_per_token",
    "median_alphabetic_characters_per_token",
]


def export_lexical_style_lines_csv(
    result: LexicalStyleAnalysisResult,
) -> bytes:
    return _csv_bytes(
        STRUCTURAL_FIELDS,
        (asdict(item) for item in result.line_summaries),
    )


def export_lexical_style_stanzas_csv(
    result: LexicalStyleAnalysisResult,
) -> bytes:
    return _csv_bytes(
        STRUCTURAL_FIELDS,
        (asdict(item) for item in result.stanza_summaries),
    )


def export_lexical_style_token_audit_csv(
    result: LexicalStyleAnalysisResult,
) -> bytes:
    fields = [
        "token_id",
        "token_position",
        "surface_form",
        "normalized_surface_type",
        "lemma",
        "normalized_lemma",
        "part_of_speech",
        "line_number",
        "stanza_number",
        "character_start",
        "character_end",
        "included",
        "alphabetic_character_count",
        "reason",
    ]
    return _csv_bytes(fields, (asdict(item) for item in result.token_audit))


def export_lexical_style_bundle(
    result: LexicalStyleAnalysisResult,
) -> dict[str, bytes]:
    return {
        "lexical_style_summary.csv": export_lexical_style_summary_csv(result),
        "lexical_style_word_lengths.csv": (
            export_lexical_style_word_lengths_csv(result)
        ),
        "lexical_style_lines.csv": export_lexical_style_lines_csv(result),
        "lexical_style_stanzas.csv": export_lexical_style_stanzas_csv(result),
        "lexical_style_token_audit.csv": (
            export_lexical_style_token_audit_csv(result)
        ),
        "lexical_style_result.json": export_lexical_style_json(result),
    }
