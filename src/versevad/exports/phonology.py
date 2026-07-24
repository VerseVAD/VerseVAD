"""Stable UTF-8 CSV and JSON exports for Stage 7 rhyme evidence."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Iterable

from versevad.phonology import PhonologicalAnalysisResult


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


def export_phonological_json(result: PhonologicalAnalysisResult) -> bytes:
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


def export_phonological_summary_csv(
    result: PhonologicalAnalysisResult,
) -> bytes:
    summary = result.summary
    rows = [
        {
            "section": section,
            "metric": metric,
            "value": value,
            "unit_or_scale": unit,
            "denominator": denominator,
            "note": note,
        }
        for section, metric, value, unit, denominator, note in (
            (
                "end_rhyme",
                "whole_poem_rhyme_scheme",
                summary.whole_poem_rhyme_scheme,
                "perfect/identical rhyme labels; x unrhymed; ? unresolved",
                f"{summary.eligible_line_count} eligible line endings",
                "Slant and eye evidence do not create scheme groups.",
            ),
            (
                "end_rhyme",
                "rhyme_density",
                summary.rhyme_density,
                "proportion",
                f"{summary.analyzable_ending_count} analyzable line endings",
                "Share of analyzable lines in a within-stanza exact rhyme pair.",
            ),
            (
                "coverage",
                "line_ending_coverage",
                summary.ending_coverage,
                "proportion",
                (
                    f"{summary.analyzable_ending_count} of "
                    f"{summary.eligible_line_count} eligible line endings"
                ),
                "Unresolved endings receive no rhyme label or zero score.",
            ),
            (
                "rhyme_pairs",
                "perfect_rhyme_pair_count",
                summary.perfect_rhyme_pair_count,
                "within-stanza ending pairs",
                "",
                "",
            ),
            (
                "rhyme_pairs",
                "identical_rhyme_pair_count",
                summary.identical_rhyme_pair_count,
                "within-stanza ending pairs",
                "",
                "Repeated endings and homophonic complete endings remain labeled.",
            ),
            (
                "rhyme_pairs",
                "slant_rhyme_pair_count",
                summary.slant_rhyme_pair_count,
                "within-stanza ending pairs",
                "",
                (
                    f"Conservative minimum similarity at or above "
                    f"{result.configuration.slant_rhyme_threshold}."
                ),
            ),
            (
                "rhyme_pairs",
                "eye_rhyme_pair_count",
                summary.eye_rhyme_pair_count,
                "within-stanza orthographic pairs",
                "",
                "Orthographic evidence remains separate from phonetic rhyme.",
            ),
            (
                "internal_rhyme",
                "internal_rhyme_pair_count",
                summary.internal_rhyme_pair_count,
                "within-line exact rhyme pairs",
                "",
                "",
            ),
            (
                "sound_patterns",
                "alliteration_density",
                summary.alliteration_density,
                "repeated initial-consonant occurrences / supported initials",
                "all supported initial consonant occurrences",
                "Uses phonemes, not letters.",
            ),
            (
                "sound_patterns",
                "assonance_density",
                summary.assonance_density,
                "repeated stressed-vowel occurrences / supported stressed vowels",
                "all supported stressed vowel occurrences",
                "",
            ),
            (
                "sound_patterns",
                "consonance_density",
                summary.consonance_density,
                "repeated consonant occurrences / supported consonants",
                "all supported consonant occurrences",
                "",
            ),
            (
                "configuration",
                "configuration_id",
                result.configuration.configuration_id,
                "stable local identifier",
                "",
                "",
            ),
        )
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


def export_rhyme_stanzas_csv(result: PhonologicalAnalysisResult) -> bytes:
    fields = [
        "stanza_number",
        "eligible_line_count",
        "analyzable_ending_count",
        "ending_coverage",
        "rhyme_scheme",
        "perfect_or_identical_pair_count",
        "slant_pair_count",
        "rhymed_line_count",
        "rhyme_density",
    ]
    return _csv_bytes(fields, (asdict(item) for item in result.stanza_summaries))


def export_rhyme_lines_csv(result: PhonologicalAnalysisResult) -> bytes:
    fields = [
        "line_id",
        "line_number",
        "stanza_number",
        "source_text",
        "status",
        "eligible_token_count",
        "phonologically_supported_token_count",
        "ending_token_id",
        "ending_surface_form",
        "ending_lookup_form",
        "ending_pronunciation_status",
        "ending_candidate_phones",
        "ending_rhyme_parts",
        "resolved_rhyme_part",
        "stressed_vowel",
        "ending_shape",
        "poem_scheme_label",
        "stanza_scheme_label",
        "rhyme_group_id",
        "is_refrain",
        "refrain_group_id",
        "internal_rhyme_count",
        "initial_consonant_sequence",
        "repeated_initial_consonants",
        "stressed_vowel_sequence",
        "repeated_stressed_vowels",
        "consonant_sequence",
        "repeated_consonants",
        "alliteration_density",
        "assonance_density",
        "consonance_density",
        "reason",
    ]
    rows = []
    for item in result.line_results:
        row = asdict(item)
        row["status"] = item.status.value
        row["ending_candidate_phones"] = " | ".join(
            item.ending_candidate_phones
        )
        row["ending_rhyme_parts"] = " | ".join(item.ending_rhyme_parts)
        row["internal_rhyme_count"] = len(item.internal_rhyme_matches)
        row["initial_consonant_sequence"] = " ".join(
            item.initial_consonant_sequence
        )
        row["repeated_initial_consonants"] = " ".join(
            item.repeated_initial_consonants
        )
        row["stressed_vowel_sequence"] = " ".join(
            item.stressed_vowel_sequence
        )
        row["repeated_stressed_vowels"] = " ".join(
            item.repeated_stressed_vowels
        )
        row["consonant_sequence"] = " ".join(item.consonant_sequence)
        row["repeated_consonants"] = " ".join(item.repeated_consonants)
        row.pop("internal_rhyme_matches")
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_rhyme_pairs_csv(result: PhonologicalAnalysisResult) -> bytes:
    fields = [
        "pair_id",
        "stanza_number",
        "first_line_id",
        "first_line_number",
        "first_word",
        "second_line_id",
        "second_line_number",
        "second_word",
        "relationship",
        "rhyme_types",
        "similarity_score",
        "maximum_similarity_score",
        "stressed_vowel_similarity",
        "final_consonant_similarity",
        "phoneme_edit_similarity",
        "stress_alignment_similarity",
        "syllable_count_similarity",
        "is_eye_rhyme",
        "orthographic_rime",
        "confidence_label",
        "note",
    ]
    rows = []
    for item in result.pair_results:
        row = asdict(item)
        row["rhyme_types"] = " | ".join(item.rhyme_types)
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_internal_rhymes_csv(result: PhonologicalAnalysisResult) -> bytes:
    fields = [
        "line_id",
        "line_number",
        "stanza_number",
        "first_token_id",
        "first_word",
        "second_token_id",
        "second_word",
        "rhyme_part",
        "relationship",
    ]
    rows = []
    for line in result.line_results:
        for item in line.internal_rhyme_matches:
            row = asdict(item)
            row.update(
                {
                    "line_id": line.line_id,
                    "line_number": line.line_number,
                    "stanza_number": line.stanza_number,
                }
            )
            rows.append(row)
    return _csv_bytes(fields, rows)


def export_phonological_sounds_csv(
    result: PhonologicalAnalysisResult,
) -> bytes:
    fields = [
        "category",
        "sound",
        "occurrence_count",
        "line_count",
        "share_of_category_occurrences",
    ]
    return _csv_bytes(fields, (asdict(item) for item in result.sound_families))


def export_phonological_bundle(
    result: PhonologicalAnalysisResult,
) -> dict[str, bytes]:
    return {
        "rhyme_summary.csv": export_phonological_summary_csv(result),
        "rhyme_stanzas.csv": export_rhyme_stanzas_csv(result),
        "rhyme_lines.csv": export_rhyme_lines_csv(result),
        "rhyme_pairs.csv": export_rhyme_pairs_csv(result),
        "rhyme_internal.csv": export_internal_rhymes_csv(result),
        "phonological_sounds.csv": export_phonological_sounds_csv(result),
        "rhyme_result.json": export_phonological_json(result),
    }
