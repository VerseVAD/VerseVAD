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
            "detailed_part_of_speech_views",
            "RESOURCE_ROOT",
            "FrequencyConfiguration",
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
        "versevad.adapters.concreteness",
        "versevad.adapters.subtlex_us",
        "versevad.adapters",
        "versevad.analysis.phase2",
        "versevad.lexical_semantic.concreteness",
        "versevad.lexical_semantic.frequency",
        "versevad.exports.concreteness",
        "versevad.exports.frequency",
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
    RESOURCE_ROOT,
    TextImportError,
    VAD_DEFINITIONS,
    WorkspaceAnalysisError,
    coverage_views,
    csv_reading_guide,
    decode_uploaded_text,
    detailed_export_zip,
    detailed_part_of_speech_views,
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
from versevad.lexical_semantic.concreteness import (
    ConcretenessConfiguration,
    ConcretenessModule,
)
from versevad.lexical_semantic.frequency import (
    FrequencyConfiguration,
    FrequencyModule,
)
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
_CORPUS_RUNTIME_REVISION = "2026-07-23-phase5-review-pos-3"
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

        st.markdown("**Optional lexical-semantic modules**")
        concreteness_status = ConcretenessModule(
            RESOURCE_ROOT
        ).validate_resources()[0]
        include_concreteness = st.checkbox(
            "Concreteness profile (Brysbaert et al. ratings)",
            value=False,
            disabled=not concreteness_status.available,
            key="include_concreteness",
            help=(
                "Measures matched normative lexical concreteness on the source "
                "1-5 scale. The module is independent of the affective lexicons."
            ),
        )
        if concreteness_status.available:
            st.caption(
                "Available locally. The source workbook is read in place, its "
                "SHA-256 is recorded, and it is not added to source control."
            )
        else:
            st.info(concreteness_status.message)

        frequency_status = FrequencyModule(RESOURCE_ROOT).validate_resources()[0]
        include_frequency = st.checkbox(
            "Frequency & rarity profile (SUBTLEX-US Zipf)",
            value=False,
            disabled=not frequency_status.available,
            key="include_frequency",
            help=(
                "Describes corpus-relative word-form frequency using the "
                "official local SUBTLEX-US Zipf workbook. No wordfreq fallback "
                "is used."
            ),
        )
        if frequency_status.available:
            st.caption(
                "Available locally. Zipf values come from the pinned official "
                "SUBTLEX-US workbook, read in place with its SHA-256 recorded."
            )
        else:
            st.info(frequency_status.message)

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
            st.markdown("**Concreteness settings**")
            concreteness_columns = st.columns(2)
            highly_abstract_max = concreteness_columns[0].number_input(
                "Highly abstract band: rating at or below",
                min_value=1.0,
                max_value=4.9,
                value=2.0,
                step=0.1,
                key="concreteness_abstract_max",
                disabled=not include_concreteness,
            )
            highly_concrete_min = concreteness_columns[1].number_input(
                "Highly concrete band: rating at or above",
                min_value=1.1,
                max_value=5.0,
                value=4.0,
                step=0.1,
                key="concreteness_concrete_min",
                disabled=not include_concreteness,
            )
            concreteness_policy_columns = st.columns(2)
            exclude_concreteness_proper_nouns = concreteness_policy_columns[
                0
            ].checkbox(
                "Exclude model-tagged proper nouns",
                value=True,
                key="concreteness_exclude_proper",
                disabled=not include_concreteness,
            )
            activate_concreteness_phrases = concreteness_policy_columns[
                1
            ].checkbox(
                "Activate exact two-word source expressions",
                value=True,
                key="concreteness_phrases",
                disabled=not include_concreteness,
            )
            concreteness_warning_threshold = st.number_input(
                "Concreteness rated-token coverage caution threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.05,
                key="concreteness_coverage_warning",
                disabled=not include_concreteness,
            )
            st.caption(
                "The extreme bands and coverage caution are configurable "
                "VerseVAD orientation aids, not categories or validity cutoffs "
                "defined by the source paper."
            )
            st.markdown("**Frequency & rarity settings**")
            frequency_threshold_columns = st.columns(4)
            rare_below = frequency_threshold_columns[0].number_input(
                "Rare: Zipf below",
                min_value=1.0,
                max_value=7.0,
                value=3.0,
                step=0.1,
                key="frequency_rare_below",
                disabled=not include_frequency,
            )
            uncommon_below = frequency_threshold_columns[1].number_input(
                "Uncommon: below",
                min_value=1.1,
                max_value=7.2,
                value=4.0,
                step=0.1,
                key="frequency_uncommon_below",
                disabled=not include_frequency,
            )
            moderately_common_below = frequency_threshold_columns[
                2
            ].number_input(
                "Moderately common: below",
                min_value=1.2,
                max_value=7.4,
                value=5.0,
                step=0.1,
                key="frequency_moderate_below",
                disabled=not include_frequency,
            )
            very_common_min = frequency_threshold_columns[3].number_input(
                "Very common: at or above",
                min_value=1.3,
                max_value=8.0,
                value=6.0,
                step=0.1,
                key="frequency_very_common_min",
                disabled=not include_frequency,
            )
            frequency_policy_columns = st.columns(3)
            exclude_frequency_proper_nouns = frequency_policy_columns[
                0
            ].checkbox(
                "Exclude frequency proper nouns",
                value=True,
                key="frequency_exclude_proper",
                disabled=not include_frequency,
            )
            frequency_content_words_only = frequency_policy_columns[
                1
            ].checkbox(
                "Content words only",
                value=False,
                key="frequency_content_words_only",
                disabled=not include_frequency,
                help=(
                    "Optional and off by default. Limits eligible tokens to "
                    "model-tagged NOUN, VERB, ADJ, and ADV; excludes determiners, "
                    "prepositions, conjunctions, pronouns, auxiliaries, and "
                    "punctuation."
                ),
            )
            enable_frequency_lemma_fallback = frequency_policy_columns[
                2
            ].checkbox(
                "Allow explicit lemma fallback",
                value=True,
                key="frequency_lemma_fallback",
                disabled=not include_frequency,
            )
            frequency_warning_threshold = st.number_input(
                "Frequency matched-token coverage caution threshold",
                min_value=0.0,
                max_value=1.0,
                value=0.6,
                step=0.05,
                key="frequency_coverage_warning",
                disabled=not include_frequency,
            )
            st.caption(
                "Median Zipf is primary. Each one-point increase represents "
                "roughly ten times greater corpus frequency. The configurable "
                "bands are orientation aids rather than universal categories."
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

    concreteness_configuration_error = ""
    try:
        concreteness_configuration = ConcretenessConfiguration(
            highly_abstract_max=float(highly_abstract_max),
            highly_concrete_min=float(highly_concrete_min),
            exclude_proper_nouns=exclude_concreteness_proper_nouns,
            activate_multiword_expressions=activate_concreteness_phrases,
            minimum_rated_tokens=int(minimum_matches),
            low_coverage_warning_threshold=float(
                concreteness_warning_threshold
            ),
        )
    except ValueError as error:
        concreteness_configuration_error = str(error)
        concreteness_configuration = ConcretenessConfiguration()
        if include_concreteness:
            st.warning(concreteness_configuration_error)

    frequency_configuration_error = ""
    try:
        frequency_configuration = FrequencyConfiguration(
            rare_below=float(rare_below),
            uncommon_below=float(uncommon_below),
            moderately_common_below=float(moderately_common_below),
            very_common_min=float(very_common_min),
            exclude_proper_nouns=exclude_frequency_proper_nouns,
            content_words_only=frequency_content_words_only,
            enable_lemma_fallback=enable_frequency_lemma_fallback,
            minimum_matched_tokens=int(minimum_matches),
            low_coverage_warning_threshold=float(frequency_warning_threshold),
        )
    except ValueError as error:
        frequency_configuration_error = str(error)
        frequency_configuration = FrequencyConfiguration()
        if include_frequency:
            st.warning(frequency_configuration_error)

    if analyze_clicked:
        try:
            if concreteness_configuration_error:
                raise ValueError(concreteness_configuration_error)
            if frequency_configuration_error:
                raise ValueError(frequency_configuration_error)
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
                include_concreteness=include_concreteness,
                concreteness_configuration=concreteness_configuration,
                include_frequency=include_frequency,
                frequency_configuration=frequency_configuration,
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
        or include_concreteness != workspace.request.include_concreteness
        or include_frequency != workspace.request.include_frequency
        or (
            include_concreteness
            and concreteness_configuration
            != workspace.request.concreteness_configuration
        )
        or (
            include_frequency
            and frequency_configuration
            != workspace.request.frequency_configuration
        )
    ):
        st.warning(
            "The text, lexicon selection, or optional-module settings have "
            "changed since this result was calculated. "
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
        concreteness_tab,
        frequency_tab,
        vad_tab,
        emotion_tab,
        evidence_tab,
        download_tab,
        help_tab,
    ) = st.tabs(
        [
            "Overview",
            "Language Profile",
            "Concreteness Profile",
            "Frequency & Rarity",
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
        lexical_tokens = (
            workspace.poem_document.coverage.lexical_token_count
            if workspace.poem_document is not None
            else (coverage[0].lexical_tokens if coverage else 0)
        )
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
        if coverage:
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
            coverage_frame["Coverage"] = coverage_frame["Coverage"].map(
                _percentage
            )
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
        else:
            st.info(
                "No affective lexicon was selected for this result. Optional "
                "module coverage is reported separately below."
            )
        if workspace.frequency is not None:
            frequency_summary = workspace.frequency.summary
            st.markdown("**SUBTLEX-US frequency coverage**")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Resource": workspace.frequency.resource_status.display_name,
                            "Scope": frequency_summary.scope_label,
                            "Matched tokens": frequency_summary.matched_token_count,
                            "Eligible tokens": frequency_summary.eligible_token_count,
                            "Matched-token coverage": frequency_summary.token_coverage,
                            "Matched unique words": (
                                frequency_summary.matched_unique_type_count
                            ),
                            "Eligible unique words": (
                                frequency_summary.eligible_unique_type_count
                            ),
                            "Unique-word coverage": (
                                frequency_summary.unique_type_coverage
                            ),
                        }
                    ]
                ).style.format(
                    {
                        "Matched-token coverage": lambda value: _percentage(value),
                        "Unique-word coverage": lambda value: _percentage(value),
                    }
                ),
                hide_index=True,
                width="stretch",
            )
        if workspace.concreteness is not None:
            concrete_summary = workspace.concreteness.summary
            st.markdown("**Concreteness coverage**")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Resource": (
                                workspace.concreteness.resource_status.display_name
                            ),
                            "Rated tokens": concrete_summary.rated_token_count,
                            "Eligible tokens": concrete_summary.eligible_token_count,
                            "Rated-token coverage": (
                                concrete_summary.token_coverage
                            ),
                            "Rated unique words": (
                                concrete_summary.rated_unique_type_count
                            ),
                            "Eligible unique words": (
                                concrete_summary.eligible_unique_type_count
                            ),
                            "Unique-word coverage": (
                                concrete_summary.unique_type_coverage
                            ),
                        }
                    ]
                ).style.format(
                    {
                        "Rated-token coverage": lambda value: _percentage(value),
                        "Unique-word coverage": lambda value: _percentage(value),
                    }
                ),
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
            if filtered_coverage:
                st.markdown("**Stopwords-excluded coverage**")
                st.dataframe(
                    pd.DataFrame(filtered_coverage).style.format(
                        {
                            "Content-focused coverage": lambda value: _percentage(
                                value
                            ),
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
                st.caption(
                    "Content-focused coverage uses eligible non-stopword tokens as "
                    "its denominator, so intentional exclusions do not appear as "
                    "failed matches."
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
        if workspace.concreteness is not None:
            warnings.extend(
                (
                    "Concreteness",
                    warning.message,
                )
                for warning in workspace.concreteness.module_result.warnings
            )
        if workspace.frequency is not None:
            warnings.extend(
                (
                    "Frequency",
                    warning.message,
                )
                for warning in workspace.frequency.module_result.warnings
            )
        if warnings:
            with st.expander(f"Warnings and cautions ({len(warnings)})"):
                for lexicon, warning in warnings:
                    st.warning(f"{lexicon}: {warning}")

    with language_tab:
        poem_document = workspace.poem_document
        if poem_document is not None:
            st.subheader("Shared Processing Record")
            st.write(
                "This is the reusable structural and linguistic representation "
                "created once for the text and shared by the selected analyses. "
                "The original text remains unchanged; normalized lookup forms and "
                "model annotations are stored separately."
            )
            structure_columns = st.columns(5)
            structure_columns[0].metric("Stanzas", len(poem_document.stanzas))
            structure_columns[1].metric("Physical lines", len(poem_document.lines))
            structure_columns[2].metric(
                "Model sentences", poem_document.coverage.sentence_count
            )
            structure_columns[3].metric(
                "Tokens", poem_document.coverage.total_token_count
            )
            structure_columns[4].metric(
                "Lexical tokens", poem_document.coverage.lexical_token_count
            )
            st.write(
                f"**Processing recipe:** `{poem_document.configuration.recipe_id}` "
                f"| **configuration:** "
                f"`{poem_document.configuration.configuration_id}` "
                f"| **pipeline:** `{poem_document.preprocessing.pipeline_name}` "
                f"{poem_document.preprocessing.pipeline_version} "
                f"| **dependency coverage:** "
                f"{_percentage(poem_document.coverage.dependency_annotation_rate)} "
                f"| **NER:** "
                f"{'enabled' if poem_document.configuration.enable_ner else 'disabled'}"
            )
            if not poem_document.coverage.model_vocabulary_available:
                st.info(
                    "Model-vocabulary OOV reporting is unavailable because the "
                    "installed small English model has no static vectors. This does "
                    "not affect named-resource coverage: each lexicon or later "
                    "research dataset reports its own unmatched terms separately."
                )
            with st.expander(
                f"Processing warnings and cautions ({len(poem_document.warnings)})"
            ):
                for warning in poem_document.warnings:
                    if warning.severity.value == "information":
                        st.info(warning.message)
                    else:
                        st.warning(warning.message)

        st.subheader("Part-of-Speech Profile")
        st.write(
            "This is a grammatical profile of all eligible lexical token occurrences, "
            "independent of affective-lexicon coverage. The count is the number of "
            "occurrences assigned to a category; the share divides that count by all "
            "eligible lexical tokens in this text. The displayed Noun category combines "
            "the model's common-noun (NOUN) and proper-noun (PROPN) tags; Verb "
            "combines main-verb (VERB) and auxiliary/copular (AUX) tags."
        )
        pos_rows = part_of_speech_views(workspace)
        if pos_rows:
            pos_frame = _frame(
                pos_rows,
                {
                    "tag": "Source POS tag(s)",
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
            st.subheader("Detailed Model-Tag Breakdown")
            st.write(
                "This second table preserves the installed model's Universal "
                "Dependencies distinctions. Use it to audit how the broad Noun and "
                "Verb rows were composed."
            )
            detailed_pos_frame = _frame(
                detailed_part_of_speech_views(workspace),
                {
                    "tag": "Universal POS tag",
                    "category": "Detailed category",
                    "token_count": "Token count",
                    "share_of_lexical_tokens": "Share of lexical tokens",
                    "unique_type_count": "Unique normalized types",
                    "example_forms": "Examples",
                    "lexical_token_denominator": "Lexical-token denominator",
                },
            )
            st.dataframe(
                detailed_pos_frame.style.format(
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

    with concreteness_tab:
        concreteness = workspace.concreteness
        if concreteness is None:
            st.info(
                "Concreteness was not selected for this result. Enable the "
                "optional Concreteness profile under Choose Evidence, then run "
                "the analysis again."
            )
            if not concreteness_status.available:
                st.warning(concreteness_status.message)
        else:
            summary = concreteness.summary
            st.subheader("Normative Lexical Concreteness")
            st.write(
                "These values summarize matched Brysbaert, Warriner, and "
                "Kuperman ratings. On the source scale, 1 is very abstract "
                "(language-based) and 5 is very concrete (experience-based). "
                "They describe normative lexical evidence, not the poem's "
                "quality, imagery success, readability, intelligence, or "
                "comprehensibility."
            )
            headline = st.columns(6)
            headline[0].metric("Mean", _decimal(summary.statistics.mean))
            headline[1].metric("Median", _decimal(summary.statistics.median))
            headline[2].metric(
                "Population SD",
                _decimal(summary.statistics.population_standard_deviation),
            )
            headline[3].metric(
                "IQR",
                _decimal(summary.interquartile_range),
            )
            headline[4].metric(
                "Rated-token coverage",
                _percentage(summary.token_coverage),
            )
            headline[5].metric(
                "Unique-word coverage",
                _percentage(summary.unique_type_coverage),
            )
            st.caption(
                f"{summary.rated_token_count:,} of "
                f"{summary.eligible_token_count:,} eligible token occurrences "
                f"and {summary.rated_unique_type_count:,} of "
                f"{summary.eligible_unique_type_count:,} unique normalized "
                "surface types were rated. Unmatched values remain missing."
            )

            band_columns = st.columns(2)
            band_columns[0].metric(
                f"Rating >= {summary.highly_concrete_min:g}",
                _percentage(summary.highly_concrete_proportion),
                help=(
                    "Configurable VerseVAD orientation band among rated token "
                    "occurrences; not a category defined by the source paper."
                ),
            )
            band_columns[1].metric(
                f"Rating <= {summary.highly_abstract_max:g}",
                _percentage(summary.highly_abstract_proportion),
                help=(
                    "Configurable VerseVAD orientation band among rated token "
                    "occurrences; not a category defined by the source paper."
                ),
            )
            st.caption(
                "The extreme bands are configurable display aids. Values between "
                "them remain part of the full continuous 1-5 distribution."
            )

            if concreteness.module_result.warnings:
                with st.expander(
                    "Concreteness warnings and method notices "
                    f"({len(concreteness.module_result.warnings)})"
                ):
                    for warning in concreteness.module_result.warnings:
                        if warning.severity.value == "information":
                            st.info(warning.message)
                        else:
                            st.warning(warning.message)

            rated_lines = [
                group
                for group in concreteness.line_summaries
                if group.statistics.mean is not None
            ]
            st.subheader("Physical-Line Profile")
            if rated_lines:
                line_frame = pd.DataFrame(
                    [
                        {
                            "Line": group.ordinal,
                            "Mean normative concreteness": group.statistics.mean,
                            "Median": group.statistics.median,
                            "Rated tokens": group.rated_token_count,
                            "Eligible tokens": group.eligible_token_count,
                            "Coverage": group.token_coverage,
                            "Text": group.source_text,
                        }
                        for group in rated_lines
                    ]
                )
                st.line_chart(
                    line_frame.set_index("Line")[
                        ["Mean normative concreteness"]
                    ],
                    height=280,
                )
                st.dataframe(
                    line_frame.style.format(
                        {
                            "Mean normative concreteness": lambda value: _decimal(
                                value
                            ),
                            "Median": lambda value: _decimal(value),
                            "Coverage": lambda value: _percentage(value),
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("No physical line contains a rated eligible token.")

            st.subheader("Stanza Profile")
            stanza_frame = pd.DataFrame(
                [
                    {
                        "Stanza": group.ordinal,
                        "Mean": group.statistics.mean,
                        "Median": group.statistics.median,
                        "Population SD": (
                            group.statistics.population_standard_deviation
                        ),
                        "Rated tokens": group.rated_token_count,
                        "Eligible tokens": group.eligible_token_count,
                        "Coverage": group.token_coverage,
                    }
                    for group in concreteness.stanza_summaries
                ]
            )
            if not stanza_frame.empty:
                st.dataframe(
                    stanza_frame.style.format(
                        {
                            "Mean": lambda value: _decimal(value),
                            "Median": lambda value: _decimal(value),
                            "Population SD": lambda value: _decimal(value),
                            "Coverage": lambda value: _percentage(value),
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.info("No stanza units were available.")

            st.subheader("Concreteness by Model Part of Speech")
            pos_frame = pd.DataFrame(
                [
                    {
                        "Universal POS tag": group.label,
                        "Mean": group.statistics.mean,
                        "Median": group.statistics.median,
                        "Rated tokens": group.rated_token_count,
                        "Eligible tokens": group.eligible_token_count,
                        "Coverage": group.token_coverage,
                    }
                    for group in concreteness.part_of_speech_summaries
                ]
            )
            if not pos_frame.empty:
                st.dataframe(
                    pos_frame.style.format(
                        {
                            "Mean": lambda value: _decimal(value),
                            "Median": lambda value: _decimal(value),
                            "Coverage": lambda value: _percentage(value),
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
                st.caption(
                    "Part-of-speech tags come from the installed English model "
                    "and may be uncertain for poetic syntax, fragments, names, "
                    "archaic language, and deliberate ambiguity."
                )

            st.subheader("Matched Term Extremes")
            concrete_column, abstract_column = st.columns(2)
            with concrete_column:
                st.markdown("**Highest source ratings**")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Term": term.source_term,
                                "Rating": term.rating,
                                "Rated token occurrences": (
                                    term.rated_token_occurrences
                                ),
                            }
                            for term in concreteness.most_concrete_terms
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
            with abstract_column:
                st.markdown("**Lowest source ratings**")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Term": term.source_term,
                                "Rating": term.rating,
                                "Rated token occurrences": (
                                    term.rated_token_occurrences
                                ),
                            }
                            for term in concreteness.most_abstract_terms
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
            st.caption(
                "These are rankings among matched source entries, not claims "
                "about contextual meaning or the poem as a whole."
            )

            with st.expander(
                f"Concreteness token audit ({len(concreteness.token_audit):,} rows)"
            ):
                audit_frame = _frame(
                    concreteness.token_audit,
                    {
                        "surface_form": "Surface",
                        "normalized_form": "Normalized surface",
                        "lemma": "Model lemma",
                        "part_of_speech": "POS",
                        "line_number": "Line",
                        "stanza_number": "Stanza",
                        "eligible": "Eligible",
                        "included": "Rated",
                        "match_method": "Method",
                        "matched_source_term": "Source entry",
                        "rating": "Rating",
                        "source_rating_standard_deviation": "Source rating SD",
                        "source_percent_known": "Source percent known",
                        "match_group_id": "Match group",
                        "reason": "Why",
                    },
                )
                st.dataframe(
                    audit_frame[
                        [
                            "Surface",
                            "Normalized surface",
                            "Model lemma",
                            "POS",
                            "Line",
                            "Stanza",
                            "Eligible",
                            "Rated",
                            "Method",
                            "Source entry",
                            "Rating",
                            "Source rating SD",
                            "Source percent known",
                            "Match group",
                            "Why",
                        ]
                    ],
                    hide_index=True,
                    width="stretch",
                    height=420,
                )
            with st.expander("Concreteness resource and calculation provenance"):
                provenance = concreteness.module_result.provenance
                resource = provenance.resources[0]
                st.write(
                    f"**Resource:** {resource.display_name}  \n"
                    f"**Version:** {resource.version}  \n"
                    f"**SHA-256:** `{resource.source_sha256}`  \n"
                    f"**Adapter:** {resource.adapter_version}  \n"
                    f"**Module:** {concreteness.module_result.module_name} "
                    f"{concreteness.module_result.module_version}  \n"
                    f"**Configuration:** "
                    f"`{provenance.configuration_id}`  \n"
                    f"**Lookup policy:** {provenance.lookup_policy}  \n"
                    f"**Inclusion policy:** {provenance.inclusion_policy}"
                )
                st.write(f"**Citation:** {resource.citation}")
                st.caption(resource.license_notice)

    with frequency_tab:
        frequency = workspace.frequency
        if frequency is None:
            st.subheader("SUBTLEX-US Lexical Frequency & Rarity")
            st.info(
                "Frequency & rarity was not selected for this result. Enable "
                "the optional SUBTLEX-US Zipf module above and analyze again."
            )
            if not frequency_status.available:
                st.warning(frequency_status.message)
        else:
            summary = frequency.summary
            statistics = summary.statistics
            st.subheader("SUBTLEX-US Lexical Frequency & Rarity")
            st.markdown(
                '<div class="verse-callout"><strong>Primary reading:</strong> '
                "Median Zipf describes the central corpus-relative frequency "
                "among matched eligible token occurrences. The scale is "
                "logarithmic: one Zipf point is roughly a tenfold frequency "
                "difference. It does not measure difficulty, sophistication, "
                "accessibility, or literary quality.</div>",
                unsafe_allow_html=True,
            )
            metric_columns = st.columns(5)
            metric_columns[0].metric(
                "Median Zipf (primary)", _decimal(statistics.median)
            )
            metric_columns[1].metric("Mean Zipf", _decimal(statistics.mean))
            metric_columns[2].metric(
                "Interquartile range", _decimal(summary.interquartile_range)
            )
            metric_columns[3].metric(
                "Matched-token coverage", _percentage(summary.token_coverage)
            )
            metric_columns[4].metric(
                "Unique-word coverage",
                _percentage(summary.unique_type_coverage),
            )
            st.caption(
                f"Active scope: **{summary.scope_label}**. "
                f"{summary.matched_token_count:,} of "
                f"{summary.eligible_token_count:,} eligible token occurrences "
                "matched. Unmatched words remain missing rather than Zipf zero."
            )

            st.markdown("**Configured Zipf distribution**")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Band": band.label,
                            "Lower bound": band.lower_bound,
                            "Upper bound": band.upper_bound,
                            "Matched tokens": band.token_count,
                            "Proportion": band.proportion,
                        }
                        for band in summary.bands
                    ]
                ).style.format(
                    {
                        "Lower bound": lambda value: (
                            "" if pd.isna(value) else f"{value:.2f}"
                        ),
                        "Upper bound": lambda value: (
                            "" if pd.isna(value) else f"{value:.2f}"
                        ),
                        "Proportion": lambda value: _percentage(value),
                    }
                ),
                hide_index=True,
                width="stretch",
            )
            st.caption(
                "Default orientation: rare <3, uncommon 3-<4, moderately "
                "common 4-<5, common 5-<6, and very common >=6. These "
                "configurable labels are not universal linguistic categories."
            )

            if frequency.module_result.warnings:
                with st.expander(
                    "Frequency warnings and methodology notes "
                    f"({len(frequency.module_result.warnings)})"
                ):
                    for warning in frequency.module_result.warnings:
                        if warning.severity.value == "information":
                            st.info(warning.message)
                        else:
                            st.warning(warning.message)

            st.markdown("**Physical-line summaries**")
            line_rows = [
                {
                    "Line": group.ordinal,
                    "Text": group.source_text,
                    "Eligible tokens": group.eligible_token_count,
                    "Matched tokens": group.matched_token_count,
                    "Coverage": group.token_coverage,
                    "Median Zipf": group.statistics.median,
                    "Mean Zipf": group.statistics.mean,
                }
                for group in frequency.line_summaries
            ]
            st.dataframe(
                pd.DataFrame(
                    line_rows,
                    columns=[
                        "Line",
                        "Text",
                        "Eligible tokens",
                        "Matched tokens",
                        "Coverage",
                        "Median Zipf",
                        "Mean Zipf",
                    ],
                ).style.format(
                    {
                        "Coverage": lambda value: _percentage(value),
                        "Median Zipf": lambda value: _decimal(value),
                        "Mean Zipf": lambda value: _decimal(value),
                    }
                ),
                hide_index=True,
                width="stretch",
            )
            with st.expander("Stanza and part-of-speech summaries"):
                stanza_rows = [
                    {
                        "Stanza": group.ordinal,
                        "Text": group.source_text,
                        "Eligible tokens": group.eligible_token_count,
                        "Matched tokens": group.matched_token_count,
                        "Coverage": group.token_coverage,
                        "Median Zipf": group.statistics.median,
                        "Mean Zipf": group.statistics.mean,
                    }
                    for group in frequency.stanza_summaries
                ]
                st.markdown("**Stanzas**")
                st.dataframe(
                    pd.DataFrame(
                        stanza_rows,
                        columns=[
                            "Stanza",
                            "Text",
                            "Eligible tokens",
                            "Matched tokens",
                            "Coverage",
                            "Median Zipf",
                            "Mean Zipf",
                        ],
                    ).style.format(
                        {
                            "Coverage": lambda value: _percentage(value),
                            "Median Zipf": lambda value: _decimal(value),
                            "Mean Zipf": lambda value: _decimal(value),
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
                pos_rows = [
                    {
                        "POS": group.label,
                        "Eligible tokens": group.eligible_token_count,
                        "Matched tokens": group.matched_token_count,
                        "Coverage": group.token_coverage,
                        "Median Zipf": group.statistics.median,
                        "Mean Zipf": group.statistics.mean,
                    }
                    for group in frequency.part_of_speech_summaries
                ]
                st.markdown("**Part of speech**")
                st.dataframe(
                    pd.DataFrame(
                        pos_rows,
                        columns=[
                            "POS",
                            "Eligible tokens",
                            "Matched tokens",
                            "Coverage",
                            "Median Zipf",
                            "Mean Zipf",
                        ],
                    ).style.format(
                        {
                            "Coverage": lambda value: _percentage(value),
                            "Median Zipf": lambda value: _decimal(value),
                            "Mean Zipf": lambda value: _decimal(value),
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )
                st.caption(
                    "POS labels are model-generated. When Content words only "
                    "is active, only NOUN, VERB, ADJ, and ADV are eligible."
                )

            low_column, high_column = st.columns(2)
            with low_column:
                st.markdown("**Lowest-frequency represented terms**")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Term": term.source_term,
                                "Zipf": term.zipf_value,
                                "Token occurrences": (
                                    term.matched_token_occurrences
                                ),
                                "Frequency per million": (
                                    term.frequency_per_million
                                ),
                            }
                            for term in frequency.lowest_frequency_terms
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
            with high_column:
                st.markdown("**Highest-frequency represented terms**")
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Term": term.source_term,
                                "Zipf": term.zipf_value,
                                "Token occurrences": (
                                    term.matched_token_occurrences
                                ),
                                "Frequency per million": (
                                    term.frequency_per_million
                                ),
                            }
                            for term in frequency.highest_frequency_terms
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )
            with st.expander(
                f"Rare-word tail ({len(frequency.rare_word_tail):,} represented terms)"
            ):
                st.dataframe(
                    pd.DataFrame(
                        [
                            {
                                "Term": term.source_term,
                                "Zipf": term.zipf_value,
                                "Token occurrences": (
                                    term.matched_token_occurrences
                                ),
                                "Model POS in poem": " | ".join(
                                    term.part_of_speech_tags
                                ),
                            }
                            for term in frequency.rare_word_tail
                        ]
                    ),
                    hide_index=True,
                    width="stretch",
                )

            with st.expander(
                f"Frequency token audit ({len(frequency.token_audit):,} rows)"
            ):
                audit_frame = _frame(
                    frequency.token_audit,
                    {
                        "surface_form": "Surface",
                        "normalized_form": "Normalized surface",
                        "lemma": "Model lemma",
                        "part_of_speech": "POS",
                        "line_number": "Line",
                        "stanza_number": "Stanza",
                        "eligible": "Eligible",
                        "included": "Matched",
                        "match_method": "Method",
                        "matched_source_term": "Source entry",
                        "zipf_value": "Zipf",
                        "frequency_count": "Corpus count",
                        "contextual_diversity_count": "Film count",
                        "reason": "Why",
                    },
                )
                st.dataframe(
                    audit_frame[
                        [
                            "Surface",
                            "Normalized surface",
                            "Model lemma",
                            "POS",
                            "Line",
                            "Stanza",
                            "Eligible",
                            "Matched",
                            "Method",
                            "Source entry",
                            "Zipf",
                            "Corpus count",
                            "Film count",
                            "Why",
                        ]
                    ],
                    hide_index=True,
                    width="stretch",
                    height=420,
                )
            with st.expander("Frequency resource and calculation provenance"):
                provenance = frequency.module_result.provenance
                resource = provenance.resources[0]
                st.write(
                    f"**Resource:** {resource.display_name}  \n"
                    f"**Version:** {resource.version}  \n"
                    f"**SHA-256:** `{resource.source_sha256}`  \n"
                    f"**Adapter:** {resource.adapter_version}  \n"
                    f"**Module:** {frequency.module_result.module_name} "
                    f"{frequency.module_result.module_version}  \n"
                    f"**Configuration:** `{provenance.configuration_id}`  \n"
                    f"**Lookup policy:** {provenance.lookup_policy}  \n"
                    f"**Inclusion policy:** {provenance.inclusion_policy}"
                )
                st.write(f"**Citation:** {resource.citation}")
                st.caption(resource.license_notice)

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
        status_options = sorted({row.status for row in all_matches})
        status_filter = st.multiselect(
            "Match status",
            options=status_options,
            default=["included"] if "included" in status_options else [],
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
        elif workspace.results:
            st.success("Every lexical token matched each selected lexicon under this policy.")
        else:
            st.info(
                "No affective lexicon was selected. Optional-module matching is "
                "available in the Concreteness Profile or Frequency & Rarity "
                "token audits and downloads."
            )

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
            "reproducibility-manifest, shared poem document, and complete JSON "
            "result files. When concreteness is selected, it also includes its "
            "summary, structural, POS, term, token-audit, and JSON files. When "
            "frequency is selected, it includes its summary, distribution, "
            "structural, POS, term, token-audit, and JSON files."
        )

    with help_tab:
        st.subheader("A Practical Reading Order")
        st.markdown(
            """
            1. **Coverage:** Is enough vocabulary represented to make the aggregate useful?
            2. **Concreteness:** Read the source 1-5 distribution with both coverage denominators and configured bands.
            3. **Normalized VAD:** Compare source-specific 0–1 means, keeping coverage beside them.
            4. **Emotion associations:** Read category rates as overlapping lexical associations.
            5. **Emotion intensity:** Keep prevalence separate from mean intensity among matches.
            6. **Evidence:** Inspect the terms, lemmas, phrases, and suppressions producing a pattern.
            7. **Manifest:** Use this only when you need provenance or reproducibility details.
            """
        )
        st.info(
            "When Frequency & Rarity is selected, read median SUBTLEX-US Zipf "
            "after coverage and concreteness, then inspect configured bands and "
            "the rare-word audit before moving to VAD."
        )
        st.subheader("What the Main Terms Mean")
        definitions = [
            ("Coverage", "The share of eligible lexical tokens that found a source entry."),
            ("Token-weighted", "Every matched occurrence contributes, including repetitions."),
            ("Type-weighted", "Each distinct matched lexicon entry contributes once."),
            ("Work-weighted corpus", "Each eligible work contributes one work-level mean regardless of length."),
            ("Cumulative lexical load", "A length-sensitive sum of matched normative ratings or midpoint deviations."),
            ("Normalized VAD", "A derived 0-1 version used for legitimate side-by-side VAD comparison."),
            ("Normative lexical concreteness", "A matched source rating from 1 (very abstract or language-based) to 5 (very concrete or experience-based)."),
            ("Rated-token coverage", "The share of eligible lexical token occurrences assigned a source rating; missing tokens stay missing."),
            ("Rated unique-word coverage", "The share of unique normalized observed surface forms assigned a source rating."),
            ("SUBTLEX-US Zipf frequency", "A logarithmic, corpus-relative word-form frequency value; one point is roughly a tenfold frequency difference."),
            ("Matched frequency coverage", "The share of eligible token occurrences or observed surface types that found a SUBTLEX-US entry; unmatched values stay missing."),
            ("Content words only", "An optional frequency scope limited to model-tagged NOUN, VERB, ADJ, and ADV; it is off by default."),
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
