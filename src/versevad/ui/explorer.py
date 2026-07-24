"""Streamlit Lexicon Explorer for exact, lemma, phrase, and mapped lookup."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from versevad.explorer import LexiconExplorerResult, explore_lexicons
from versevad.preprocessing import TextPreprocessor
from versevad.ui.design import render_empty_state, render_workspace_header


def _score(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def _render_vad(result: LexiconExplorerResult) -> None:
    vad = [row for row in result.entries if row.original_scores is not None]
    if not vad:
        return
    st.subheader("Valence, Arousal, and Dominance")
    mode = st.radio(
        "Value display",
        options=["Original and normalized", "Original source values", "Normalized comparison"],
        horizontal=True,
        key="explorer_value_display",
    )
    rows = []
    for entry in vad:
        original = entry.original_scores
        normalized = entry.normalized_scores
        assert original is not None and normalized is not None
        row = {
            "Lexicon": entry.lexicon,
            "Matched entry": entry.matched_term,
            "Method": entry.match_method,
        }
        if mode != "Normalized comparison":
            row.update(
                {
                    "Valence — original": f"{original.valence:.3f} / {entry.original_scale}",
                    "Arousal — original": f"{original.arousal:.3f} / {entry.original_scale}",
                    "Dominance — original": f"{original.dominance:.3f} / {entry.original_scale}",
                }
            )
        if mode != "Original source values":
            row.update(
                {
                    "Valence — normalized": normalized.valence,
                    "Arousal — normalized": normalized.arousal,
                    "Dominance — normalized": normalized.dominance,
                }
            )
        rows.append(row)
    frame = pd.DataFrame(rows)
    normalized_columns = [column for column in frame if "normalized" in column]
    styling = frame.style
    if normalized_columns:
        styling = styling.format({column: "{:.3f}" for column in normalized_columns})
    st.dataframe(styling, hide_index=True, width="stretch")
    st.caption(
        "Original values reproduce the source scales. Normalized values are separate "
        "derived 0–1 transformations; they do not make the source samples interchangeable."
    )

    comparison_rows = []
    for entry in vad:
        normalized = entry.normalized_scores
        assert normalized is not None
        for dimension in ("valence", "arousal", "dominance"):
            comparison_rows.append(
                {
                    "Lexicon": entry.lexicon,
                    "Dimension": dimension.title(),
                    "Normalized rating": getattr(normalized, dimension),
                    "Method": entry.match_method,
                }
            )
    st.bar_chart(
        pd.DataFrame(comparison_rows),
        x="Dimension",
        y="Normalized rating",
        color="Lexicon",
        stack=False,
        height=320,
    )

    uncertainty = []
    for entry in vad:
        if entry.standard_deviation is None and entry.rater_count is None:
            continue
        for dimension in ("valence", "arousal", "dominance"):
            uncertainty.append(
                {
                    "Lexicon": entry.lexicon,
                    "Dimension": dimension.title(),
                    "Mean": getattr(entry.original_scores, dimension),
                    "Standard deviation": (
                        getattr(entry.standard_deviation, dimension)
                        if entry.standard_deviation is not None
                        else None
                    ),
                    "Rater count": (
                        int(getattr(entry.rater_count, dimension))
                        if entry.rater_count is not None
                        else None
                    ),
                }
            )
    if uncertainty:
        with st.expander("Rating variation and rater counts"):
            st.write(
                "A larger standard deviation means the source ratings were more dispersed "
                "around the mean. Blank cells mean that source did not supply the field."
            )
            st.dataframe(
                pd.DataFrame(uncertainty).style.format(
                    {"Mean": "{:.3f}", "Standard deviation": "{:.3f}"},
                    na_rep="—",
                ),
                hide_index=True,
                width="stretch",
            )

    if result.comparisons:
        st.subheader("VerseVAD-Derived Cross-Lexicon Spread")
        spread = pd.DataFrame(
            [
                {
                    "Dimension": row.dimension.title(),
                    "Entries": row.entry_count,
                    "Minimum": row.minimum,
                    "Maximum": row.maximum,
                    "Range": row.spread,
                    "Descriptive agreement": row.descriptive_agreement.title(),
                }
                for row in result.comparisons
            ]
        )
        st.dataframe(
            spread.style.format({"Minimum": "{:.3f}", "Maximum": "{:.3f}", "Range": "{:.3f}"}),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Agreement is a VerseVAD heuristic based only on normalized range: high ≤ 0.10, "
            "moderate ≤ 0.25, low > 0.25. It is descriptive, not a reliability statistic."
        )


def _render_emotion(result: LexiconExplorerResult) -> None:
    association_entries = [
        row for row in result.entries if row.value_kind == "categorical_association"
    ]
    emotions = [
        row
        for row in association_entries
        if any(
            category
            in {
                "anger",
                "anticipation",
                "disgust",
                "fear",
                "joy",
                "sadness",
                "surprise",
                "trust",
            }
            for category in row.associations
        )
    ]
    sentiments = [
        row
        for row in association_entries
        if any(category in {"positive", "negative"} for category in row.associations)
    ]
    intensities = [row for row in result.entries if row.intensities]
    if emotions:
        st.subheader("Eight Emotion Associations")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Lexicon": row.lexicon,
                        "Matched entry": row.matched_term,
                        "Method": row.match_method,
                        "Source associations": (
                            ", ".join(
                                category
                                for category in row.associations
                                if category
                                in {
                                    "anger",
                                    "anticipation",
                                    "disgust",
                                    "fear",
                                    "joy",
                                    "sadness",
                                    "surprise",
                                    "trust",
                                }
                            )
                            if row.associations
                            else "No positive associations in the source entry"
                        ),
                    }
                    for row in emotions
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    if sentiments:
        st.subheader("Positive and Negative Sentiment Associations")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Lexicon": row.lexicon,
                        "Matched entry": row.matched_term,
                        "Method": row.match_method,
                        "Source associations": ", ".join(
                            category
                            for category in row.associations
                            if category in {"positive", "negative"}
                        ),
                    }
                    for row in sentiments
                ]
            ),
            hide_index=True,
            width="stretch",
        )
    if intensities:
        st.subheader("Emotion Intensity Entries")
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Lexicon": row.lexicon,
                        "Matched entry": row.matched_term,
                        "Method": row.match_method,
                        "Category": category.title(),
                        "Source intensity": intensity,
                    }
                    for row in intensities
                    for category, intensity in row.intensities
                ]
            ).style.format({"Source intensity": "{:.3f}"}),
            hide_index=True,
            width="stretch",
        )


def _render_components(result: LexiconExplorerResult) -> None:
    if not result.component_averages:
        return
    st.subheader("Derived Component Averages")
    st.warning(
        "No published phrase entry was found in these VAD sources. The rows below "
        "average exact component entries and are VerseVAD-derived—not published phrase ratings."
    )
    rows = []
    for average in result.component_averages:
        rows.append(
            {
                "Lexicon": average.lexicon,
                "Components": " + ".join(average.components),
                "Original valence": f"{average.original_scores.valence:.3f} / {average.original_scale}",
                "Normalized valence": average.normalized_scores.valence,
                "Normalized arousal": average.normalized_scores.arousal,
                "Normalized dominance": average.normalized_scores.dominance,
            }
        )
    st.dataframe(
        pd.DataFrame(rows).style.format(
            {
                "Normalized valence": "{:.3f}",
                "Normalized arousal": "{:.3f}",
                "Normalized dominance": "{:.3f}",
            }
        ),
        hide_index=True,
        width="stretch",
    )


def _render_supplementary(result: LexiconExplorerResult) -> None:
    if not result.supplementary_entries:
        return
    st.subheader("Additional Lexical Evidence")
    st.caption(
        "These are separate local datasets and constructs. Missing entries remain "
        "unmatched; VerseVAD never supplies a neutral replacement value."
    )
    status_rows = {}
    for entry in result.supplementary_entries:
        status_rows.setdefault(
            entry.resource_id,
            {
                "Resource": entry.resource,
                "Construct": entry.construct.replace("_", " ").title(),
                "Status": entry.status.replace("_", " ").title(),
                "Matched entry": entry.matched_term or "—",
                "Method": entry.match_method or "—",
                "Note": entry.status_message,
            },
        )
    st.dataframe(
        pd.DataFrame(status_rows.values()),
        hide_index=True,
        width="stretch",
    )

    evidence_rows = []
    for entry in result.supplementary_entries:
        for value in entry.values:
            evidence_rows.append(
                {
                    "Resource": entry.resource,
                    "Variant": entry.variant_label or "—",
                    "Field": value.field,
                    "Value": "—" if value.value is None else value.value,
                    "Unit": value.unit or "—",
                    "Note": value.note or "—",
                }
            )
    if evidence_rows:
        st.dataframe(
            pd.DataFrame(evidence_rows),
            hide_index=True,
            width="stretch",
        )
    st.caption(
        "Concreteness and age-of-acquisition values are normative source ratings; "
        "SUBTLEX-US values describe corpus frequency; CMUdict supplies candidate "
        "pronunciations and lexical stress, not a context-sensitive performance."
    )


def _render_provenance(result: LexiconExplorerResult) -> None:
    if not result.entries and not result.supplementary_entries:
        return
    with st.expander("Source provenance"):
        if result.entries:
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Resource": row.lexicon,
                            "Version": row.version,
                            "Matched entry": row.matched_term,
                            "Method": row.match_method,
                            "Source rows": ", ".join(
                                str(value) for value in row.source_rows
                            ),
                            "Original scale": row.original_scale,
                            "Formula": row.normalization_formula,
                            "Adapter": row.adapter_version,
                            "Source file": row.source_file,
                            "SHA-256": row.source_sha256,
                            "Citation": row.citation,
                        }
                        for row in result.entries
                    ]
                ),
                hide_index=True,
                width="stretch",
                height=340,
            )
        supplementary = {}
        for row in result.supplementary_entries:
            supplementary.setdefault(
                row.resource_id,
                {
                    "Resource": row.resource,
                    "Version": row.version,
                    "Matched entry": row.matched_term or "—",
                    "Method": row.match_method or "—",
                    "Source rows": ", ".join(
                        str(value) for value in row.source_rows
                    )
                    or "—",
                    "Adapter": row.adapter_version,
                    "Source file": row.source_file,
                    "SHA-256": row.source_sha256 or "—",
                    "Additional hashes": "; ".join(
                        f"{resource_id}: {sha256}"
                        for resource_id, sha256 in row.source_hashes
                    )
                    or "—",
                    "Citation": row.citation,
                },
            )
        if supplementary:
            st.dataframe(
                pd.DataFrame(supplementary.values()),
                hide_index=True,
                width="stretch",
                height=300,
            )


def render_lexicon_explorer(preprocessor: TextPreprocessor) -> None:
    with st.sidebar:
        st.markdown("### Lexicon Explorer")
        st.success("Every lookup stays on this computer.")
        st.caption(
            "Exact entries, phrase entries, lemma-derived entries, and user-supplied mappings are always labeled separately."
        )
    render_workspace_header(
        "Lexicon Explorer",
        "Look up a word or phrase across all installed affective lexicons plus "
        "concreteness, SUBTLEX-US frequency, age of acquisition, and CMUdict "
        "pronunciation and stress. Each source remains separate and auditable.",
        kicker="Auditable word and phrase lookup",
        status="Local resources",
    )
    with st.form("lexicon_explorer_search"):
        query = st.text_input(
            "Word or phrase",
            placeholder="Try: blood, burning, broken heart, or fall in love",
        )
        mapped_query = st.text_input(
            "Optional user-supplied mapping",
            placeholder="Example: o'er → over (enter over here)",
            help="Used only as a clearly labeled lookup fallback. It never changes poem or corpus analyses.",
        )
        search = st.form_submit_button("Search installed lexicons", type="primary")
    if search:
        try:
            with st.spinner("Searching all local lexical resources…"):
                st.session_state["lexicon_explorer_result"] = explore_lexicons(
                    query,
                    preprocessor,
                    mapped_query=mapped_query,
                )
        except ValueError as error:
            st.error(str(error))

    result = st.session_state.get("lexicon_explorer_result")
    if result is None:
        render_empty_state(
            "Inspect a word or phrase",
            "The Explorer reports every available local lexical and phonological "
            "source while keeping exact, lemma-derived, mapped, and missing "
            "evidence distinct.",
            "Enter one word or phrase above and select Search installed lexicons.",
        )
        return
    st.divider()
    st.header(result.query)
    details = [f"Normalized lookup: `{result.normalized_query}`"]
    if result.processing_lemma:
        details.append(f"Model lemma: `{result.processing_lemma}`")
    if result.processing_pos:
        details.append(f"Model part of speech: `{result.processing_pos}`")
    st.write(" · ".join(details))
    for notice in result.notices:
        st.info(notice)
    if not result.entries:
        st.warning(
            "No exact or lemma-derived affective entry was found in the installed "
            "affective sources."
        )
        if result.suggestions:
            st.write("**Possible spelling or nearby-form suggestions (not substitutes):**")
            st.write(", ".join(result.suggestions))
    else:
        methods = pd.DataFrame(
            [
                {
                    "Lexicon": row.lexicon,
                    "Matched source entry": row.matched_term,
                    "How it matched": row.match_method,
                    "Value kind": row.value_kind.replace("_", " ").title(),
                }
                for row in result.entries
            ]
        )
        st.dataframe(methods, hide_index=True, width="stretch")
    _render_vad(result)
    _render_emotion(result)
    _render_components(result)
    _render_supplementary(result)
    _render_provenance(result)
    st.warning(
        "A lookup reports decontextualized normative ratings or associations. It does "
        "not resolve polysemy, historical sense, irony, metaphor, or contextual meaning."
    )
