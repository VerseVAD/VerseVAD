"""VerseVAD Phase 3 local graphical one-text workspace."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from versevad import __version__
from versevad.application import (
    AnalysisRequest,
    LEXICON_SPECS,
    TextImportError,
    WorkspaceAnalysisError,
    coverage_views,
    csv_reading_guide,
    decode_uploaded_text,
    detailed_export_zip,
    emotion_association_views,
    emotion_intensity_views,
    match_views,
    overview_notes,
    run_workspace_analysis,
    scholar_summary_csv,
    unmatched_views,
    vad_views,
)
from versevad.diagnostics import run_self_test
from versevad.models import PhrasePolicy
from versevad.preprocessing import SpacyEnglishPreprocessor


st.set_page_config(
    page_title="VerseVAD",
    page_icon="V",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
      --verse-ink: #172a3a;
      --verse-rust: #a34f32;
      --verse-sage: #5f7661;
      --verse-paper: #fbf8f1;
    }
    .stApp { background: linear-gradient(180deg, #fbf8f1 0%, #ffffff 34%); }
    h1, h2, h3 { color: var(--verse-ink); letter-spacing: -0.015em; }
    h1 { font-family: Georgia, 'Times New Roman', serif; }
    [data-testid="stMetric"] {
      background: rgba(255,255,255,.82);
      border: 1px solid #ded8cc;
      border-radius: 12px;
      padding: .8rem 1rem;
    }
    [data-testid="stSidebar"] { background: #f3efe5; }
    .verse-kicker {
      color: var(--verse-rust);
      font-size: .78rem;
      font-weight: 700;
      letter-spacing: .12em;
      text-transform: uppercase;
      margin-bottom: -.65rem;
    }
    .verse-callout {
      background: #eef3ec;
      border-left: 4px solid var(--verse-sage);
      border-radius: 6px;
      color: #24392b;
      padding: .85rem 1rem;
      margin: .5rem 0 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner=False)
def _preprocessor() -> SpacyEnglishPreprocessor:
    return SpacyEnglishPreprocessor()


def _percentage(value: float | None) -> str:
    return "—" if value is None else f"{value:.1%}"


def _decimal(value: float | None) -> str:
    return "—" if value is None else f"{value:.3f}"


def _frame(rows, rename: dict[str, str] | None = None) -> pd.DataFrame:
    data = pd.DataFrame([asdict(row) for row in rows])
    return data.rename(columns=rename or {})


def _display_self_test() -> None:
    with st.spinner("Checking the model, formulas, and five local lexicons…"):
        checks = run_self_test()
    st.session_state["self_test_checks"] = checks


st.session_state.setdefault("project_name", "Temporary private workspace")
st.session_state.setdefault("poem_title", "")
st.session_state.setdefault("poem_text", "")
st.session_state.setdefault("workspace", None)

with st.sidebar:
    st.markdown("### Local workspace")
    st.caption(f"VerseVAD {__version__}")
    st.success("Private by design: analysis stays on this computer.")
    st.info(
        "Phase 3 workspaces last only while the app is open. Download your results "
        "before closing; saved projects arrive in Phase 4."
    )
    st.markdown("### Installation check")
    if st.button("Run self-test", width="stretch", key="run_self_test"):
        _display_self_test()
    if "self_test_checks" in st.session_state:
        checks = st.session_state["self_test_checks"]
        passed = sum(check.passed for check in checks)
        st.caption(f"{passed}/{len(checks)} checks passed")
        with st.expander("Self-test details", expanded=passed != len(checks)):
            for check in checks:
                st.markdown(
                    f"**{'PASS' if check.passed else 'FAIL'} — {check.check}**  \n"
                    f"{check.detail}"
                )
    st.markdown("---")
    st.caption(
        "VerseVAD describes lexical evidence. It does not determine the emotion "
        "of a poem, speaker, author, or reader."
    )

st.markdown('<p class="verse-kicker">Local literary text analysis</p>', unsafe_allow_html=True)
st.title("VerseVAD")
st.write(
    "Paste or choose one poem, select the lexical evidence you want to inspect, "
    "and receive a readable analysis with its full audit trail."
)

with st.container(border=True):
    st.subheader("1. Add a poem")
    uploaded = st.file_uploader(
        "Choose a UTF-8 plain-text file (optional)",
        type=["txt"],
        help="The browser reads this file locally into the app. VerseVAD does not upload it to a cloud service.",
        key="uploaded_poem",
    )
    if uploaded is not None:
        content = uploaded.getvalue()
        upload_signature = hashlib.sha256(content).hexdigest()
        if st.session_state.get("upload_signature") != upload_signature:
            try:
                st.session_state["poem_text"] = decode_uploaded_text(uploaded.name, content)
                if not st.session_state.get("poem_title", "").strip():
                    st.session_state["poem_title"] = Path(uploaded.name).stem
                st.session_state["upload_signature"] = upload_signature
                st.rerun()
            except TextImportError as error:
                st.error(str(error))

    left, right = st.columns([1, 1])
    with left:
        st.text_input(
            "Workspace name",
            key="project_name",
            help="A temporary label for this session; Phase 3 does not create a persistent database.",
        )
    with right:
        st.text_input("Poem title or working label", key="poem_title")
    st.text_area(
        "Paste the poem exactly as you want it analyzed",
        key="poem_text",
        height=260,
        placeholder="Paste a poem here, preserving its line and stanza breaks…",
        help="VerseVAD keeps this original string unchanged and creates a separate processing representation.",
    )

with st.container(border=True):
    st.subheader("2. Choose evidence")
    spec_by_id = {spec.lexicon_id: spec for spec in LEXICON_SPECS}
    selected_lexicons = st.multiselect(
        "Lexicons",
        options=[spec.lexicon_id for spec in LEXICON_SPECS],
        default=[spec.lexicon_id for spec in LEXICON_SPECS],
        format_func=lambda lexicon_id: spec_by_id[lexicon_id].display_name,
        help="Each source is analyzed independently. VerseVAD never creates a default consensus score.",
        key="selected_lexicons",
    )
    if selected_lexicons:
        with st.expander("What each selected lexicon contributes"):
            for lexicon_id in selected_lexicons:
                spec = spec_by_id[lexicon_id]
                st.markdown(f"**{spec.display_name}:** {spec.short_description}")

    with st.expander("Advanced methodology settings"):
        policy_labels = {
            "Prefer the longest phrase (recommended)": PhrasePolicy.PHRASE_PREFERRED,
            "Use unigrams only": PhrasePolicy.UNIGRAM_ONLY,
            "Count phrases and components (exploratory)": PhrasePolicy.PHRASE_AND_COMPONENT,
        }
        policy_label = st.selectbox(
            "Phrase policy",
            options=list(policy_labels),
            index=0,
            help="Only NRC VAD v2.1 currently activates multiword expressions.",
            key="phrase_policy_label",
        )
        minimum_matches = st.number_input(
            "Minimum included matches before a VAD result is considered non-sparse",
            min_value=1,
            max_value=100,
            value=3,
            step=1,
            key="minimum_matches",
        )
        st.caption(
            "This threshold marks a result as sparse; it does not invent values or remove the audit trail."
        )

    analyze_clicked = st.button(
        "Analyze this text",
        type="primary",
        width="stretch",
        key="analyze_text",
    )

if analyze_clicked:
    try:
        request = AnalysisRequest(
            project_name=st.session_state["project_name"],
            title=st.session_state["poem_title"],
            original_text=st.session_state["poem_text"],
            lexicon_ids=tuple(selected_lexicons),
            phrase_policy=policy_labels[policy_label],
            minimum_match_requirement=int(minimum_matches),
        )
        with st.spinner("Analyzing locally and preserving the audit trail…"):
            st.session_state["workspace"] = run_workspace_analysis(
                request, preprocessor=_preprocessor()
            )
        st.success("Analysis complete. Start with Overview; use Evidence when you want to inspect why.")
    except (TextImportError, WorkspaceAnalysisError, ValueError) as error:
        st.error(str(error))
    except Exception as error:  # pragma: no cover - defensive UI boundary
        st.error(
            "VerseVAD could not complete this analysis. No source lexicon or original "
            "file was changed. Copy the technical detail below if you report the problem."
        )
        st.code(f"{type(error).__name__}: {error}")

workspace = st.session_state.get("workspace")
if workspace is None:
    st.markdown("### What happens next")
    steps = st.columns(3)
    steps[0].markdown("**1 — Overview**  \nCoverage and a plain-language orientation.")
    steps[1].markdown("**2 — Profiles**  \nComparable VAD plus separate association and intensity views.")
    steps[2].markdown("**3 — Evidence**  \nMatches, phrases, lemmas, and unmatched vocabulary.")
    st.stop()

if (
    st.session_state["poem_text"] != workspace.request.original_text
    or tuple(selected_lexicons) != workspace.request.lexicon_ids
):
    st.warning(
        "The text or lexicon selection has changed since this result was calculated. "
        "Click Analyze this text again before using the results."
    )

st.markdown("---")
st.markdown('<p class="verse-kicker">Current result</p>', unsafe_allow_html=True)
st.header(workspace.document.title)
st.caption(
    f"Text version {workspace.document.text_version_id} · "
    f"Phrase policy: {workspace.request.phrase_policy.value.replace('_', ' ')}"
)

overview_tab, vad_tab, emotion_tab, evidence_tab, download_tab, help_tab = st.tabs(
    ["Overview", "VAD profile", "Emotion profile", "Evidence", "Downloads", "How to read"]
)

with overview_tab:
    coverage = coverage_views(workspace)
    metrics = st.columns(4)
    lexical_tokens = coverage[0].lexical_tokens if coverage else 0
    metrics[0].metric("Lexical tokens", f"{lexical_tokens:,}")
    metrics[1].metric("Lexicons analyzed", len(workspace.results))
    metrics[2].metric("Lines preserved", len(workspace.document.original_text.splitlines()))
    metrics[3].metric("Text checksum", workspace.document.text_sha256[:10] + "…")

    st.markdown(
        '<div class="verse-callout"><strong>Begin here:</strong> Coverage is the '
        "share of eligible vocabulary that found an entry in each lexicon. "
        "Every aggregate below is based only on matched evidence.</div>",
        unsafe_allow_html=True,
    )
    coverage_frame = _frame(
        coverage,
        {
            "lexicon": "Lexicon",
            "matched_tokens": "Matched tokens",
            "lexical_tokens": "Lexical tokens",
            "coverage": "Coverage",
            "matched_types": "Matched types",
            "total_types": "Total types",
            "exact_matches": "Exact",
            "lemma_matches": "Lemma",
            "phrase_matches": "Phrases",
            "note": "Reading note",
        },
    )
    coverage_frame["Coverage"] = coverage_frame["Coverage"].map(_percentage)
    st.dataframe(
        coverage_frame[
            [
                "Lexicon",
                "Matched tokens",
                "Lexical tokens",
                "Coverage",
                "Exact",
                "Lemma",
                "Phrases",
                "Reading note",
            ]
        ],
        hide_index=True,
        width="stretch",
    )
    st.caption(
        "The 60% and 80% coverage bands are orientation aids, not universal scholarly cutoffs."
    )
    st.subheader("How to frame this result")
    for note in overview_notes(workspace):
        st.markdown(f"- {note}")
    warnings = [
        (result.lexicon_metadata.display_name, warning)
        for result in workspace.results
        for warning in result.warnings
    ]
    if warnings:
        with st.expander(f"Warnings and cautions ({len(warnings)})"):
            for lexicon, warning in warnings:
                st.warning(f"{lexicon}: {warning}")

with vad_tab:
    vad = vad_views(workspace)
    if not vad:
        st.info("No VAD lexicon was selected. Choose Warriner or either NRC VAD source to see this view.")
    else:
        st.subheader("Comparable normalized VAD")
        st.write(
            "These means use a derived 0–1 scale so the three VAD sources can be "
            "placed side by side. Higher values mean higher normative ratings on "
            "that dimension among matched observations—not more emotion in the poem."
        )
        vad_frame = _frame(
            vad,
            {
                "lexicon": "Lexicon",
                "matched_observations": "Matched observations",
                "lexical_coverage": "Coverage",
                "normalized_valence": "Valence",
                "normalized_arousal": "Arousal",
                "normalized_dominance": "Dominance",
                "type_valence": "Type valence",
                "type_arousal": "Type arousal",
                "type_dominance": "Type dominance",
                "original_scale": "Original scale",
                "normalization_formula": "Formula",
            },
        )
        st.dataframe(
            vad_frame[
                [
                    "Lexicon",
                    "Matched observations",
                    "Coverage",
                    "Valence",
                    "Arousal",
                    "Dominance",
                ]
            ].style.format(
                {
                    "Coverage": lambda value: _percentage(value),
                    "Valence": lambda value: _decimal(value),
                    "Arousal": lambda value: _decimal(value),
                    "Dominance": lambda value: _decimal(value),
                }
            ),
            hide_index=True,
            width="stretch",
        )
        dimension_order = ["Valence", "Arousal", "Dominance"]
        lexicon_order = vad_frame["Lexicon"].tolist()
        chart_data = vad_frame[["Lexicon", *dimension_order]].melt(
            id_vars="Lexicon",
            var_name="Dimension",
            value_name="Normalized mean",
        )
        chart = (
            alt.Chart(chart_data)
            .mark_bar(size=12)
            .encode(
                x=alt.X(
                    "Normalized mean:Q",
                    scale=alt.Scale(domain=[0, 1]),
                    title="Derived normalized mean (0–1)",
                ),
                y=alt.Y("Lexicon:N", sort=lexicon_order, title=None),
                yOffset=alt.YOffset("Dimension:N", sort=dimension_order),
                color=alt.Color(
                    "Dimension:N",
                    sort=dimension_order,
                    scale=alt.Scale(range=["#a64b2a", "#d18b54", "#456b72"]),
                    title=None,
                ),
                tooltip=[
                    alt.Tooltip("Lexicon:N"),
                    alt.Tooltip("Dimension:N"),
                    alt.Tooltip("Normalized mean:Q", format=".3f"),
                ],
            )
            .properties(height=max(210, 80 * len(vad)))
        )
        st.altair_chart(chart, width="stretch")
        st.caption(
            "Valence: pleasure/positivity. Arousal: activation/excitement. "
            "Dominance: control/power. All are normative lexical ratings."
        )
        with st.expander("Original scales, formulas, and token/type comparison"):
            st.markdown(
                "**Normalization formulas:** Warriner `(x − 1) / 8`; NRC VAD v1 "
                "identity; NRC VAD v2.1 `(x + 1) / 2`. Original values are never overwritten."
            )
            details = []
            result_by_id = {
                result.lexicon_metadata.lexicon_id: result for result in workspace.results
            }
            for row in vad:
                result = result_by_id[row.lexicon_id]
                summary = result.vad_summary
                assert summary is not None
                original = summary.token_weighted_original
                details.append(
                    {
                        "Lexicon": row.lexicon,
                        "Original scale": row.original_scale,
                        "Source valence mean": original.valence.mean,
                        "Source arousal mean": original.arousal.mean,
                        "Source dominance mean": original.dominance.mean,
                        "Token valence (0-1)": row.normalized_valence,
                        "Type valence (0-1)": row.type_valence,
                        "Formula": row.normalization_formula,
                    }
                )
            st.dataframe(details, hide_index=True, width="stretch")

with emotion_tab:
    associations = emotion_association_views(workspace)
    intensities = emotion_intensity_views(workspace)
    if not associations and not intensities:
        st.info("Select NRC Emotion or NRC Emotion Intensity to see this view.")
    if associations:
        st.subheader("Categorical emotion associations")
        st.write(
            "This counts vocabulary associated with each category in NRC Emotion. "
            "One token may belong to several categories, so rates do not sum to 100%."
        )
        association_frame = _frame(
            associations,
            {
                "category": "Category",
                "token_count": "Token count",
                "unique_types": "Unique types",
                "rate_per_lexical_token": "Rate per lexical token",
                "rate_among_emotion_bearing_tokens": "Rate among emotion-bearing tokens",
                "top_terms": "Top contributors",
            },
        )
        st.bar_chart(
            association_frame.set_index("Category")[["Rate per lexical token"]],
            height=300,
        )
        st.dataframe(
            association_frame.style.format(
                {
                    "Rate per lexical token": lambda value: _percentage(value),
                    "Rate among emotion-bearing tokens": lambda value: _percentage(value),
                }
            ),
            hide_index=True,
            width="stretch",
        )
    if intensities:
        st.subheader("Emotion intensity among supplied matches")
        st.write(
            "Prevalence asks how often category-scored vocabulary occurs. Mean "
            "intensity asks how strong the supplied ratings are only among those matches."
        )
        intensity_frame = _frame(
            intensities,
            {
                "category": "Category",
                "token_count": "Matched occurrences",
                "distinct_pairs": "Distinct word-category pairs",
                "prevalence_per_lexical_token": "Prevalence per lexical token",
                "mean_matched_intensity": "Mean matched intensity",
                "median_matched_intensity": "Median",
                "maximum_matched_intensity": "Maximum",
                "top_terms": "Top contributors",
            },
        )
        st.dataframe(
            intensity_frame.style.format(
                {
                    "Prevalence per lexical token": lambda value: _percentage(value),
                    "Mean matched intensity": lambda value: _decimal(value),
                    "Median": lambda value: _decimal(value),
                    "Maximum": lambda value: _decimal(value),
                }
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption("A missing word-category pair remains missing; VerseVAD does not enter a zero.")

with evidence_tab:
    st.subheader("Match evidence")
    st.write(
        "Use this table when you want to know exactly which surface form, lemma, "
        "phrase, or source entry contributed—or why it was suppressed."
    )
    all_matches = match_views(workspace)
    lexicon_filter = st.selectbox(
        "Filter by lexicon",
        options=["All lexicons", *sorted({row.lexicon for row in all_matches})],
        key="evidence_lexicon_filter",
    )
    status_filter = st.multiselect(
        "Match status",
        options=sorted({row.status for row in all_matches}),
        default=["included"],
        key="evidence_status_filter",
    )
    search = st.text_input(
        "Search surface form, matched term, lemma, or context",
        key="evidence_search",
    ).casefold()
    filtered = [
        row
        for row in all_matches
        if (lexicon_filter == "All lexicons" or row.lexicon == lexicon_filter)
        and row.status in status_filter
        and (
            not search
            or search
            in " ".join((row.surface, row.matched_term, row.lemma, row.context)).casefold()
        )
    ]
    match_frame = _frame(
        filtered,
        {
            "lexicon": "Lexicon",
            "surface": "Text surface",
            "line": "Line",
            "stanza": "Stanza",
            "pos": "POS",
            "lemma": "Lemma",
            "matched_term": "Matched entry",
            "method": "Method",
            "status": "Status",
            "value": "Source evidence",
            "context": "Line context",
            "explanation": "Why",
        },
    )
    st.dataframe(match_frame, hide_index=True, width="stretch", height=420)
    st.caption(f"Showing {len(filtered):,} of {len(all_matches):,} audit records.")

    st.subheader("Unmatched vocabulary")
    unmatched = unmatched_views(workspace)
    if unmatched:
        unmatched_frame = _frame(
            unmatched,
            {
                "lexicon": "Lexicon",
                "surface": "Surface form",
                "frequency": "Occurrences",
                "pos": "POS",
                "proposed_lemma": "Model lemma",
                "example_line": "Example line",
                "example_context": "Example context",
            },
        )
        st.dataframe(unmatched_frame, hide_index=True, width="stretch", height=320)
        st.caption(
            "A model lemma is proposed processing evidence, not an approved historical or scholarly mapping."
        )
    else:
        st.success("Every lexical token matched each selected lexicon under this policy.")

with download_tab:
    st.subheader("Readable first, audit trail second")
    st.write(
        "The compact summary is meant to be opened first. The ZIP adds every "
        "detailed table needed to inspect or reproduce the result."
    )
    safe_stem = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in workspace.document.title.strip()
    ).strip("_") or "versevad_analysis"
    column1, column2, column3 = st.columns(3)
    column1.download_button(
        "Download readable summary",
        data=scholar_summary_csv(workspace),
        file_name=f"{safe_stem}_scholar_summary.csv",
        mime="text/csv",
        width="stretch",
        key="download_summary",
    )
    column2.download_button(
        "Download CSV reading guide",
        data=csv_reading_guide(),
        file_name="VerseVAD_CSV_reading_guide.csv",
        mime="text/csv",
        width="stretch",
        key="download_guide",
    )
    column3.download_button(
        "Download full audit bundle",
        data=detailed_export_zip(workspace),
        file_name=f"{safe_stem}_VerseVAD_audit.zip",
        mime="application/zip",
        width="stretch",
        key="download_bundle",
    )
    st.info(
        "The full bundle contains START_HERE.txt, the readable summary, the CSV "
        "guide, match audit, coverage, VAD, association, intensity, comparison, "
        "and reproducibility-manifest files."
    )

with help_tab:
    st.subheader("A practical reading order")
    st.markdown(
        """
        1. **Coverage:** Is enough vocabulary represented to make the aggregate useful?
        2. **Normalized VAD:** Compare source-specific 0–1 means, keeping coverage beside them.
        3. **Emotion associations:** Read category rates as overlapping lexical associations.
        4. **Emotion intensity:** Keep prevalence separate from mean intensity among matches.
        5. **Evidence:** Inspect the terms, lemmas, phrases, and suppressions producing a pattern.
        6. **Manifest:** Use this only when you need provenance or reproducibility details.
        """
    )
    st.subheader("What the main terms mean")
    definitions = [
        ("Coverage", "The share of eligible lexical tokens that found a source entry."),
        ("Token-weighted", "Every matched occurrence contributes, including repetitions."),
        ("Type-weighted", "Each distinct matched lexicon entry contributes once."),
        ("Normalized VAD", "A derived 0-1 version used for legitimate side-by-side VAD comparison."),
        ("Association", "A binary category link; it is not an intensity or contextual interpretation."),
        ("Intensity", "A source rating for a supplied word-category pair; missing pairs stay missing."),
        ("Suppressed component", "A visible unigram candidate not counted because a preferred phrase was selected."),
        ("Lemma fallback", "A model-proposed base form used only after exact matching fails."),
    ]
    st.dataframe(
        pd.DataFrame(definitions, columns=["Term", "Meaning"]),
        hide_index=True,
        width="stretch",
    )
    st.warning(
        "Lexicon matching does not resolve negation, irony, metaphor, voice, "
        "historical sense, authorial intention, or reader response."
    )
