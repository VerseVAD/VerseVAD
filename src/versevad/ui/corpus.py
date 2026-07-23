"""Streamlit project and corpus workspace backed by local SQLite storage."""

from __future__ import annotations

import importlib
import json
from dataclasses import asdict

import pandas as pd
import streamlit as st

import versevad.exports.corpus_excel as corpus_excel_exports
from versevad.application import LEXICON_SPECS, TextImportError
from versevad.corpus import analyze_corpus, corpus_vad_profiles, decode_corpus_files
from versevad.db import ProjectRepository, default_database_path
from versevad.models import PhrasePolicy
from versevad.preprocessing import TextPreprocessor
from versevad.ui.stopwords import render_stopword_settings


def _safe_filename(value: str) -> str:
    stem = "".join(
        character if character.isalnum() or character in {"-", "_"} else "_"
        for character in value.strip()
    ).strip("_")
    return stem or "versevad_corpus"


def _records_frame(records) -> pd.DataFrame:
    return pd.DataFrame([asdict(record) for record in records])


def _create_project(repository: ProjectRepository, *, expanded: bool) -> None:
    with st.expander("Create a research project", expanded=expanded):
        with st.form("create_corpus_project", clear_on_submit=True):
            title = st.text_input("Project title", key="new_project_title")
            researcher = st.text_input("Researcher (optional)", key="new_project_researcher")
            description = st.text_area(
                "Project description (optional)",
                key="new_project_description",
                height=90,
            )
            create = st.form_submit_button("Create project", type="primary")
        if create:
            try:
                repository.create_project(
                    title,
                    researcher=researcher,
                    description=description,
                )
                st.success("Project created in the local VerseVAD database.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))


def _render_texts_tab(repository: ProjectRepository, project_id: str) -> None:
    st.subheader("Import a folder of works")
    st.write(
        "Choose a folder containing UTF-8 `.txt` files. Each file becomes one work; "
        "subfolder paths are retained. Re-importing a changed file creates a new "
        "preserved text version rather than overwriting the old one."
    )
    uploads = st.file_uploader(
        "Corpus folder",
        type=["txt"],
        accept_multiple_files="directory",
        help="The browser passes these files only to the VerseVAD process on this computer.",
        key=f"corpus_folder_{project_id}",
    )
    if st.button(
        "Import selected folder",
        type="primary",
        disabled=not uploads,
        key=f"import_corpus_{project_id}",
    ):
        try:
            decoded = decode_corpus_files(
                (upload.name, upload.getvalue()) for upload in uploads
            )
            records = repository.import_texts(project_id, decoded.files)
            st.success(
                f"Imported {len(decoded.files):,} files. This project now contains "
                f"{len(records):,} active works."
            )
            st.rerun()
        except (TextImportError, ValueError) as error:
            st.error(str(error))

    texts = repository.list_texts(project_id)
    if not texts:
        st.info("No works have been imported into this project yet.")
        return
    st.subheader(f"Works in this project ({len(texts):,})")
    summary = pd.DataFrame(
        [
            {
                "Title": text.title,
                "Author": text.author,
                "Collection": text.collection,
                "Date": text.date_label,
                "Genre": text.genre,
                "Source path": text.relative_path,
                "Version": text.text_version_id,
            }
            for text in texts
        ]
    )
    st.dataframe(summary, hide_index=True, width="stretch", height=300)

    st.subheader("Edit one work's metadata")
    selected_id = st.selectbox(
        "Work",
        options=[text.text_id for text in texts],
        format_func=lambda text_id: next(text.title for text in texts if text.text_id == text_id),
        key=f"metadata_text_{project_id}",
    )
    selected = next(text for text in texts if text.text_id == selected_id)
    with st.form(f"metadata_form_{selected.text_id}"):
        left, right = st.columns(2)
        title = left.text_input("Title", value=selected.title)
        author = right.text_input("Author", value=selected.author)
        collection = left.text_input("Collection or volume", value=selected.collection)
        date_label = right.text_input("Date or date range", value=selected.date_label)
        genre = left.text_input("Genre or work type", value=selected.genre)
        notes = st.text_area("Research notes", value=selected.notes, height=90)
        custom_json = st.text_area(
            "Custom metadata (JSON object)",
            value=json.dumps(dict(selected.custom_metadata), ensure_ascii=False, indent=2),
            height=100,
            help='For extensible fields such as {"sequence": 3, "section": "Part I"}.',
        )
        save = st.form_submit_button("Save metadata")
    if save:
        try:
            custom = json.loads(custom_json or "{}")
            if not isinstance(custom, dict):
                raise ValueError("Custom metadata must be a JSON object enclosed in braces.")
            repository.update_text_metadata(
                selected.text_id,
                title=title,
                author=author,
                collection=collection,
                date_label=date_label,
                genre=genre,
                notes=notes,
                custom_metadata=custom,
            )
            st.success("Metadata saved locally.")
            st.rerun()
        except (ValueError, json.JSONDecodeError) as error:
            st.error(f"Metadata was not changed: {error}")


def _render_profiles(metrics, total_works: int) -> None:
    profiles = corpus_vad_profiles(metrics, total_works=total_works)
    if not profiles:
        st.info("The latest complete corpus batch has no normalized VAD means to compare.")
        return
    st.subheader("Collection VAD: report both views")
    st.write(
        "The **token-weighted volume profile** pools included matched observations, so "
        "long works contribute more. The **work-weighted volume profile** gives every "
        "eligible work one poem-level score. Their divergence can be an important finding."
    )
    profile_frame = pd.DataFrame(
        [
            {
                "Lexicon": row.lexicon,
                "Analysis view": (
                    "All matched tokens"
                    if row.analysis_view == "all_matched"
                    else "Stopwords excluded"
                ),
                "Dimension": row.dimension.title(),
                "Works included": row.works_included,
                "Works omitted": row.works_omitted,
                "Matched observations": row.matched_observations,
                "Volume coverage": row.volume_coverage,
                "Token-weighted volume mean": row.token_weighted_volume_mean,
                "Work-weighted volume mean": row.work_weighted_volume_mean,
                "Work minus token": row.work_minus_token_difference,
            }
            for row in profiles
        ]
    )
    st.dataframe(
        profile_frame.style.format(
            {
                "Volume coverage": "{:.1%}",
                "Token-weighted volume mean": "{:.3f}",
                "Work-weighted volume mean": "{:.3f}",
                "Work minus token": "{:+.3f}",
            }
        ),
        hide_index=True,
        width="stretch",
    )
    chart = profile_frame.melt(
        id_vars=["Lexicon", "Analysis view", "Dimension"],
        value_vars=["Token-weighted volume mean", "Work-weighted volume mean"],
        var_name="Collection view",
        value_name="Normalized mean",
    )
    st.bar_chart(
        chart,
        x="Dimension",
        y="Normalized mean",
        color="Collection view",
        stack=False,
        height=320,
    )
    st.caption(
        "Only eligible work scores enter either mean. Works with missing scores are reported as omitted, not assigned a neutral value."
    )


def _render_analysis_tab(
    repository: ProjectRepository,
    project_id: str,
    preprocessor: TextPreprocessor,
) -> None:
    texts = repository.list_texts(project_id)
    if not texts:
        st.info("Import a folder of `.txt` works before running corpus analysis.")
        return
    st.subheader("Run a complete corpus batch")
    st.write(
        "VerseVAD analyzes one work at a time, preserving separate work-level results. "
        "The comparison dashboard updates only after every selected work finishes."
    )
    text_ids = st.multiselect(
        "Works to analyze",
        options=[text.text_id for text in texts],
        default=[text.text_id for text in texts],
        format_func=lambda text_id: next(text.title for text in texts if text.text_id == text_id),
        key=f"analysis_texts_{project_id}",
    )
    lexicon_lookup = {spec.lexicon_id: spec for spec in LEXICON_SPECS}
    lexicon_ids = st.multiselect(
        "Lexicons",
        options=list(lexicon_lookup),
        default=list(lexicon_lookup),
        format_func=lambda lexicon_id: lexicon_lookup[lexicon_id].display_name,
        key=f"analysis_lexicons_{project_id}",
    )
    with st.expander("Advanced batch methodology"):
        policies = {
            "Prefer the longest phrase (recommended)": PhrasePolicy.PHRASE_PREFERRED,
            "Use unigrams only": PhrasePolicy.UNIGRAM_ONLY,
            "Count phrases and components (exploratory)": PhrasePolicy.PHRASE_AND_COMPONENT,
        }
        policy_label = st.selectbox(
            "Phrase policy",
            options=list(policies),
            key=f"corpus_policy_{project_id}",
        )
        minimum = st.number_input(
            "Minimum matched observations before a VAD result is marked non-sparse",
            min_value=1,
            max_value=100,
            value=3,
            key=f"corpus_minimum_{project_id}",
        )
    with st.expander("Stopword settings"):
        st.info(
            "Stopword exclusion changes only the secondary VAD view. Matching, "
            "the complete analysis, and the token audit remain intact."
        )
        stopword_settings = render_stopword_settings(f"corpus_{project_id}")
    run = st.button(
        "Analyze selected works",
        type="primary",
        disabled=not text_ids or not lexicon_ids,
        key=f"analyze_corpus_{project_id}",
    )
    if run:
        progress_bar = st.progress(0.0, text="Preparing corpus batch…")

        def update_progress(completed: int, total: int, title: str) -> None:
            progress_bar.progress(
                completed / total if total else 0.0,
                text=f"{completed:,}/{total:,} complete — {title}",
            )

        try:
            batch = analyze_corpus(
                repository,
                project_id,
                lexicon_ids=tuple(lexicon_ids),
                text_ids=tuple(text_ids),
                phrase_policy=policies[policy_label],
                minimum_match_requirement=int(minimum),
                stopword_mode=stopword_settings.mode,
                protected_stopwords=stopword_settings.protected_words,
                custom_stopword_additions=stopword_settings.custom_additions,
                custom_stopword_removals=stopword_settings.custom_removals,
                preprocessor=preprocessor,
                progress=update_progress,
            )
            progress_bar.progress(1.0, text="Corpus analysis complete")
            st.success(
                f"Completed batch {batch.batch_id}. Comparisons now use this internally consistent run."
            )
            st.rerun()
        except Exception as error:
            st.error(
                "The corpus batch did not complete, so it was not published to the comparison dashboard. "
                f"Technical detail: {error}"
            )

    metrics = repository.list_latest_metrics(project_id)
    if not metrics:
        st.info("No complete corpus batch is available yet.")
        return
    st.divider()
    st.subheader("Filter the completed comparison batch")
    collections = sorted({row.collection or "(unassigned)" for row in metrics})
    authors = sorted({row.author or "(unassigned)" for row in metrics})
    genres = sorted({row.genre or "(unassigned)" for row in metrics})
    filter_columns = st.columns(3)
    selected_collections = filter_columns[0].multiselect(
        "Collections",
        options=collections,
        default=collections,
        key=f"filter_collections_{project_id}",
    )
    selected_authors = filter_columns[1].multiselect(
        "Authors",
        options=authors,
        default=authors,
        key=f"filter_authors_{project_id}",
    )
    selected_genres = filter_columns[2].multiselect(
        "Genres",
        options=genres,
        default=genres,
        key=f"filter_genres_{project_id}",
    )
    metrics = tuple(
        row
        for row in metrics
        if (row.collection or "(unassigned)") in selected_collections
        and (row.author or "(unassigned)") in selected_authors
        and (row.genre or "(unassigned)") in selected_genres
    )
    if not metrics:
        st.info("No completed work matches these metadata filters.")
        return
    view_labels = {
        "all_matched": "All matched tokens",
        "stopwords_excluded": "Stopwords excluded",
    }
    available_views = [
        view
        for view in ("all_matched", "stopwords_excluded")
        if any(row.analysis_view == view for row in metrics)
    ]
    selected_views = st.multiselect(
        "Affective result views",
        options=available_views,
        default=available_views,
        format_func=lambda value: view_labels[value],
        key=f"comparison_analysis_views_{project_id}",
        help="Keep both selected to compare full and stopword-excluded results together.",
    )
    metrics = tuple(row for row in metrics if row.analysis_view in selected_views)
    if not metrics:
        st.info("Select at least one affective result view.")
        return
    _render_profiles(metrics, len({row.text_id for row in metrics}))

    st.subheader("Compare individual works")
    vad = [
        row
        for row in metrics
        if row.metric == "vad_mean" and row.scale == "normalized_0_1"
    ]
    if vad:
        selected_lexicon = st.selectbox(
            "Comparison lexicon",
            options=sorted({row.lexicon for row in vad}),
            key=f"comparison_lexicon_{project_id}",
        )
        selected_weighting = st.radio(
            "Within-work weighting",
            options=["token", "type"],
            format_func=lambda value: (
                "Token-weighted — repetitions count"
                if value == "token"
                else "Type-weighted — each matched entry counts once"
            ),
            horizontal=True,
            key=f"comparison_weighting_{project_id}",
        )
        chosen = [
            row
            for row in vad
            if row.lexicon == selected_lexicon and row.weighting == selected_weighting
        ]
        work_frame = pd.DataFrame(
            [
                {
                    "Work": row.title,
                    "Collection": row.collection,
                    "Analysis view": view_labels[row.analysis_view],
                    "Dimension": row.dimension.title(),
                    "Mean": row.value,
                    "Observations": row.observations,
                    "Coverage": row.coverage,
                }
                for row in chosen
            ]
        )
        st.dataframe(
            work_frame.style.format({"Mean": "{:.3f}", "Coverage": "{:.1%}"}),
            hide_index=True,
            width="stretch",
        )
        if {"all_matched", "stopwords_excluded"}.issubset(
            {row.analysis_view for row in chosen}
        ):
            sensitivity = (
                work_frame.pivot_table(
                    index=["Work", "Collection", "Dimension"],
                    columns="Analysis view",
                    values="Mean",
                    aggfunc="first",
                )
                .reset_index()
            )
            if {
                "All matched tokens",
                "Stopwords excluded",
            }.issubset(sensitivity.columns):
                sensitivity["Difference"] = (
                    sensitivity["Stopwords excluded"]
                    - sensitivity["All matched tokens"]
                )
                st.markdown("**Stopword sensitivity by work**")
                st.dataframe(
                    sensitivity.style.format(
                        {
                            "All matched tokens": "{:.3f}",
                            "Stopwords excluded": "{:.3f}",
                            "Difference": "{:+.3f}",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                )

    st.subheader("Length-sensitive cumulative load by work")
    st.write(
        "These sums answer a different question from means. They grow with included "
        "matched vocabulary and repetition; they are not estimates of a reader's psychological response."
    )
    cumulative_metric_names = {
        "vad_rating_total",
        "vad_above_midpoint_load",
        "vad_below_midpoint_load",
        "vad_net_midpoint_load",
        "vad_absolute_midpoint_load",
    }
    load_rows = [row for row in metrics if row.metric in cumulative_metric_names]
    if load_rows:
        load_frame = pd.DataFrame(
            [
                {
                    "Work": row.title,
                    "Collection": row.collection,
                    "Lexicon": row.lexicon,
                    "Analysis view": view_labels[row.analysis_view],
                    "Dimension": row.dimension.title(),
                    "Measure": row.metric.replace("vad_", "").replace("_", " ").title(),
                    "Value": row.value,
                    "Matched observations": row.observations,
                    "Coverage": row.coverage,
                }
                for row in load_rows
            ]
        )
        st.dataframe(
            load_frame.style.format({"Value": "{:.3f}", "Coverage": "{:.1%}"}),
            hide_index=True,
            width="stretch",
            height=380,
        )


def _render_project_settings_tab(
    repository: ProjectRepository,
    project_id: str,
) -> None:
    project = repository.get_project(project_id)
    st.subheader("Project settings")
    st.warning(
        "Deleting this project permanently removes only this project's imported "
        "texts, preserved versions, completed analyses, corpus batches, and "
        "quality-control notes from the local VerseVAD database. Other projects "
        "are not affected."
    )
    confirmation = st.text_input(
        f'Type the exact project title to confirm: "{project.title}"',
        key=f"delete_project_confirmation_{project_id}",
    )
    if st.button(
        "Delete this project",
        type="primary",
        disabled=confirmation != project.title,
        key=f"delete_project_{project_id}",
    ):
        try:
            repository.delete_project(
                project_id,
                confirmation_title=confirmation,
            )
            st.session_state.pop("active_corpus_project", None)
            st.session_state["corpus_project_flash"] = (
                f'Project "{project.title}" was deleted from this computer.'
            )
            st.rerun()
        except (KeyError, ValueError, RuntimeError) as error:
            st.error(f"The project was not deleted: {error}")


def _render_qc_tab(repository: ProjectRepository, project_id: str) -> None:
    rows = repository.list_latest_unmatched(project_id)
    st.subheader("Unmatched-vocabulary quality control")
    st.write(
        "These observations did not match a selected lexicon in the latest complete "
        "batch. Notes persist locally by project, work, lexicon, and normalized form. "
        "They document review; they do not alter an analysis score."
    )
    if not rows:
        st.info("No unmatched observations are available from a complete corpus batch.")
        return
    statuses = ["All", "unreviewed", "reviewed", "needs mapping", "accepted gap"]
    status_filter = st.selectbox(
        "Review status",
        options=statuses,
        key=f"qc_status_{project_id}",
    )
    search = st.text_input(
        "Search word, work, lexicon, lemma, or note",
        key=f"qc_search_{project_id}",
    ).casefold()
    filtered = [
        row
        for row in rows
        if (status_filter == "All" or row.status == status_filter)
        and (
            not search
            or search
            in " ".join(
                (
                    row.display_form,
                    row.normalized_form,
                    row.text_title,
                    row.lexicon,
                    row.proposed_lemma,
                    row.note,
                )
            ).casefold()
        )
    ]
    frame = pd.DataFrame(
        [
            {
                "Work": row.text_title,
                "Lexicon": row.lexicon,
                "Surface": row.display_form,
                "Normalized": row.normalized_form,
                "Frequency": row.frequency,
                "POS": row.pos,
                "Proposed lemma": row.proposed_lemma,
                "Status": row.status,
                "Research note": row.note,
                "Example": row.example_context,
            }
            for row in filtered
        ]
    )
    st.dataframe(frame, hide_index=True, width="stretch", height=340)
    if not filtered:
        return
    selected_index = st.selectbox(
        "Item to review",
        options=range(len(filtered)),
        format_func=lambda index: (
            f"{filtered[index].display_form} — {filtered[index].text_title} — "
            f"{filtered[index].lexicon}"
        ),
        key=f"qc_item_{project_id}",
    )
    selected = filtered[selected_index]
    with st.form(f"qc_note_{selected.text_id}_{selected.lexicon_id}_{selected.normalized_form}"):
        status = st.selectbox(
            "Status",
            options=["unreviewed", "reviewed", "needs mapping", "accepted gap"],
            index=["unreviewed", "reviewed", "needs mapping", "accepted gap"].index(
                selected.status
            ),
        )
        note = st.text_area("Research note", value=selected.note, height=100)
        mapping = st.text_input(
            "Possible mapping (documentation only)",
            value=selected.proposed_mapping,
        )
        save = st.form_submit_button("Save quality-control note")
    if save:
        repository.upsert_unmatched_note(
            project_id=project_id,
            text_id=selected.text_id,
            lexicon_id=selected.lexicon_id,
            normalized_form=selected.normalized_form,
            display_form=selected.display_form,
            status=status,
            note=note,
            proposed_mapping=mapping,
        )
        st.success("Quality-control note saved locally. Analysis results were not changed.")
        st.rerun()


def _render_export_tab(repository: ProjectRepository, project_id: str) -> None:
    project = repository.get_project(project_id)
    texts = repository.list_texts(project_id)
    metrics = repository.list_latest_metrics(project_id)
    unmatched = repository.list_latest_unmatched(project_id)
    st.subheader("Excel research workbook")
    st.write(
        "The workbook begins with a reading guide and includes both collection "
        "weightings, individual-work token/type means, cumulative load, coverage, "
        "emotion metrics, unmatched review notes, and provenance metadata."
    )
    if not metrics:
        st.info("Complete a corpus analysis before exporting a workbook.")
        return
    # A Streamlit process can remain open while VerseVAD is updated. Resolve
    # the exporter through its module and refresh it if that process retained
    # the pre-methodology four-argument API.
    if getattr(corpus_excel_exports, "CORPUS_WORKBOOK_API_VERSION", 0) < 2:
        importlib.reload(corpus_excel_exports)
    workbook = corpus_excel_exports.build_corpus_workbook(
        project,
        texts,
        metrics,
        unmatched,
        methodology=repository.latest_methodology(project_id),
    )
    st.download_button(
        "Download corpus Excel workbook",
        data=workbook,
        file_name=f"{_safe_filename(project.title)}_VerseVAD_corpus.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        key=f"download_corpus_{project_id}",
    )
    st.caption(
        "The workbook does not duplicate the full literary texts; it records text/version IDs, source paths, and SHA-256 hashes."
    )


def render_corpus_workspace(preprocessor: TextPreprocessor) -> None:
    """Render the persistent local-project branch of the Streamlit application."""

    repository = ProjectRepository(default_database_path())
    repository.initialize()
    with st.sidebar:
        st.markdown("### Persistent local projects")
        st.success("Projects, texts, notes, and results stay on this computer.")
        st.caption(f"Database: {repository.database_path}")
        st.markdown("---")
        st.caption(
            "Corpus results describe lexical evidence. They do not determine a work's emotion or a reader's response."
        )

    st.markdown(
        '<p class="verse-kicker">Private corpus research workspace</p>',
        unsafe_allow_html=True,
    )
    st.title("VerseVAD projects & corpus")
    st.write(
        "Import a folder as separate works, add metadata, compare complete analysis "
        "batches, review unmatched vocabulary, and export a readable Excel workbook."
    )
    project_flash = st.session_state.pop("corpus_project_flash", None)
    if project_flash:
        st.success(project_flash)
    projects = repository.list_projects()
    _create_project(repository, expanded=not projects)
    if not projects:
        st.info("Create a project to begin. Nothing has been imported yet.")
        return
    project_id = st.selectbox(
        "Active project",
        options=[project.project_id for project in projects],
        format_func=lambda item: next(
            project.title for project in projects if project.project_id == item
        ),
        key="active_corpus_project",
    )
    project = repository.get_project(project_id)
    st.caption(
        f"{project.description or 'No project description.'} "
        f"Researcher: {project.researcher or 'not recorded'}."
    )
    texts_tab, analysis_tab, qc_tab, export_tab, settings_tab = st.tabs(
        [
            "Works & metadata",
            "Analyze & compare",
            "Unmatched QC",
            "Excel export",
            "Project settings",
        ]
    )
    with texts_tab:
        _render_texts_tab(repository, project_id)
    with analysis_tab:
        _render_analysis_tab(repository, project_id, preprocessor)
    with qc_tab:
        _render_qc_tab(repository, project_id)
    with export_tab:
        _render_export_tab(repository, project_id)
    with settings_tab:
        _render_project_settings_tab(repository, project_id)
