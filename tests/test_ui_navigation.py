from __future__ import annotations

from types import SimpleNamespace

import pytest

import versevad.ui.navigation as navigation


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
