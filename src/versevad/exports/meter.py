"""Stable UTF-8 CSV and narrative Word meter exports."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict
from typing import Iterable

from versevad.exports.docx_report import build_narrative_report_from_summary_csv
from versevad.exports.module_manifest import export_module_manifest_csv
from versevad.prosody.meter import MeterAnalysisResult


def _csv_bytes(
    fieldnames: list[str],
    rows: Iterable[dict[str, object]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


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
                "One fixed recurring stress pattern and foot count.",
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
    for line in result.line_results:
        fit = line.closest_candidate
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


def export_meter_realizations_csv(result: MeterAnalysisResult) -> bytes:
    """Export primary and retained alternate performance-aware readings."""

    fields = [
        "line_id",
        "line_number",
        "stanza_number",
        "source_text",
        "reading_rank",
        "reading_role",
        "candidate_meter",
        "lexical_stress",
        "candidate_template",
        "realized_scansion",
        "line_confidence",
        "score_margin",
        "candidate_fit",
        "contextual_fit",
        "syllable_count_fit",
        "phrase_fit",
        "line_ending_fit",
        "pronunciation_plausibility",
        "poem_consistency",
        "stanza_consistency",
        "style_compatibility",
        "substitution_penalty",
        "overall_score",
        "promotions",
        "demotions",
        "substitutions",
        "stress_clashes",
        "stress_lapses",
        "caesurae",
        "selected_pronunciation_path",
        "explanation",
    ]
    performance = result.performance_aware
    rows: list[dict[str, object]] = []
    if performance is None:
        return _csv_bytes(fields, rows)
    for line in performance.line_results:
        readings = (
            (line.primary_realization,) + line.alternate_realizations
            if line.primary_realization is not None
            else ()
        )
        for rank, reading in enumerate(readings, start=1):
            rows.append(
                {
                    "line_id": line.line_id,
                    "line_number": line.line_number,
                    "stanza_number": line.stanza_number,
                    "source_text": line.source_text,
                    "reading_rank": rank,
                    "reading_role": "primary" if rank == 1 else "alternate",
                    "candidate_meter": reading.candidate_label,
                    "lexical_stress": reading.lexical_stress,
                    "candidate_template": reading.candidate_template,
                    "realized_scansion": reading.realized_display,
                    "line_confidence": line.confidence.value,
                    "score_margin": line.score_margin,
                    "candidate_fit": reading.scores.candidate_fit,
                    "contextual_fit": reading.scores.contextual_fit,
                    "syllable_count_fit": reading.scores.syllable_count_fit,
                    "phrase_fit": reading.scores.phrase_fit,
                    "line_ending_fit": reading.scores.line_ending_fit,
                    "pronunciation_plausibility": (
                        reading.scores.pronunciation_plausibility
                    ),
                    "poem_consistency": reading.scores.poem_consistency,
                    "stanza_consistency": reading.scores.stanza_consistency,
                    "style_compatibility": (
                        reading.scores.style_compatibility
                    ),
                    "substitution_penalty": (
                        reading.scores.substitution_penalty
                    ),
                    "overall_score": reading.scores.overall,
                    "promotions": reading.promotions,
                    "demotions": reading.demotions,
                    "substitutions": " | ".join(
                        item.label for item in reading.substitutions
                    ),
                    "stress_clashes": " | ".join(
                        str(item) for item in reading.stress_clashes
                    ),
                    "stress_lapses": " | ".join(
                        f"{start}-{end}"
                        for start, end in reading.stress_lapses
                    ),
                    "caesurae": " | ".join(
                        f"after {item.after_syllable} ({item.strength})"
                        for item in reading.caesurae
                    ),
                    "selected_pronunciation_path": " | ".join(
                        reading.selected_pronunciation_path
                    ),
                    "explanation": line.explanation,
                }
            )
    return _csv_bytes(fields, rows)


def export_meter_stanzas_csv(result: MeterAnalysisResult) -> bytes:
    fields = [
        "stanza_number",
        "line_numbers",
        "primary_candidate",
        "alternate_candidate",
        "analyzable_lines",
        "mean_realized_score",
        "regularity",
        "line_position_pattern",
        "exceptions",
    ]
    performance = result.performance_aware
    rows = []
    if performance is not None:
        for stanza in performance.stanza_summaries:
            rows.append(
                {
                    "stanza_number": stanza.stanza_number,
                    "line_numbers": " | ".join(
                        str(item) for item in stanza.line_numbers
                    ),
                    "primary_candidate": stanza.primary_candidate,
                    "alternate_candidate": stanza.alternate_candidate,
                    "analyzable_lines": stanza.analyzable_lines,
                    "mean_realized_score": stanza.mean_realized_score,
                    "regularity": stanza.regularity,
                    "line_position_pattern": " | ".join(
                        stanza.line_position_pattern
                    ),
                    "exceptions": " | ".join(
                        str(item) for item in stanza.exceptions
                    ),
                }
            )
    return _csv_bytes(fields, rows)


def export_meter_rhythm_trajectory_csv(result: MeterAnalysisResult) -> bytes:
    fields = [
        "line_number",
        "stanza_number",
        "candidate_meter",
        "realized_score",
        "syllable_count",
        "realized_beats",
        "lexical_stress_density",
        "substitution_count",
        "caesura_after_syllable",
    ]
    performance = result.performance_aware
    rows = []
    if performance is not None:
        rows = [asdict(item) for item in performance.trajectory]
    return _csv_bytes(fields, rows)


def export_meter_scholar_revisions_csv(result: MeterAnalysisResult) -> bytes:
    """Keep automatic and scholar-supplied readings in separate columns."""

    fields = [
        "line_id",
        "line_number",
        "source_text",
        "applied_to_existing_line",
        "automatic_candidate",
        "automatic_scansion",
        "revised_candidate",
        "revised_scansion",
        "scholar_note",
    ]
    performance = result.performance_aware
    rows = []
    if performance is not None:
        rows = [
            {
                "line_id": item.line_id,
                "line_number": item.line_number,
                "source_text": item.source_text,
                "applied_to_existing_line": item.applied_to_existing_line,
                "automatic_candidate": item.automatic_candidate,
                "automatic_scansion": item.automatic_scansion,
                "revised_candidate": item.revised_candidate,
                "revised_scansion": item.revised_scansion,
                "scholar_note": item.note,
            }
            for item in performance.scholar_revisions
        ]
    return _csv_bytes(fields, rows)


def _meter_scansion_narrative(result: MeterAnalysisResult) -> bytes:
    """Return an accessible plain-text performance-aware scansion report."""

    performance = result.performance_aware
    if performance is None:
        return (
            "Performance-aware meter was not selected for this analysis.\n"
        ).encode("utf-8")
    summary = performance.poem_summary
    lines = [
        "VerseVAD performance-aware meter report",
        "=" * 39,
        "",
        f"Analysis mode: {performance.analysis_mode.value}",
        (
            "Declared style profile: "
            f"{performance.style_profile.label} "
            f"(v{performance.style_profile.version})"
        ),
        (
            "Rhythmic organization: "
            f"{summary.rhythmic_organization.value}"
        ),
        f"Primary candidate: {summary.primary_meter or 'Insufficient evidence'}",
        f"Secondary candidate: {summary.secondary_meter or 'None retained'}",
        f"Rule-based confidence: {summary.confidence.value}",
        (
            "Analyzable line coverage: "
            f"{summary.analyzable_line_count} line(s); "
            f"{summary.line_coverage if summary.line_coverage is not None else 'NA'}"
        ),
        f"Mean realized score: {summary.mean_realized_score}",
        (
            "Generic recurring sequence: "
            f"{summary.generic_composite_pattern or 'None detected'}"
        ),
        "",
        "Notation",
        "--------",
        "x = weak position; / = strong position; ^ = proposed promotion;",
        "v = proposed demotion; 2 = secondary-stress flexibility;",
        "|| = punctuation-supported caesura; | = candidate foot boundary.",
        "",
        "Line readings",
        "-------------",
    ]
    for line in performance.line_results:
        lines.extend(
            (
                "",
                f"Line {line.line_number}: {line.source_text}",
                f"Status: {line.status.value}",
            )
        )
        reading = line.primary_realization
        if reading is None:
            lines.append(f"Reason: {line.explanation}")
            continue
        lines.extend(
            (
                f"Raw lexical stress: {line.raw_lexical_stress}",
                f"Fixed-layer nearest candidate: {line.candidate_meter}",
                f"Primary realized candidate: {reading.candidate_label}",
                f"Candidate template: {reading.candidate_template}",
                f"Realized scansion: {reading.realized_display}",
                f"Overall component score: {reading.scores.overall:.4f}",
                f"Confidence: {line.confidence.value}",
                (
                    "Substitutions: "
                    + (
                        "; ".join(
                            item.label for item in reading.substitutions
                        )
                        or "None"
                    )
                ),
                f"Explanation: {line.explanation}",
            )
        )
        if line.alternate_realizations:
            lines.append(
                "Retained alternatives: "
                + "; ".join(
                    (
                        f"{item.candidate_label} "
                        f"({item.scores.overall:.4f})"
                    )
                    for item in line.alternate_realizations
                )
            )
    lines.extend(("", "Method safeguards", "-----------------"))
    lines.extend(performance.methodology)
    lines.extend(("", "Warnings", "--------"))
    lines.extend(performance.warnings)
    if performance.scholar_revisions:
        lines.extend(("", "Scholar revisions", "-----------------"))
        for revision in performance.scholar_revisions:
            lines.extend(
                (
                    f"Line {revision.line_number}",
                    (
                        "Automatic: "
                        f"{revision.automatic_candidate or 'unavailable'} | "
                        f"{revision.automatic_scansion or 'unavailable'}"
                    ),
                    (
                        "Scholar revision: "
                        f"{revision.revised_candidate} | "
                        f"{revision.revised_scansion}"
                    ),
                    f"Scholar note: {revision.note}",
                )
            )
    return ("\n".join(lines) + "\n").encode("utf-8")


def export_meter_bundle(
    result: MeterAnalysisResult,
    *,
    text_title: str = "",
) -> dict[str, bytes]:
    bundle = {
        "meter_summary.csv": export_meter_summary_csv(result),
        "meter_candidates.csv": export_meter_candidates_csv(result),
        "meter_lines.csv": export_meter_lines_csv(result),
        "meter_alignment_operations.csv": (
            export_meter_alignment_operations_csv(result)
        ),
        "meter_manifest.csv": export_module_manifest_csv(result),
    }
    if result.performance_aware is not None:
        bundle.update(
            {
                "meter_realizations.csv": export_meter_realizations_csv(result),
                "meter_stanzas.csv": export_meter_stanzas_csv(result),
                "meter_rhythm_trajectory.csv": (
                    export_meter_rhythm_trajectory_csv(result)
                ),
            }
        )
        if result.performance_aware.scholar_revisions:
            bundle["meter_scholar_revisions.csv"] = (
                export_meter_scholar_revisions_csv(result)
            )
    bundle["meter_report.docx"] = build_narrative_report_from_summary_csv(
        "meter",
        bundle["meter_summary.csv"],
        companion_csv_files=tuple(bundle),
        text_title=text_title,
        text_id=result.module_result.text_id,
        result_id=result.module_result.result_id,
        warnings=tuple(
            warning.message for warning in result.module_result.warnings
        ),
    )
    return bundle
