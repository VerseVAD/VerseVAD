"""Stable UTF-8 CSV and JSON exports for Stage 6 meter evidence."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from typing import Iterable

from versevad.prosody.meter import CandidateMeterFit, MeterAnalysisResult


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


def export_meter_json(result: MeterAnalysisResult) -> bytes:
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


def export_meter_summary_csv(result: MeterAnalysisResult) -> bytes:
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
                "nearest_candidate",
                "candidate_kind",
                summary.closest_candidate_kind,
                "structural comparison kind",
                f"{summary.analyzable_line_count} analyzable physical lines",
                "A fixed line template or a stanza-aware alternating scheme.",
            ),
            (
                "nearest_candidate",
                "candidate_label",
                summary.closest_candidate_label,
                "configured candidate label",
                f"{summary.analyzable_line_count} analyzable physical lines",
                "Nearest configured candidate; not a definitive classification.",
            ),
            (
                "nearest_candidate",
                "mean_fit",
                summary.whole_poem_mean_fit,
                "normalized configured alignment similarity 0-1",
                f"{summary.analyzable_line_count} analyzable physical lines",
                "Fit is not a probability.",
            ),
            (
                "nearest_candidate",
                "matching_line_proportion",
                summary.matching_line_proportion,
                "proportion",
                f"{summary.analyzable_line_count} analyzable physical lines",
                (
                    f"Line match threshold: "
                    f"{result.configuration.line_match_threshold}."
                ),
            ),
            (
                "nearest_candidate",
                "rule_based_confidence",
                summary.candidate_confidence,
                "configured category",
                f"{summary.analyzable_line_count} analyzable physical lines",
                summary.confidence_explanation,
            ),
            (
                "coverage",
                "analyzable_line_coverage",
                summary.line_coverage,
                "proportion",
                (
                    f"{summary.analyzable_line_count} of "
                    f"{summary.eligible_line_count} eligible physical lines"
                ),
                "Unanalyzable lines receive no fabricated fit.",
            ),
            (
                "common_meter",
                "mean_fit",
                summary.common_meter_mean_fit,
                "normalized stanza-aware alignment similarity 0-1",
                f"{summary.analyzable_line_count} analyzable physical lines",
                (
                    "Stanza-phase comparison against iambic "
                    "tetrameter/trimeter/tetrameter/trimeter."
                ),
            ),
            (
                "common_meter",
                "matching_line_proportion",
                summary.common_meter_matching_line_proportion,
                "proportion",
                f"{summary.analyzable_line_count} analyzable physical lines",
                "The 4-3-4-3 cycle restarts at each stanza.",
            ),
            (
                "common_meter",
                "complete_stanza_coverage",
                summary.common_meter_complete_stanza_coverage,
                "proportion",
                "eligible stanzas",
                (
                    "Only a complete four-line stanza can support selection of "
                    "common meter as the nearest poem-level scheme."
                ),
            ),
            (
                "deviations",
                "common_deviation",
                summary.common_deviation,
                "alignment evidence label",
                f"{summary.analyzable_line_count} selected line alignments",
                "Describes the selected alignment paths, not performed scansion.",
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


def export_meter_candidates_csv(result: MeterAnalysisResult) -> bytes:
    fields = [
        "rank",
        "pattern",
        "foot_count",
        "foot_count_name",
        "label",
        "analyzed_line_count",
        "mean_fit",
        "median_fit",
        "fit_variability",
        "matching_line_count",
        "matching_line_proportion",
    ]
    rows = []
    for item in result.candidate_summaries:
        row = asdict(item)
        row["pattern"] = item.pattern.value
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_meter_schemes_csv(result: MeterAnalysisResult) -> bytes:
    fields = [
        "rank",
        "scheme_id",
        "label",
        "pattern",
        "foot_count_cycle",
        "structural_unit",
        "eligible_line_count",
        "analyzed_line_count",
        "line_coverage",
        "mean_fit",
        "median_fit",
        "fit_variability",
        "matching_line_count",
        "matching_line_proportion",
        "eligible_stanza_count",
        "complete_stanza_count",
        "complete_stanza_coverage",
    ]
    rows = []
    for item in result.scheme_summaries:
        row = asdict(item)
        row["pattern"] = item.pattern.value
        row["foot_count_cycle"] = "-".join(
            str(value) for value in item.foot_count_cycle
        )
        rows.append(row)
    return _csv_bytes(fields, rows)


def export_meter_lines_csv(result: MeterAnalysisResult) -> bytes:
    fields = [
        "line_id",
        "line_number",
        "stanza_number",
        "source_text",
        "status",
        "eligible_token_count",
        "supported_token_count",
        "pronunciation_coverage",
        "missing_forms",
        "pronunciation_variant_count",
        "common_meter_position",
        "common_meter_expected_foot_count",
        "common_meter_expected_foot_count_name",
        "common_meter_line_fit",
        "closest_candidate",
        "pattern",
        "foot_count",
        "foot_count_name",
        "selected_stress_sequence",
        "base_template_stress",
        "evaluated_template_stress",
        "fit_score",
        "fit_label",
        "total_cost",
        "substitution_count",
        "initial_inversion_count",
        "extra_syllable_count",
        "omitted_syllable_count",
        "feminine_ending_count",
        "catalectic_count",
        "spondee_substitution_count",
        "pyrrhic_substitution_count",
        "aligned_observed",
        "aligned_template",
        "reason",
    ]
    rows = []
    common_meter_by_line: dict[
        str,
        tuple[int, int, CandidateMeterFit | None],
    ] = {}
    for stanza_number in sorted(
        {item.stanza_number for item in result.line_results}
    ):
        stanza_lines = sorted(
            (
                item
                for item in result.line_results
                if item.stanza_number == stanza_number
                and item.status.value != "no_lexical_tokens"
            ),
            key=lambda item: item.line_number,
        )
        for position, line in enumerate(stanza_lines):
            expected_foot_count = (4, 3, 4, 3)[position % 4]
            expected_fit = next(
                (
                    fit
                    for fit in line.candidate_fits
                    if fit.pattern.value == "iambic"
                    and fit.foot_count == expected_foot_count
                ),
                None,
            )
            common_meter_by_line[line.line_id] = (
                (position % 4) + 1,
                expected_foot_count,
                expected_fit,
            )
    for line in result.line_results:
        fit = line.closest_candidate
        scheme_evidence = common_meter_by_line.get(line.line_id)
        common_fit = scheme_evidence[2] if scheme_evidence else None
        rows.append(
            {
                "line_id": line.line_id,
                "line_number": line.line_number,
                "stanza_number": line.stanza_number,
                "source_text": line.source_text,
                "status": line.status.value,
                "eligible_token_count": line.eligible_token_count,
                "supported_token_count": line.supported_token_count,
                "pronunciation_coverage": line.pronunciation_coverage,
                "missing_forms": " | ".join(line.missing_forms),
                "pronunciation_variant_count": line.pronunciation_variant_count,
                "common_meter_position": (
                    scheme_evidence[0] if scheme_evidence else ""
                ),
                "common_meter_expected_foot_count": (
                    scheme_evidence[1] if scheme_evidence else ""
                ),
                "common_meter_expected_foot_count_name": (
                    (
                        "tetrameter"
                        if scheme_evidence[1] == 4
                        else "trimeter"
                    )
                    if scheme_evidence
                    else ""
                ),
                "common_meter_line_fit": (
                    common_fit.fit_score if common_fit else ""
                ),
                "closest_candidate": fit.label if fit else "",
                "pattern": fit.pattern.value if fit else "",
                "foot_count": fit.foot_count if fit else "",
                "foot_count_name": fit.foot_count_name if fit else "",
                "selected_stress_sequence": (
                    fit.selected_stress_sequence if fit else ""
                ),
                "base_template_stress": fit.base_template_stress if fit else "",
                "evaluated_template_stress": (
                    fit.evaluated_template_stress if fit else ""
                ),
                "fit_score": fit.fit_score if fit else "",
                "fit_label": fit.fit_label if fit else "",
                "total_cost": fit.total_cost if fit else "",
                "substitution_count": fit.substitution_count if fit else "",
                "initial_inversion_count": (
                    fit.initial_inversion_count if fit else ""
                ),
                "extra_syllable_count": (
                    fit.extra_syllable_count if fit else ""
                ),
                "omitted_syllable_count": (
                    fit.omitted_syllable_count if fit else ""
                ),
                "feminine_ending_count": (
                    fit.feminine_ending_count if fit else ""
                ),
                "catalectic_count": fit.catalectic_count if fit else "",
                "spondee_substitution_count": (
                    fit.spondee_substitution_count if fit else ""
                ),
                "pyrrhic_substitution_count": (
                    fit.pyrrhic_substitution_count if fit else ""
                ),
                "aligned_observed": fit.aligned_observed if fit else "",
                "aligned_template": fit.aligned_template if fit else "",
                "reason": line.reason,
            }
        )
    return _csv_bytes(fields, rows)


def export_meter_alignment_operations_csv(
    result: MeterAnalysisResult,
) -> bytes:
    fields = [
        "line_id",
        "line_number",
        "candidate_label",
        "operation_number",
        "kind",
        "observed_index",
        "template_index",
        "observed_stress",
        "template_stress",
        "cost",
        "token_id",
        "surface_form",
        "part_of_speech",
        "feminine_ending",
        "catalectic_ending",
    ]
    rows = []
    for line in result.line_results:
        fit = line.closest_candidate
        if fit is None:
            continue
        for operation_number, operation in enumerate(
            fit.operations,
            start=1,
        ):
            row = asdict(operation)
            row.update(
                {
                    "line_id": line.line_id,
                    "line_number": line.line_number,
                    "candidate_label": fit.label,
                    "operation_number": operation_number,
                    "kind": operation.kind.value,
                }
            )
            rows.append(row)
    return _csv_bytes(fields, rows)


def export_meter_bundle(result: MeterAnalysisResult) -> dict[str, bytes]:
    return {
        "meter_summary.csv": export_meter_summary_csv(result),
        "meter_candidates.csv": export_meter_candidates_csv(result),
        "meter_schemes.csv": export_meter_schemes_csv(result),
        "meter_lines.csv": export_meter_lines_csv(result),
        "meter_alignment_operations.csv": (
            export_meter_alignment_operations_csv(result)
        ),
        "meter_result.json": export_meter_json(result),
    }
