"""CSV and narrative Word exports for inherited-form candidate analysis."""

from __future__ import annotations

import csv
import io
from typing import Iterable

from versevad.exports.docx_report import REPORT_PROFILES, build_narrative_report
from versevad.exports.module_manifest import export_module_manifest_csv
from versevad.inherited_form import FORM_PROFILES, InheritedFormAnalysisResult


def _csv_bytes(fieldnames: list[str], rows: Iterable[dict[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def export_inherited_form_summary_csv(
    result: InheritedFormAnalysisResult,
) -> bytes:
    fields = [
        "result_status",
        "best_candidate_id",
        "best_candidate_name",
        "classification",
        "consistency_index",
        "evidence_coverage",
        "confidence_band",
        "confidence_is_probability",
        "nearest_alternative_id",
        "nearest_alternative_name",
        "candidate_margin",
        "traditional_definition",
        "suggestion_tooltip",
        "narrative",
    ]
    best = result.best_candidate
    alternative = result.nearest_alternative
    return _csv_bytes(
        fields,
        (
            {
                "result_status": result.status,
                "best_candidate_id": best.profile_id if best else "",
                "best_candidate_name": best.profile_name if best else "",
                "classification": (
                    best.classification if best else "No inherited-form match"
                ),
                "consistency_index": best.consistency if best else "",
                "evidence_coverage": (
                    best.evidence_coverage
                    if best
                    else result.candidates[0].evidence_coverage
                    if result.candidates
                    else ""
                ),
                "confidence_band": best.confidence if best else "none",
                "confidence_is_probability": False,
                "nearest_alternative_id": (
                    alternative.profile_id if alternative else ""
                ),
                "nearest_alternative_name": (
                    alternative.profile_name if alternative else ""
                ),
                "candidate_margin": (
                    best.margin_over_next
                    if best and best.margin_over_next is not None
                    else ""
                ),
                "traditional_definition": best.definition if best else "",
                "suggestion_tooltip": best.tooltip if best else "",
                "narrative": best.narrative if best else (
                    "No enabled profile met both the configured suggestion "
                    "threshold and minimum evidence coverage."
                ),
            },
        ),
    )


def export_inherited_form_candidates_csv(
    result: InheritedFormAnalysisResult,
) -> bytes:
    fields = [
        "rank",
        "profile_id",
        "profile_name",
        "classification",
        "suggested",
        "consistency_index",
        "evidence_coverage",
        "required_feature_agreement",
        "required_evidence_coverage",
        "required_contradiction_count",
        "margin_over_next",
        "confidence_band",
        "traditional_definition",
        "suggestion_tooltip",
        "narrative",
    ]
    return _csv_bytes(
        fields,
        (
            {
                "rank": item.rank,
                "profile_id": item.profile_id,
                "profile_name": item.profile_name,
                "classification": item.classification,
                "suggested": item.suggested,
                "consistency_index": (
                    item.consistency if item.consistency is not None else ""
                ),
                "evidence_coverage": item.evidence_coverage,
                "required_feature_agreement": (
                    item.required_feature_agreement
                    if item.required_feature_agreement is not None
                    else ""
                ),
                "required_evidence_coverage": (
                    item.required_evidence_coverage
                ),
                "required_contradiction_count": (
                    item.required_contradiction_count
                ),
                "margin_over_next": (
                    item.margin_over_next
                    if item.margin_over_next is not None
                    else ""
                ),
                "confidence_band": item.confidence,
                "traditional_definition": item.definition,
                "suggestion_tooltip": item.tooltip,
                "narrative": item.narrative,
            }
            for item in result.candidates
        ),
    )


def export_inherited_form_features_csv(
    result: InheritedFormAnalysisResult,
) -> bytes:
    fields = [
        "candidate_rank",
        "profile_id",
        "profile_name",
        "rule_id",
        "feature_id",
        "feature_label",
        "role",
        "weight",
        "expected",
        "detected",
        "score",
        "available",
        "evidence_coverage",
        "explanation",
        "source_modules",
    ]
    return _csv_bytes(
        fields,
        (
            {
                "candidate_rank": candidate.rank,
                "profile_id": candidate.profile_id,
                "profile_name": candidate.profile_name,
                "rule_id": item.rule_id,
                "feature_id": item.feature_id,
                "feature_label": item.label,
                "role": item.role,
                "weight": item.weight,
                "expected": item.expected,
                "detected": item.detected,
                "score": item.score if item.score is not None else "",
                "available": item.available,
                "evidence_coverage": (
                    item.evidence_coverage
                    if item.evidence_coverage is not None
                    else ""
                ),
                "explanation": item.explanation,
                "source_modules": " | ".join(item.source_modules),
            }
            for candidate in result.candidates
            for item in candidate.feature_evidence
        ),
    )


def export_inherited_form_profiles_csv(
    result: InheritedFormAnalysisResult,
) -> bytes:
    del result
    fields = [
        "registry_version",
        "profile_id",
        "profile_name",
        "family",
        "tradition",
        "traditional_definition",
        "tooltip_definition",
        "source_urls",
        "limitations",
    ]
    return _csv_bytes(
        fields,
        (
            {
                "registry_version": profile.registry_version,
                "profile_id": profile.profile_id,
                "profile_name": profile.name,
                "family": profile.family,
                "tradition": profile.tradition,
                "traditional_definition": profile.definition,
                "tooltip_definition": profile.tooltip_definition,
                "source_urls": " | ".join(profile.source_urls),
                "limitations": " | ".join(profile.limitations),
            }
            for profile in FORM_PROFILES
        ),
    )


def export_inherited_form_methodology_csv(
    result: InheritedFormAnalysisResult,
) -> bytes:
    fields = ["section", "item", "value", "note"]
    configuration = result.configuration
    rows = [
        {
            "section": "method",
            "item": "candidate ranking",
            "value": "weighted available-evidence consistency",
            "note": (
                "Consistency = weighted scored evidence / available evidence "
                "weight. Missing evidence is excluded and lowers coverage."
            ),
        },
        {
            "section": "method",
            "item": "confidence",
            "value": "low / moderate / high",
            "note": (
                "A non-probabilistic band using consistency, evidence coverage, "
                "required-feature contradictions, and margin over the runner-up."
            ),
        },
        {
            "section": "method",
            "item": "identity claim",
            "value": "potential match only",
            "note": (
                "VerseVAD measures resemblance to a documented profile; it does "
                "not declare the poem's genre, quality, intent, or historical identity."
            ),
        },
    ]
    for name in (
        "suggestion_threshold",
        "minimum_evidence_coverage",
        "minimum_required_evidence_coverage",
        "moderate_confidence_threshold",
        "high_confidence_threshold",
        "moderate_margin",
        "high_margin",
        "modified_refrain_floor",
        "scenario_id",
    ):
        rows.append(
            {
                "section": "configuration",
                "item": name,
                "value": getattr(configuration, name),
                "note": "",
            }
        )
    return _csv_bytes(fields, rows)


def export_inherited_form_bundle(
    result: InheritedFormAnalysisResult,
    *,
    text_title: str = "",
) -> dict[str, bytes]:
    bundle = {
        "inherited_form_summary.csv": export_inherited_form_summary_csv(result),
        "inherited_form_candidates.csv": (
            export_inherited_form_candidates_csv(result)
        ),
        "inherited_form_features.csv": export_inherited_form_features_csv(result),
        "inherited_form_profiles.csv": export_inherited_form_profiles_csv(result),
        "inherited_form_methodology.csv": (
            export_inherited_form_methodology_csv(result)
        ),
        "inherited_form_manifest.csv": export_module_manifest_csv(result),
    }
    best = result.best_candidate
    alternative = result.nearest_alternative
    summary_rows = []
    if best is not None:
        summary_rows.append(
            {
                "section": "potential inherited-form match",
                "metric": "candidate",
                "value": best.profile_name,
                "unit_or_scale": best.classification,
                "denominator": (
                    f"{best.evidence_coverage:.1%} of weighted profile evidence"
                ),
                "note": (
                    f"Consistency {best.consistency:.1%}; confidence "
                    f"{best.confidence}. {best.tooltip}"
                ),
            }
        )
        if alternative is not None:
            summary_rows.append(
                {
                    "section": "potential inherited-form match",
                    "metric": "nearest alternative",
                    "value": alternative.profile_name,
                    "unit_or_scale": (
                        f"{alternative.consistency:.1%} consistency"
                        if alternative.consistency is not None
                        else "unavailable"
                    ),
                    "denominator": "same ten-profile registry",
                    "note": "Retained because related forms can share structural features.",
                }
            )
        summary_rows.extend(
            {
                "section": "feature evidence",
                "metric": item.label,
                "value": (
                    f"{item.score:.1%}" if item.score is not None else "unavailable"
                ),
                "unit_or_scale": item.role,
                "denominator": item.expected,
                "note": f"Detected: {item.detected}. {item.explanation}",
            }
            for item in best.feature_evidence
        )
    else:
        summary_rows.append(
            {
                "section": "potential inherited-form match",
                "metric": "result",
                "value": "No inherited-form match",
                "unit_or_scale": "",
                "denominator": "configured suggestion and coverage thresholds",
                "note": (
                    "The complete ranked candidates remain in "
                    "inherited_form_candidates.csv."
                ),
            }
        )
    bundle["inherited_form_report.docx"] = build_narrative_report(
        profile=REPORT_PROFILES["inherited_form"],
        summary_rows=summary_rows,
        companion_csv_files=tuple(bundle),
        text_title=text_title,
        text_id=result.module_result.text_id,
        result_id=result.module_result.result_id,
        warnings=tuple(
            warning.message for warning in result.module_result.warnings
        ),
        additional_paragraphs=(
            "Traditional definitions and their source URLs are recorded in "
            "inherited_form_profiles.csv. Confidence is not a probability.",
        ),
    )
    return bundle


__all__ = [
    "export_inherited_form_bundle",
    "export_inherited_form_candidates_csv",
    "export_inherited_form_features_csv",
    "export_inherited_form_methodology_csv",
    "export_inherited_form_profiles_csv",
    "export_inherited_form_summary_csv",
]
