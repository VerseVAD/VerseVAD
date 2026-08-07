"""Personal Corpus presentation backed by VerseVAD's existing corpus services."""

from __future__ import annotations

import hashlib
import re

import pandas as pd
import streamlit as st

from versevad.application import ResourceReadiness, TextImportError
from versevad.corpus import decode_corpus_files
from versevad.db import (
    SCHEMA_VERSION,
    CorpusTextImport,
    ProjectRecord,
    ProjectRepository,
    default_personal_corpus_database_path,
)
from versevad.preprocessing import TextPreprocessor
from versevad.module_capabilities import fixed_profile_notice
from versevad.ui.corpus import (
    _corpus_part_of_speech_rows,
    _project_repository_for_path,
    _render_analysis_tab,
    _render_export_tab,
    _render_part_of_speech_tab,
    _render_review_tab,
    _render_texts_tab,
    _render_versemap_tab,
)
from versevad.ui.dataframes import (
    heterogeneous_display_value,
    rounded_display_data,
)
from versevad.ui.design import (
    collapse_control_html,
    render_dataframe,
    render_stateful_section_navigation,
    render_workspace_header,
)
from versevad.analysis_profiles import LexicalScope, ProfileSelection
from versevad.ui.profile_controls import render_report_profile_controls


PERSONAL_CORPUS_TITLE = "My Personal Corpus"
PERSONAL_CORPUS_DESCRIPTION = (
    "A private, locally stored library of poems and reusable VerseVAD results."
)


def _personal_project(repository: ProjectRepository) -> ProjectRecord:
    """Return the single project record inside the isolated personal database."""

    projects = repository.list_projects()
    if projects:
        return projects[0]
    return repository.create_project(
        PERSONAL_CORPUS_TITLE,
        description=PERSONAL_CORPUS_DESCRIPTION,
    )


def _safe_stem(title: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", title.strip()).strip("-._")
    return stem[:80] or "untitled-poem"


def _bottom_collapse(label: str, control_id: str) -> None:
    st.html(
        collapse_control_html(label, control_id),
        width="stretch",
        unsafe_allow_javascript=True,
    )


def _render_add_poems(
    repository: ProjectRepository,
    project_id: str,
) -> None:
    texts = repository.list_texts(project_id)
    with st.expander("Add One or More Poems", expanded=not texts):
        st.write(
            "Choose one or several UTF-8 `.txt` files. Every file remains a "
            "separate poem with its original text preserved."
        )
        uploads = st.file_uploader(
            "Poem files",
            type=["txt"],
            accept_multiple_files=True,
            key=f"personal_corpus_files_{project_id}",
            help=(
                "Files are read by the local VerseVAD process and are never sent "
                "to an external service."
            ),
        )
        if st.button(
            "Add Selected Poems",
            type="primary",
            disabled=not uploads,
            width="stretch",
            key=f"personal_corpus_import_files_{project_id}",
        ):
            try:
                decoded = decode_corpus_files(
                    (upload.name, upload.getvalue()) for upload in uploads
                )
                records = repository.import_texts(project_id, decoded.files)
                st.session_state["personal_corpus_flash"] = (
                    f"Added {len(decoded.files):,} poem"
                    f"{'' if len(decoded.files) == 1 else 's'}. "
                    f"Your personal corpus now contains {len(records):,} poems."
                )
                st.rerun()
            except (TextImportError, ValueError) as error:
                st.error(str(error))

        st.divider()
        st.markdown("#### Paste One Poem")
        with st.form(
            f"personal_corpus_paste_{project_id}",
            clear_on_submit=True,
        ):
            title = st.text_input("Poem title")
            author = st.text_input("Author (optional)")
            original_text = st.text_area(
                "Poem text",
                height=260,
                placeholder="Paste the poem exactly as it should be analyzed.",
            )
            add_pasted = st.form_submit_button(
                "Add Pasted Poem",
                type="primary",
            )
        if add_pasted:
            try:
                clean_title = title.strip()
                if not clean_title:
                    raise ValueError("Enter a poem title.")
                if not original_text.strip():
                    raise ValueError("Paste nonblank poem text.")
                digest = hashlib.sha256(
                    f"{clean_title}\0{original_text}".encode("utf-8")
                ).hexdigest()[:12]
                relative_path = (
                    f"pasted/{_safe_stem(clean_title)}-{digest}.txt"
                )
                records = repository.import_texts(
                    project_id,
                    (
                        CorpusTextImport(
                            title=clean_title,
                            source_name=f"{_safe_stem(clean_title)}.txt",
                            relative_path=relative_path,
                            original_text=original_text,
                        ),
                    ),
                )
                added = next(
                    record
                    for record in records
                    if record.relative_path == relative_path
                )
                repository.update_text_metadata(
                    added.text_id,
                    title=clean_title,
                    author=author,
                    genre="poem",
                )
                st.session_state["personal_corpus_flash"] = (
                    f'Added "{clean_title}" to the personal corpus.'
                )
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        _bottom_collapse(
            "Add One or More Poems",
            f"personal_add_{project_id}",
        )


def _render_edit_poem(
    repository: ProjectRepository,
    project_id: str,
) -> None:
    texts = repository.list_texts(project_id)
    with st.expander("Edit a Poem", expanded=False):
        if not texts:
            st.info("Add a poem before editing it.")
            _bottom_collapse("Edit a Poem", f"personal_edit_{project_id}")
            return
        selected_id = st.selectbox(
            "Poem to edit",
            options=[text.text_id for text in texts],
            format_func=lambda text_id: next(
                text.title for text in texts if text.text_id == text_id
            ),
            key=f"personal_edit_poem_{project_id}",
        )
        selected = next(text for text in texts if text.text_id == selected_id)
        st.caption(
            "Saving changed poem text creates a new preserved text version. "
            "Existing completed analysis batches remain immutable; rerun analysis "
            "to publish results for the new version."
        )
        with st.form(f"personal_edit_form_{selected.text_id}"):
            left, right = st.columns(2)
            title = left.text_input("Title", value=selected.title)
            author = right.text_input("Author", value=selected.author)
            collection = left.text_input(
                "Collection or volume",
                value=selected.collection,
            )
            date_label = right.text_input(
                "Date or date range",
                value=selected.date_label,
            )
            genre = left.text_input(
                "Genre or work type",
                value=selected.genre or "poem",
            )
            notes = st.text_area(
                "Research notes",
                value=selected.notes,
                height=90,
            )
            original_text = st.text_area(
                "Poem text",
                value=selected.original_text,
                height=320,
            )
            save = st.form_submit_button(
                "Save Poem Changes",
                type="primary",
            )
        if save:
            try:
                clean_title = title.strip()
                if not clean_title:
                    raise ValueError("A poem title cannot be blank.")
                if not original_text.strip():
                    raise ValueError("Poem text cannot be blank.")
                repository.import_texts(
                    project_id,
                    (
                        CorpusTextImport(
                            title=clean_title,
                            source_name=selected.source_name,
                            relative_path=selected.relative_path,
                            original_text=original_text,
                        ),
                    ),
                )
                repository.update_text_metadata(
                    selected.text_id,
                    title=clean_title,
                    author=author,
                    collection=collection,
                    date_label=date_label,
                    genre=genre,
                    notes=notes,
                    custom_metadata=selected.custom_metadata,
                )
                st.session_state["personal_corpus_flash"] = (
                    f'Saved changes to "{clean_title}".'
                )
                st.rerun()
            except ValueError as error:
                st.error(f"The poem was not changed: {error}")
        _bottom_collapse("Edit a Poem", f"personal_edit_{project_id}")


def _render_delete_poem(
    repository: ProjectRepository,
    project_id: str,
) -> None:
    texts = repository.list_texts(project_id)
    with st.expander("Delete a Poem", expanded=False):
        if not texts:
            st.info("The personal corpus contains no poems.")
            _bottom_collapse("Delete a Poem", f"personal_delete_{project_id}")
            return
        selected_id = st.selectbox(
            "Poem to delete",
            options=[text.text_id for text in texts],
            format_func=lambda text_id: next(
                text.title for text in texts if text.text_id == text_id
            ),
            key=f"personal_delete_poem_{project_id}",
        )
        selected = next(text for text in texts if text.text_id == selected_id)
        st.warning(
            "This permanently removes this poem's preserved versions and locally "
            "stored analysis records from the Personal Corpus database. Other "
            "poems and Project / Corpus projects are not affected."
        )
        confirmation = st.text_input(
            f'Type the exact poem title to confirm: "{selected.title}"',
            key=f"personal_delete_confirmation_{selected.text_id}",
        )
        if st.button(
            "Delete This Poem",
            type="primary",
            disabled=confirmation != selected.title,
            key=f"personal_delete_button_{selected.text_id}",
        ):
            try:
                repository.delete_text(
                    project_id,
                    selected.text_id,
                    confirmation_title=confirmation,
                )
                st.session_state["personal_corpus_flash"] = (
                    f'Deleted "{selected.title}" from the personal corpus.'
                )
                st.rerun()
            except (KeyError, ValueError, RuntimeError) as error:
                st.error(f"The poem was not deleted: {error}")
        _bottom_collapse("Delete a Poem", f"personal_delete_{project_id}")


def _render_library(
    repository: ProjectRepository,
    project_id: str,
) -> None:
    _render_add_poems(repository, project_id)
    with st.expander("Import a Folder and Browse the Library", expanded=False):
        _render_texts_tab(repository, project_id)
        _bottom_collapse(
            "Import a Folder and Browse the Library",
            f"personal_library_{project_id}",
        )
    _render_edit_poem(repository, project_id)
    _render_delete_poem(repository, project_id)


def _humanize(value: str) -> str:
    return value.replace(".", " · ").replace("_", " ").strip().title()


def _render_poem_detail(
    repository: ProjectRepository,
    project_id: str,
    profile_selection: ProfileSelection,
) -> None:
    texts = repository.list_texts(project_id)
    if not texts:
        st.info("Add and analyze at least one poem to view poem-specific results.")
        return
    selected_id = st.selectbox(
        "Poem",
        options=[text.text_id for text in texts],
        format_func=lambda text_id: next(
            text.title for text in texts if text.text_id == text_id
        ),
        key=f"personal_detail_poem_{project_id}",
    )
    selected = next(text for text in texts if text.text_id == selected_id)
    st.caption(
        f"{selected.author or 'Author not recorded'} · "
        f"Version {selected.text_version_id} · "
        "Only the latest complete compatible corpus batch is shown."
    )

    affective = tuple(
        row
        for row in repository.list_latest_metrics(project_id)
        if row.text_id == selected_id
    )
    module_metrics = tuple(
        row
        for row in repository.list_latest_module_metrics(project_id)
        if row.text_id == selected_id
    )
    coverage = tuple(
        row
        for row in repository.list_latest_module_coverage(project_id)
        if row.text_id == selected_id
    )
    warnings = tuple(
        row
        for row in repository.list_latest_module_warnings(project_id)
        if row.text_id == selected_id
    )
    if not affective and not module_metrics:
        st.info(
            "This poem has no completed results yet. Open Analyze & Compare, "
            "include this poem, choose the desired sources and modules, and run "
            "the corpus analysis."
        )
        return

    with st.expander("Affective Metrics", expanded=False):
        if not affective:
            st.info("The latest batch contains no affective lexicon results.")
        else:
            view_ids = {
                LexicalScope.ALL_LEXICAL: "all_matched",
                LexicalScope.STOPWORD_EXCLUDED: "stopwords_excluded",
                LexicalScope.CONTENT_WORDS: "content_words",
            }
            views = {view_ids[scope] for scope in profile_selection.scopes}
            weightings = {
                item.value.casefold() for item in profile_selection.weightings
            }
            scope_labels = {
                "all_matched": "All lexical tokens",
                "stopwords_excluded": "Stopword-excluded",
                "content_words": "Content words only",
            }
            chosen = tuple(
                row
                for row in affective
                if row.analysis_view in views and row.weighting in weightings
            )
            frame = pd.DataFrame(
                [
                    {
                        "Lexicon": row.lexicon,
                        "Profile": (
                            f"{scope_labels[row.analysis_view]} · "
                            f"{row.weighting.title()}-weighted"
                        ),
                        "Measure": _humanize(row.metric),
                        "Dimension": row.dimension.title() or "—",
                        "Category": row.category.title() or "—",
                        "Value": row.value,
                        "Observations": row.observations,
                        "Coverage": row.coverage,
                    }
                    for row in chosen
                ]
            )
            if frame.empty:
                st.info("No metrics are available for this combination.")
            else:
                render_dataframe(
                    frame.style.format(
                        {"Value": "{:.3f}", "Coverage": "{:.1%}"},
                        na_rep="—",
                    ),
                    hide_index=True,
                    width="stretch",
                    height=380,
                )
                means = frame[
                    frame["Measure"].str.casefold() == "vad mean"
                ].copy()
                if not means.empty:
                    st.bar_chart(
                        rounded_display_data(means),
                        x="Dimension",
                        y="Value",
                        color="Lexicon",
                        stack=False,
                        height=300,
                    )
        _bottom_collapse(
            "Affective Metrics",
            f"personal_detail_affective_{project_id}",
        )

    non_versemap = tuple(
        row for row in module_metrics if row.module_name != "versemap"
    )
    with st.expander("Enabled Optional-Module Metrics", expanded=False):
        if not non_versemap:
            st.info("No optional-module metrics are available for this poem.")
        else:
            modules = sorted({row.module_name for row in non_versemap})
            selected_module = st.selectbox(
                "Module",
                options=modules,
                format_func=_humanize,
                key=f"personal_detail_module_{project_id}",
            )
            frame = pd.DataFrame(
                [
                    {
                        "Metric": _humanize(row.metric_id),
                        "Value": heterogeneous_display_value(row.value),
                        "Layer": _humanize(row.layer),
                        "Scope": _humanize(row.scope),
                        "Weighting": _humanize(row.weighting) or "—",
                        "Observations": row.observation_count,
                        "Note": row.note,
                    }
                    for row in non_versemap
                    if row.module_name == selected_module
                ]
            )
            render_dataframe(
                frame,
                hide_index=True,
                width="stretch",
                height=420,
            )
        _bottom_collapse(
            "Enabled Optional-Module Metrics",
            f"personal_detail_modules_{project_id}",
        )

    versemap_metrics = tuple(
        row for row in module_metrics if row.module_name == "versemap"
    )
    with st.expander("VerseMap Profile", expanded=False):
        st.info(
            "VerseMap always uses the pinned Standard Profile 1.0 for both this "
            "poem and the reference corpus. Token/type and stopword controls do "
            "not alter this comparison."
        )
        if not versemap_metrics:
            st.info("VerseMap was not enabled in this poem's latest analysis.")
        else:
            frame = pd.DataFrame(
                [
                    {
                        "Metric": _humanize(row.metric_id),
                        "Value": heterogeneous_display_value(row.value),
                        "Scope": _humanize(row.scope),
                        "Unit": row.unit,
                        "Observations": row.observation_count,
                        "Note": row.note,
                    }
                    for row in versemap_metrics
                ]
            )
            render_dataframe(
                frame,
                hide_index=True,
                width="stretch",
                height=420,
            )
        _bottom_collapse(
            "VerseMap Profile",
            f"personal_detail_versemap_{project_id}",
        )

    with st.expander("Coverage and Warnings", expanded=False):
        if coverage:
            render_dataframe(
                pd.DataFrame(
                    [
                        {
                            "Module": _humanize(row.module_name),
                            "Measure": _humanize(row.coverage_id),
                            "Eligible": row.eligible_count,
                            "Matched": row.matched_count,
                            "Unmatched": row.unmatched_count,
                            "Coverage": row.coverage_rate,
                            "Note": row.note,
                        }
                        for row in coverage
                    ]
                ).style.format({"Coverage": "{:.1%}"}, na_rep="—"),
                hide_index=True,
                width="stretch",
                height=320,
            )
        else:
            st.info("No optional-module coverage records are available.")
        if warnings:
            st.markdown("#### Warnings")
            render_dataframe(
                pd.DataFrame(
                    [
                        {
                            "Module": _humanize(row.module_name),
                            "Severity": row.severity.title(),
                            "Code": row.code,
                            "Message": row.message,
                            "Technical detail": row.technical_detail,
                        }
                        for row in warnings
                    ]
                ),
                hide_index=True,
                width="stretch",
                height=280,
            )
        _bottom_collapse(
            "Coverage and Warnings",
            f"personal_detail_coverage_{project_id}",
        )


def _render_corpus_settings(
    repository: ProjectRepository,
    project_id: str,
) -> None:
    project = repository.get_project(project_id)
    with st.expander("Local Storage and Method", expanded=False):
        st.write(
            "The Personal Corpus uses the same versioned SQLite schema and "
            "analysis pipeline as Project / Corpus, but it lives in its own local "
            "database and does not appear in the main project selector."
        )
        st.code(str(repository.database_path), language=None)
        render_dataframe(
            pd.DataFrame(
                [
                    {
                        "Corpus": project.title,
                        "Poems": len(repository.list_texts(project_id)),
                        "Schema": SCHEMA_VERSION,
                        "Created": project.created_at,
                        "Last modified": project.updated_at,
                    }
                ]
            ),
            hide_index=True,
            width="stretch",
        )
        st.caption(
            "Back up the database file while VerseVAD is closed if you want an "
            "independent local copy. Personal-corpus databases, texts, and exports "
            "remain excluded from source control."
        )
        _bottom_collapse(
            "Local Storage and Method",
            f"personal_settings_{project_id}",
        )


def render_personal_corpus_workspace(
    preprocessor: TextPreprocessor,
    resource_readiness: ResourceReadiness,
) -> None:
    """Render a locally persistent personal library using shared corpus services."""

    repository = _project_repository_for_path(
        str(default_personal_corpus_database_path())
    )
    project = _personal_project(repository)
    project_id = project.project_id
    texts = repository.list_texts(project_id)

    with st.sidebar:
        st.markdown("### Personal Corpus")
        st.success("Poems, metadata, and results stay on this computer.")
        st.caption(f"Database: {repository.database_path}")
        st.markdown("---")
        st.caption(
            "Personal Corpus reuses VerseVAD's corpus analysis engines; it does "
            "not duplicate or send your poems elsewhere."
        )

    render_workspace_header(
        "Personal Corpus",
        "Build and maintain a private local poetry library, inspect individual "
        "poems or whole-corpus profiles, run the usual configurable analyses, "
        "compare with VerseMap, and export auditable research reports.",
        kicker="Private personal poetry library",
        status="Persistent · local only",
    )
    flash = st.session_state.pop("personal_corpus_flash", None)
    if flash:
        st.success(flash)

    summary = st.columns(4)
    summary[0].metric("Poems", len(texts))
    summary[1].metric(
        "Analyzed",
        len(
            {
                row.text_id
                for row in repository.list_latest_metrics(project_id)
            }
            | {
                row.text_id
                for row in repository.list_latest_module_results(project_id)
            }
        ),
    )
    summary[2].metric("Schema", SCHEMA_VERSION)
    summary[3].metric("Last modified", project.updated_at[:10])
    st.caption(
        "Affective and optional-module controls behave exactly as they do in "
        "Project / Corpus. VerseMap alone remains pinned to Standard Profile 1.0."
    )

    sections = (
        "Poems & Metadata",
        "Poem Detail",
        "Corpus Analysis",
        "Language Profile",
        "VerseMap",
        "Review & Scenarios",
        "Export",
        "Corpus Settings",
    )
    state_key = f"personal_corpus_report_section_{project_id}"
    active_section, report_controls_container, containers = (
        render_stateful_section_navigation(
            "Report Section",
            sections,
            state_key=state_key,
            container_key_prefix=state_key.replace("-", "_"),
            default="Poems & Metadata",
            control="dropdown",
            help_text=(
                "The selected report remains active when imports, filters, "
                "analyses, or downloads refresh the page."
            ),
            include_header_container=True,
        )
    )
    with report_controls_container:
        profile_state = render_report_profile_controls(
            f"personal_corpus_{project_id}",
        )

    if active_section == "Poems & Metadata":
        container = containers["Poems & Metadata"]
    elif active_section == "Poem Detail":
        container = containers["Poem Detail"]
    elif active_section == "Corpus Analysis":
        container = containers["Corpus Analysis"]
    elif active_section == "Language Profile":
        container = containers["Language Profile"]
    elif active_section == "VerseMap":
        container = containers["VerseMap"]
    elif active_section == "Review & Scenarios":
        container = containers["Review & Scenarios"]
    elif active_section == "Export":
        container = containers["Export"]
    else:
        container = containers["Corpus Settings"]

    with container:
        if active_section == "Poems & Metadata":
            _render_library(repository, project_id)
        elif active_section == "Poem Detail":
            _render_poem_detail(
                repository,
                project_id,
                profile_state.selection,
            )
        elif active_section == "Corpus Analysis":
            with st.expander("Corpus Analysis and Comparisons", expanded=False):
                _render_analysis_tab(
                    repository,
                    project_id,
                    preprocessor,
                    resource_readiness,
                )
                _bottom_collapse(
                    "Corpus Analysis and Comparisons",
                    f"personal_analysis_{project_id}",
                )
        elif active_section == "Language Profile":
            with st.expander("Corpus Language Profile", expanded=False):
                _render_part_of_speech_tab(
                    repository,
                    project_id,
                    preprocessor,
                )
                _bottom_collapse(
                    "Corpus Language Profile",
                    f"personal_language_{project_id}",
                )
        elif active_section == "VerseMap":
            st.caption(fixed_profile_notice("versemap"))
            with st.expander("Personal Corpus VerseMap", expanded=False):
                _render_versemap_tab(repository, project_id)
                _bottom_collapse(
                    "Personal Corpus VerseMap",
                    f"personal_versemap_{project_id}",
                )
        elif active_section == "Review & Scenarios":
            with st.expander("Review Decisions and Scenarios", expanded=False):
                _render_review_tab(repository, project_id)
                _bottom_collapse(
                    "Review Decisions and Scenarios",
                    f"personal_review_{project_id}",
                )
        elif active_section == "Export":
            with st.expander("CSV and Word Reports", expanded=False):
                part_of_speech_rows = _corpus_part_of_speech_rows(
                    repository,
                    project_id,
                    preprocessor,
                )
                _render_export_tab(
                    repository,
                    project_id,
                    part_of_speech_rows,
                )
                _bottom_collapse(
                    "CSV and Word Reports",
                    f"personal_export_{project_id}",
                )
        else:
            _render_corpus_settings(repository, project_id)


__all__ = ["render_personal_corpus_workspace"]
