"""Streamlit presentation for inherited-form candidate evidence."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from versevad.exports.inherited_form import export_inherited_form_bundle
from versevad.inherited_form import FORM_PROFILES, InheritedFormAnalysisResult
from versevad.ui.design import render_dataframe


def _percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def render_inherited_form(
    result: InheritedFormAnalysisResult | None,
) -> None:
    st.subheader("Inherited Form Analysis")
    st.write(
        "VerseVAD compares the poem with ten documented structural profiles. "
        "It reports a potential match, consistency, evidence coverage, and "
        "candidate separation—not a definitive genre identity."
    )
    if result is None:
        st.info(
            "Enable Inherited Form Analysis, then analyze the text. VerseVAD "
            "will automatically reuse the pronunciation, meter, and rhyme foundation."
        )
        return

    best = result.best_candidate
    if best is None:
        st.info(
            "No profile met both the configured suggestion threshold and the "
            "minimum evidence coverage. The full ranking remains available below."
        )
    else:
        st.markdown(f"### Potential match: {best.profile_name}")
        st.caption(best.definition)
        columns = st.columns(4)
        columns[0].metric(
            "Classification",
            best.classification,
            help=best.tooltip,
        )
        columns[1].metric(
            "Consistency",
            _percentage(best.consistency),
            help=(
                "Agreement with the available weighted rules for this profile. "
                "It is not a probability."
            ),
        )
        columns[2].metric(
            "Evidence coverage",
            _percentage(best.evidence_coverage),
            help=(
                "Share of the profile's possible weighted evidence that was "
                "available. Missing pronunciation or rhyme stays missing."
            ),
        )
        columns[3].metric(
            "Confidence",
            best.confidence.title(),
            help=(
                "A rule-based band using consistency, coverage, required-feature "
                "contradictions, and distance from the runner-up—not a probability."
            ),
        )
        st.write(best.narrative)
        st.info(
            best.tooltip,
            icon="ℹ️",
        )
        if result.nearest_alternative is not None:
            alternative = result.nearest_alternative
            st.caption(
                f"Nearest alternative: {alternative.profile_name} "
                f"({_percentage(alternative.consistency)} consistency). "
                f"Best-candidate margin: {_percentage(best.margin_over_next)}."
            )

    candidate_rows = [
        {
            "Rank": item.rank,
            "Candidate profile": item.profile_name,
            "Consistency": item.consistency,
            "Evidence coverage": item.evidence_coverage,
            "Required evidence": item.required_evidence_coverage,
            "Classification": item.classification,
            "Confidence": item.confidence.title(),
            "Suggested": item.suggested,
        }
        for item in result.candidates
    ]
    st.markdown("#### Ten-profile ranking")
    render_dataframe(
        pd.DataFrame(candidate_rows),
        column_config={
            "Consistency": st.column_config.NumberColumn(format="percent"),
            "Evidence coverage": st.column_config.NumberColumn(format="percent"),
            "Required evidence": st.column_config.NumberColumn(format="percent"),
        },
        hide_index=True,
        width="stretch",
        height=min(420, 36 * (len(candidate_rows) + 1)),
    )

    profile_ids = [item.profile_id for item in result.candidates]
    selected_id = st.selectbox(
        "Inspect candidate evidence",
        options=profile_ids,
        format_func=lambda value: next(
            item.profile_name for item in result.candidates
            if item.profile_id == value
        ),
        key="inherited_form_candidate_detail",
    )
    selected = next(
        item for item in result.candidates if item.profile_id == selected_id
    )
    st.caption(selected.definition)
    st.info(selected.tooltip, icon="ℹ️")
    feature_rows = [
        {
            "Feature": item.label,
            "Role": item.role.title(),
            "Weight": item.weight,
            "Expected": item.expected,
            "Detected": item.detected,
            "Match": item.score,
            "Evidence coverage": item.evidence_coverage,
            "Evidence source": ", ".join(item.source_modules),
        }
        for item in selected.feature_evidence
    ]
    render_dataframe(
        pd.DataFrame(feature_rows),
        column_config={
            "Match": st.column_config.NumberColumn(format="percent"),
            "Evidence coverage": st.column_config.NumberColumn(format="percent"),
        },
        hide_index=True,
        width="stretch",
        height=min(360, 44 * (len(feature_rows) + 1)),
    )

    profile = next(
        profile for profile in FORM_PROFILES
        if profile.profile_id == selected_id
    )
    with st.expander("Traditional definition, sources, and limitations"):
        st.write(profile.definition)
        for url in profile.source_urls:
            st.markdown(f"- [{url}]({url})")
        for limitation in profile.limitations:
            st.markdown(f"- {limitation}")
        st.caption(
            "Conventions vary historically and across languages and communities. "
            "The profile is versioned analytical evidence, not a universal definition."
        )

    bundle = export_inherited_form_bundle(result)
    st.download_button(
        "Download inherited-form report (.docx)",
        data=bundle["inherited_form_report.docx"],
        file_name="inherited_form_report.docx",
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        key="download_inherited_form_docx",
    )
    st.caption(
        "The complete analysis ZIP also includes candidate, feature, profile, "
        "methodology, and manifest CSV files."
    )


__all__ = ["render_inherited_form"]
