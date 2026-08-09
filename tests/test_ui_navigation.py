from __future__ import annotations

from types import SimpleNamespace

import pytest

import versevad.ui.navigation as navigation
import versevad.ui.research as research


class _SwitchedPage(RuntimeError):
    pass


def test_direct_workspace_switch_consumes_pending_fallback(monkeypatch) -> None:
    state = {
        "_pending_workspace_switch": "Single Poem",
        "_versevad_workspace_pages": {"Single Poem": "single-poem-page"},
    }

    def switch_page(page: object) -> None:
        assert page == "single-poem-page"
        raise _SwitchedPage

    fake_streamlit = SimpleNamespace(
        session_state=state,
        switch_page=switch_page,
        rerun=lambda: pytest.fail("The fallback rerun should not be used."),
    )
    monkeypatch.setattr(navigation, "st", fake_streamlit)

    with pytest.raises(_SwitchedPage):
        navigation.switch_to_workspace("Single Poem")

    assert "_pending_workspace_switch" not in state


def test_direct_workspace_switch_does_not_rerun_after_page_accepts_switch(
    monkeypatch,
) -> None:
    state = {
        "_pending_workspace_switch": "Single Poem",
        "_versevad_workspace_pages": {"Single Poem": "single-poem-page"},
    }
    switched: list[object] = []
    fake_streamlit = SimpleNamespace(
        session_state=state,
        switch_page=switched.append,
        rerun=lambda: pytest.fail(
            "A registered page switch must not call st.rerun()."
        ),
    )
    monkeypatch.setattr(navigation, "st", fake_streamlit)

    navigation.switch_to_workspace("Single Poem")

    assert switched == ["single-poem-page"]
    assert "_pending_workspace_switch" not in state


def test_workspace_switch_retains_fallback_without_registered_page(monkeypatch) -> None:
    state: dict[str, object] = {}

    class _Rerun(RuntimeError):
        pass

    fake_streamlit = SimpleNamespace(
        session_state=state,
        switch_page=lambda page: pytest.fail("No page was registered."),
        rerun=lambda: (_ for _ in ()).throw(_Rerun()),
    )
    monkeypatch.setattr(navigation, "st", fake_streamlit)

    with pytest.raises(_Rerun):
        navigation.switch_to_workspace("Single Poem")

    assert state["_pending_workspace_switch"] == "Single Poem"


@pytest.mark.parametrize(
    "workspace",
    [
        "Single Poem",
        "Other Text",
        "Compare Poems",
        "Lexicon Explorer",
        "VerseMap",
        "Saved Projects",
        "Personal Corpus",
    ],
)
def test_open_library_revision_navigates_to_restored_workspace(
    monkeypatch,
    workspace: str,
) -> None:
    restored: list[tuple[object, object]] = []
    navigated: list[str] = []
    item = object()
    revision = object()

    def restore(saved_item: object, saved_revision: object) -> str:
        restored.append((saved_item, saved_revision))
        return workspace

    monkeypatch.setattr(research, "restore_library_revision", restore)
    monkeypatch.setattr(navigation, "switch_to_workspace", navigated.append)

    research.open_library_revision(item, revision)

    assert restored == [(item, revision)]
    assert navigated == [workspace]
