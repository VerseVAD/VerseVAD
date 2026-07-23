"""VerseVAD local one-text, corpus, and lexicon-exploration interface."""

from __future__ import annotations

import hashlib
import importlib
import sys
from dataclasses import asdict
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

import versevad.application as _application_services
import versevad.adapters.nrc_vad as _nrc_vad_services
import versevad.db.repository as _repository_services

# Codex may update the local source while a Streamlit server is still open.
# Streamlit reruns this page but Python normally retains already imported
# service modules, which can momentarily pair a new interface with an older
# application API or adapter policy. Reload only when a required revision is
# absent so an already-open local session activates NRC VAD v1 phrases too.
_application_was_reloaded = (
    not all(
        hasattr(_application_services, name)
        for name in (
            "VAD_DEFINITIONS",
            "vad_cumulative_views",
            "vad_contributor_views",
            "vad_sensitivity_views",
            "part_of_speech_views",
        )
    )
    or getattr(_nrc_vad_services.NrcVadV1Adapter, "adapter_version", "") != "0.3.0"
    or not _nrc_vad_services.NrcVadV1Adapter.configuration.phrase_support
    or getattr(_repository_services, "SCHEMA_VERSION", 0) < 3
)
if _application_was_reloaded:
    # Reload the framework-independent dependency graph in type-definition
    # order. This is used only after Codex updates an already-running local
    # Streamlit process; a normal launch imports each module once.
    for _module_name in (
        "versevad.models",
        "versevad.preprocessing",
        "versevad.stopwords",
        "versevad.analysis.statistics",
        "versevad.adapters.base",
        "versevad.adapters.warriner",
        "versevad.adapters.nrc_vad",
        "versevad.adapters.nrc_emotion",
        "versevad.adapters.nrc_intensity",
        "versevad.adapters",
        "versevad.analysis.phase2",
    ):
        _module = importlib.import_module(_module_name)
        importlib.reload(_module)
    importlib.reload(_application_services)
    for _module_name in (
        "versevad.db.repository",
        "versevad.db",
        "versevad.corpus",
        "versevad.ui.corpus",
    ):
        if _module_name in sys.modules:
            importlib.reload(sys.modules[_module_name])

from versevad import __version__
from versevad.application import (
    AnalysisRequest,
    LEXICON_SPECS,
    TextImportError,
    VAD_DEFINITIONS,
    WorkspaceAnalysisError,
    coverage_views,
    csv_reading_guide,
    decode_uploaded_text,
    detailed_export_zip,
    emotion_association_views,
    emotion_intensity_views,
    match_views,
    overview_notes,
    part_of_speech_views,
    run_workspace_analysis,
    scholar_summary_csv,
    sentiment_association_views,
    unmatched_views,
    vad_contributor_views,
    vad_cumulative_views,
    vad_interpretation_views,
    vad_sensitivity_views,
    vad_views,
)
from versevad.diagnostics import run_self_test
from versevad.models import PhrasePolicy
from versevad.preprocessing import SpacyEnglishPreprocessor
from versevad.ui.stopwords import render_stopword_settings


st.set_page_config(
    page_title="VerseVAD",
    page_icon="V",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit reruns this page when a dependency changes but retains already
# imported dependency modules. Use an explicit revision marker for Explorer
# compatibility fixes so an open local session reloads both the service and UI
# modules exactly once, then retains normal session state on later interactions.
_EXPLORER_RUNTIME_REVISION = "2026-07-22-explorer-3"
_explorer_was_reloaded = (
    st.session_state.get("_explorer_runtime_revision") != _EXPLORER_RUNTIME_REVISION
)
if _explorer_was_reloaded:
    import versevad.explorer as _explorer_services
    import versevad.ui.explorer as _explorer_ui_services

    importlib.reload(_explorer_services)
    importlib.reload(_explorer_ui_services)
    st.session_state["_explorer_runtime_revision"] = _EXPLORER_RUNTIME_REVISION

# Corpus Excel gained a methodology argument after the persistent workspace
# first shipped. An already-open Streamlit process can otherwise retain the
# four-argument exporter while loading the newer five-argument corpus page.
_CORPUS_RUNTIME_REVISION = "2026-07-23-phase5-review-pos-2"
import versevad.exports.corpus_excel as _corpus_excel_services

_corpus_was_reloaded = (
    st.session_state.get("_corpus_runtime_revision") != _CORPUS_RUNTIME_REVISION
    or getattr(_corpus_excel_services, "CORPUS_WORKBOOK_API_VERSION", 0) < 4
)
if _corpus_was_reloaded:
    importlib.reload(_corpus_excel_services)
    if "versevad.ui.corpus" in sys.modules:
        importlib.reload(sys.modules["versevad.ui.corpus"])
    st.session_state["_corpus_runtime_revision"] = _CORPUS_RUNTIME_REVISION

if _application_was_reloaded:
    st.session_state.pop("workspace", None)
if _application_was_reloaded or _explorer_was_reloaded:
    st.session_state.pop("lexicon_explorer_result", None)

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
    #MainMenu, footer { visibility: hidden; }
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


workspace_page = st.segmented_control(
    "Workspace",
    options=["One Poem", "Projects & Corpus", "Lexicon Explorer"],
    default="One Poem",
    selection_mode="single",
    key="workspace_page",
)
workspace_page = workspace_page or "One Poem"
if workspace_page == "Projects & Corpus":
    from versevad.ui.corpus import render_corpus_workspace

    render_corpus_workspace(_preprocessor())
if workspace_page == "Lexicon Explorer":
    from versevad.ui.explorer import render_lexicon_explorer

    render_lexicon_explorer(_preprocessor())


if workspace_page == "One Poem":
    st.session_state.setdefault("project_name", "Temporary private workspace")
    st.session_state.setdefault("poem_title", "")
    st.session_state.setdefault("poem_text", "")
    st.session_state.setdefault("workspace", None)

    with st.sidebar:
        st.markdown("### Local Workspace")
        st.caption(f"VerseVAD {__version__}")
        st.success("Private by design: analysis stays on this computer.")
        st.info(
            "One-poem results last only while the app is open. Download them before "
            "closing, or use Projects & Corpus for persistent local work."
        )
        st.markdown("### Installation Check")
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
        st.subheader("1. Add a Poem")
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
        st.subheader("2. Choose Evidence")
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
                help="Warriner and NRC VAD v2.1 activate exact multiword expressions.",
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
        st.markdown("**Stopword reporting**")
        reporting_columns = st.columns(2)
        show_all_matched = reporting_columns[0].checkbox(
            "Show all-token results",
            value=True,
            key="show_all_matched_results",
        )
        show_stopword_excluded = reporting_columns[1].checkbox(
            "Show stopword-excluded results",
            value=True,
            key="show_stopword_excluded_results",
        )
        st.caption(
            "Stopword exclusion removes common grammatical words from the secondary "
            "analysis only. The complete analysis and token audit remain available."
        )
        with st.expander("Stopword settings"):
            stopword_settings = render_stopword_settings("one_poem")

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
                stopword_mode=stopword_settings.mode,
                protected_stopwords=stopword_settings.protected_words,
                custom_stopword_additions=stopword_settings.custom_additions,
                custom_stopword_removals=stopword_settings.custom_removals,
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
        st.markdown("### What Happens Next")
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

    (
        overview_tab,
        language_tab,
        vad_tab,
        emotion_tab,
        evidence_tab,
        download_tab,
        help_tab,
    ) = st.tabs(
        [
            "Overview",
            "Language Profile",
            "VAD Profile",
            "Emotion Profile",
            "Evidence",
            "Downloads",
            "How to Read",
        ]
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
        if show_stopword_excluded:
            filtered_coverage = [
                {
                    "Lexicon": result.lexicon_metadata.display_name,
                    "Matched non-stopword tokens": result.stopword_coverage.matched_token_count,
                    "Eligible non-stopword tokens": result.stopword_coverage.eligible_token_count,
                    "Content-focused coverage": result.stopword_coverage.lexical_token_coverage,
                    "Excluded matched observations": (
                        result.stopword_coverage.excluded_matched_observation_count
                    ),
                    "Excluded matched types": (
                        result.stopword_coverage.excluded_matched_type_count
                    ),
                }
                for result in workspace.results
                if result.stopword_coverage is not None
            ]
            st.markdown("**Stopwords-excluded coverage**")
            st.dataframe(
                pd.DataFrame(filtered_coverage).style.format(
                    {
                        "Content-focused coverage": lambda value: _percentage(value),
                    }
                ),
                hide_index=True,
                width="stretch",
            )
            st.caption(
                "Content-focused coverage uses eligible non-stopword tokens as its "
                "denominator, so intentional exclusions do not appear as failed matches."
            )
            policy = next(
                (
                    result.stopword_policy
                    for result in workspace.results
                    if result.stopword_policy is not None
                ),
                None,
            )
            if policy is not None:
                with st.expander("Stopword methodology used for this analysis"):
                    excluded_tokens = max(
                        (
                            result.stopword_coverage.excluded_matched_token_count
                            for result in workspace.results
                            if result.stopword_coverage is not None
                        ),
                        default=0,
                    )
                    st.write(
                        f"Source: **{policy.source}** · library "
                        f"**{policy.library_version}** · active exclusions "
                        f"**{len(policy.active_words):,}** · excluded matched tokens "
                        f"in the current text (maximum across selected lexicons): "
                        f"**{excluded_tokens:,}**"
                    )
                    st.write(
                        "**Protected words:** "
                        + ", ".join(policy.protected_words)
                    )
                    st.write(
                        "**Custom additions:** "
                        + (", ".join(policy.custom_additions) or "none")
                    )
                    st.write(
                        "**Custom removals:** "
                        + (", ".join(policy.custom_removals) or "none")
                    )
        st.caption(
            "The 60% and 80% coverage bands are orientation aids, not universal scholarly cutoffs."
        )
        st.subheader("How to Frame This Result")
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

    with language_tab:
        st.subheader("Part-of-Speech Profile")
        st.write(
            "This is a grammatical profile of all eligible lexical token occurrences, "
            "independent of affective-lexicon coverage. The count is the number of "
            "occurrences assigned to a category; the share divides that count by all "
            "eligible lexical tokens in this text."
        )
        pos_rows = part_of_speech_views(workspace)
        if pos_rows:
            pos_frame = _frame(
                pos_rows,
                {
                    "tag": "Universal POS tag",
                    "category": "Part of speech",
                    "token_count": "Token count",
                    "share_of_lexical_tokens": "Share of lexical tokens",
                    "unique_type_count": "Unique normalized types",
                    "example_forms": "Examples",
                    "lexical_token_denominator": "Lexical-token denominator",
                },
            )
            st.bar_chart(
                pos_frame.set_index("Part of speech")[["Share of lexical tokens"]],
                height=320,
            )
            st.dataframe(
                pos_frame.style.format(
                    {"Share of lexical tokens": lambda value: _percentage(value)}
                ),
                hide_index=True,
                width="stretch",
            )
            st.warning(
                "Part-of-speech labels are generated by the installed English model. "
                "Poetic syntax, archaic forms, fragments, and deliberate ambiguity can "
                "produce uncertain labels; inspect the token-level Evidence table when "
                "a distinction matters."
            )
        else:
            st.info("This text contains no eligible lexical tokens to profile.")

    with vad_tab:
        visible_vad_views = set()
        if show_all_matched:
            visible_vad_views.add("All matched tokens")
        if show_stopword_excluded:
            visible_vad_views.add("Stopwords excluded")
        vad = [
            row
            for row in vad_views(workspace)
            if row.analysis_view in visible_vad_views
        ]
        if not vad:
            if not visible_vad_views:
                st.info("Enable at least one stopword-reporting view in the settings above.")
            else:
                st.info("No VAD lexicon was selected. Choose Warriner or either NRC VAD source to see this view.")
        else:
            st.subheader("Parallel Normalized VAD Views")
            st.write(
                "These means use a derived 0–1 scale so the three VAD sources can be "
                "placed side by side. Higher values mean higher normative ratings on "
                "that dimension among matched observations—not more emotion in the poem."
            )
            vad_frame = _frame(
                vad,
                {
                    "lexicon": "Lexicon",
                    "analysis_view": "Analysis view",
                    "matched_observations": "Matched observations",
                    "matched_types": "Matched types",
                    "eligible_tokens": "Eligible tokens",
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
                        "Analysis view",
                        "Matched observations",
                        "Matched types",
                        "Eligible tokens",
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
            vad_frame["Lexicon and view"] = (
                vad_frame["Lexicon"] + " · " + vad_frame["Analysis view"]
            )
            lexicon_order = vad_frame["Lexicon and view"].tolist()
            chart_data = vad_frame[
                ["Lexicon", "Analysis view", "Lexicon and view", *dimension_order]
            ].melt(
                id_vars=["Lexicon", "Analysis view", "Lexicon and view"],
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
                    y=alt.Y("Lexicon and view:N", sort=lexicon_order, title=None),
                    yOffset=alt.YOffset("Dimension:N", sort=dimension_order),
                    color=alt.Color(
                        "Dimension:N",
                        sort=dimension_order,
                        scale=alt.Scale(range=["#a64b2a", "#d18b54", "#456b72"]),
                        title=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Lexicon:N"),
                        alt.Tooltip("Analysis view:N"),
                        alt.Tooltip("Dimension:N"),
                        alt.Tooltip("Normalized mean:Q", format=".3f"),
                    ],
                )
                .properties(height=max(210, 80 * len(vad)))
            )
            st.altair_chart(chart, width="stretch")
            st.caption(
                "All three dimensions are normative lexical ratings. They do not identify "
                "the poem's emotion or predict an individual reader's response."
            )
            st.subheader("What Valence, Arousal, and Dominance Mean")
            definition_columns = st.columns(3)
            for column, dimension in zip(
                definition_columns,
                ("valence", "arousal", "dominance"),
                strict=True,
            ):
                with column:
                    st.markdown(f"**{dimension.title()}**")
                    st.write(VAD_DEFINITIONS[dimension])

            interpretations = [
                row
                for row in vad_interpretation_views(workspace)
                if row.analysis_view in visible_vad_views
            ]
            interpretation_lexicon = st.selectbox(
                "Explain results from",
                options=list(dict.fromkeys(row.lexicon for row in vad)),
                key="interpretation_lexicon",
            )
            for explanation in interpretations:
                if explanation.lexicon == interpretation_lexicon:
                    st.markdown(
                        f"**{explanation.analysis_view} · "
                        f"{explanation.dimension.title()}:** {explanation.explanation}"
                    )

            st.subheader("Repetition-Sensitive and Vocabulary-Sensitive Means")
            st.write(
                "Token-weighted means count every included occurrence, so repetition matters. "
                "Type-weighted means count each distinct matched lexicon entry once, so they "
                "describe the breadth of the matched vocabulary. Both use the same 0–1 display scale."
            )
            weighting_details = []
            for row in vad:
                weighting_details.extend(
                    (
                        {
                            "Lexicon": row.lexicon,
                            "Analysis view": row.analysis_view,
                            "Weighting": "Token-weighted",
                            "Valence": row.normalized_valence,
                            "Arousal": row.normalized_arousal,
                            "Dominance": row.normalized_dominance,
                        },
                        {
                            "Lexicon": row.lexicon,
                            "Analysis view": row.analysis_view,
                            "Weighting": "Type-weighted",
                            "Valence": row.type_valence,
                            "Arousal": row.type_arousal,
                            "Dominance": row.type_dominance,
                        },
                    )
                )
            st.dataframe(
                pd.DataFrame(weighting_details).style.format(
                    {dimension: lambda value: _decimal(value) for dimension in dimension_order}
                ),
                hide_index=True,
                width="stretch",
            )

            dispersion_rows = []
            for result in workspace.results:
                summary = result.vad_summary
                if summary is None:
                    continue
                groups = (
                    (
                        "All matched tokens",
                        "Token-weighted",
                        summary.token_weighted_normalized,
                    ),
                    (
                        "All matched tokens",
                        "Type-weighted",
                        summary.type_weighted_normalized,
                    ),
                    (
                        "Stopwords excluded",
                        "Token-weighted",
                        summary.stopword_excluded_token_weighted_normalized,
                    ),
                    (
                        "Stopwords excluded",
                        "Type-weighted",
                        summary.stopword_excluded_type_weighted_normalized,
                    ),
                )
                for analysis_view, weighting, group in groups:
                    if group is None or analysis_view not in visible_vad_views:
                        continue
                    for dimension, statistics in group.by_dimension().items():
                        dispersion_rows.append(
                            {
                                "Lexicon": result.lexicon_metadata.display_name,
                                "Analysis view": analysis_view,
                                "Weighting": weighting,
                                "Dimension": dimension.title(),
                                "Count": statistics.count,
                                "Population standard deviation": (
                                    statistics.population_standard_deviation
                                ),
                            }
                        )
            with st.expander("Dispersion of matched ratings"):
                st.write(
                    "Population standard deviation describes how widely the matched "
                    "lexicon ratings vary around their mean. It is not the source "
                    "lexicon's rater-level uncertainty."
                )
                st.dataframe(
                    pd.DataFrame(dispersion_rows).style.format(
                        {"Population standard deviation": lambda value: _decimal(value)}
                    ),
                    hide_index=True,
                    width="stretch",
                )

            st.subheader("Stopword Sensitivity")
            st.write(
                "Stopword sensitivity is the stopword-excluded mean minus the "
                "all-matched mean. A large absolute difference indicates that common "
                "grammatical words materially influence the aggregate; it does not "
                "make either view more accurate."
            )
            sensitivity_frame = _frame(
                vad_sensitivity_views(workspace),
                {
                    "lexicon": "Lexicon",
                    "weighting": "Weighting",
                    "dimension": "Dimension",
                    "all_matched_mean": "All matched tokens",
                    "stopwords_excluded_mean": "Stopwords excluded",
                    "difference": "Difference",
                },
            )
            sensitivity_frame["Dimension"] = sensitivity_frame["Dimension"].str.title()
            st.dataframe(
                sensitivity_frame.style.format(
                    {
                        "All matched tokens": lambda value: _decimal(value),
                        "Stopwords excluded": lambda value: _decimal(value),
                        "Difference": lambda value: (
                            "—" if pd.isna(value) else f"{value:+.3f}"
                        ),
                    }
                ),
                hide_index=True,
                width="stretch",
            )

            st.subheader("Cumulative Normative Lexical Load")
            st.write(
                "These token totals are deliberately sensitive to length and repetition. "
                "The absolute midpoint load sums each matched rating's distance from 0.5; "
                "above and below loads preserve direction, while net load lets them offset. "
                "This reports encountered lexical evidence—not a measured load on a reader."
            )
            cumulative = [
                row
                for row in vad_cumulative_views(workspace)
                if row.analysis_view in visible_vad_views
            ]
            cumulative_frame = _frame(
                cumulative,
                {
                    "lexicon": "Lexicon",
                    "analysis_view": "Analysis view",
                    "dimension": "Dimension",
                    "matched_observations": "Matched observations",
                    "lexical_coverage": "Coverage",
                    "rating_total": "Rating total",
                    "above_midpoint_deviation": "Above-midpoint load",
                    "below_midpoint_deviation": "Below-midpoint load",
                    "net_midpoint_deviation": "Net midpoint load",
                    "absolute_midpoint_deviation": "Absolute midpoint load",
                },
            )
            cumulative_frame["Dimension"] = cumulative_frame["Dimension"].str.title()
            st.dataframe(
                cumulative_frame[
                    [
                        "Lexicon",
                        "Analysis view",
                        "Dimension",
                        "Matched observations",
                        "Coverage",
                        "Rating total",
                        "Above-midpoint load",
                        "Below-midpoint load",
                        "Net midpoint load",
                        "Absolute midpoint load",
                    ]
                ].style.format(
                    {
                        "Coverage": lambda value: _percentage(value),
                        "Rating total": "{:.3f}",
                        "Above-midpoint load": "{:.3f}",
                        "Below-midpoint load": "{:.3f}",
                        "Net midpoint load": "{:.3f}",
                        "Absolute midpoint load": "{:.3f}",
                    }
                ),
                hide_index=True,
                width="stretch",
            )

            st.subheader("Top Contributors to Each Mean")
            st.write(
                "Signed contribution is frequency × (normalized rating − 0.5). "
                "This midpoint-centered calculation shows how repetition and distance "
                "from the midpoint combine. For arousal and dominance, read the sign "
                "as weighted deviation rather than positive or negative emotion."
            )
            contributor_view = st.selectbox(
                "Contributor analysis view",
                options=sorted(visible_vad_views),
                key="contributor_analysis_view",
            )
            contributor_dimension = st.selectbox(
                "Contributor dimension",
                options=["valence", "arousal", "dominance"],
                format_func=str.title,
                key="contributor_dimension",
            )
            contributors = [
                row
                for row in vad_contributor_views(workspace)
                if row.dimension == contributor_dimension
                and row.analysis_view == contributor_view
            ]
            contributor_frame = _frame(
                contributors,
                {
                    "lexicon": "Lexicon",
                    "analysis_view": "Analysis view",
                    "term": "Matched entry",
                    "surface_forms": "Surface forms",
                    "observations": "Occurrences",
                    "normalized_rating": "Normalized rating",
                    "midpoint_deviation_per_occurrence": "Deviation per occurrence",
                    "signed_contribution": "Signed contribution",
                    "absolute_contribution": "Absolute contribution",
                    "direction": "Direction",
                    "stopword_status": "Stopword status",
                    "example_surface": "Example surface",
                    "example_line": "Line",
                    "match_method": "Method",
                },
            )
            if contributor_frame.empty:
                st.info("No contributor ranking is available for this dimension.")
            else:
                st.dataframe(
                    contributor_frame[
                        [
                            "Lexicon",
                            "Analysis view",
                            "Matched entry",
                            "Surface forms",
                            "Occurrences",
                            "Normalized rating",
                            "Deviation per occurrence",
                            "Signed contribution",
                            "Absolute contribution",
                            "Direction",
                            "Stopword status",
                            "Example surface",
                            "Line",
                            "Method",
                        ]
                    ].style.format(
                        {
                            "Normalized rating": "{:.3f}",
                            "Deviation per occurrence": "{:+.3f}",
                            "Signed contribution": "{:+.3f}",
                            "Absolute contribution": "{:.3f}",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )

            with st.expander("Original source scales and normalization formulas"):
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
                    original = (
                        summary.token_weighted_original
                        if row.analysis_view == "All matched tokens"
                        else summary.stopword_excluded_token_weighted_original
                    )
                    if original is None:
                        continue
                    details.append(
                        {
                            "Lexicon": row.lexicon,
                            "Analysis view": row.analysis_view,
                            "Original scale": row.original_scale,
                            "Source valence mean": original.valence.mean,
                            "Source arousal mean": original.arousal.mean,
                            "Source dominance mean": original.dominance.mean,
                            "Formula": row.normalization_formula,
                        }
                    )
                st.dataframe(details, hide_index=True, width="stretch")

    with emotion_tab:
        associations = emotion_association_views(workspace)
        sentiments = sentiment_association_views(workspace)
        intensities = emotion_intensity_views(workspace)
        if not associations and not sentiments and not intensities:
            st.info("Select NRC Emotion or NRC Emotion Intensity to see this view.")
        if associations:
            st.subheader("Eight Emotion Associations")
            st.write(
                "This counts vocabulary associated with anger, anticipation, disgust, "
                "fear, joy, sadness, surprise, and trust in NRC Emotion. One token may "
                "belong to several categories, so rates do not sum to 100%."
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
        if sentiments:
            st.subheader("Positive and Negative Sentiment Associations")
            st.write(
                "Positive and negative are broad sentiment labels, so VerseVAD reports "
                "them separately from the eight emotion categories. One token may have "
                "more than one source association, and these rates need not sum to 100%."
            )
            sentiment_frame = _frame(
                sentiments,
                {
                    "category": "Sentiment",
                    "token_count": "Token count",
                    "unique_types": "Unique types",
                    "rate_per_lexical_token": "Rate per lexical token",
                    "rate_among_emotion_bearing_tokens": "Rate among association-bearing tokens",
                    "top_terms": "Top contributors",
                },
            )
            st.bar_chart(
                sentiment_frame.set_index("Sentiment")[["Rate per lexical token"]],
                height=220,
            )
            st.dataframe(
                sentiment_frame.style.format(
                    {
                        "Rate per lexical token": lambda value: _percentage(value),
                        "Rate among association-bearing tokens": lambda value: _percentage(value),
                    }
                ),
                hide_index=True,
                width="stretch",
            )
        if intensities:
            st.subheader("Emotion Intensity Among Supplied Matches")
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
        st.subheader("Match Evidence")
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
        stopword_filter = st.multiselect(
            "Stopword status",
            options=sorted({row.stopword_status for row in all_matches}),
            default=sorted({row.stopword_status for row in all_matches}),
            key="evidence_stopword_filter",
        )
        only_excluded_stopwords = st.checkbox(
            "Show only matched observations excluded from the stopword-filtered view",
            value=False,
            key="evidence_only_excluded_stopwords",
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
            and row.stopword_status in stopword_filter
            and (
                not only_excluded_stopwords
                or (row.included_in_full and not row.included_in_filtered)
            )
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
                "normalized": "Normalized form",
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
                "stopword_status": "Stopword status",
                "included_in_full": "Included in full",
                "included_in_filtered": "Included in filtered",
                "stopword_exclusion_reason": "Stopword decision",
            },
        )
        st.dataframe(match_frame, hide_index=True, width="stretch", height=420)
        st.caption(f"Showing {len(filtered):,} of {len(all_matches):,} audit records.")

        st.subheader("Unmatched Vocabulary")
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
        st.subheader("Readable First, Audit Trail Second")
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
            "reproducibility-manifest, and complete JSON result files."
        )

    with help_tab:
        st.subheader("A Practical Reading Order")
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
        st.subheader("What the Main Terms Mean")
        definitions = [
            ("Coverage", "The share of eligible lexical tokens that found a source entry."),
            ("Token-weighted", "Every matched occurrence contributes, including repetitions."),
            ("Type-weighted", "Each distinct matched lexicon entry contributes once."),
            ("Work-weighted corpus", "Each eligible work contributes one work-level mean regardless of length."),
            ("Cumulative lexical load", "A length-sensitive sum of matched normative ratings or midpoint deviations."),
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
