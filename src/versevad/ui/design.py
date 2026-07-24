"""Shared Stage 13 visual system and reusable Streamlit presentation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Mapping, Sequence

import altair as alt
import streamlit as st

from versevad import __version__
from versevad.ui.preferences import (
    AppearanceMode,
    load_preferences,
    save_appearance,
)


WORKSPACES = (
    "Single Poem",
    "Project / Corpus",
    "Other Text",
    "Lexicon Explorer",
)

LIGHT_TOKENS = {
    "background": "#f6f3ed",
    "surface": "#fffdf9",
    "surface-raised": "#ffffff",
    "surface-muted": "#eee9df",
    "text-primary": "#17242d",
    "text-secondary": "#59656d",
    "text-inverse": "#ffffff",
    "border": "#d9d3c8",
    "border-strong": "#a9a197",
    "accent": "#7a3524",
    "accent-strong": "#5f2619",
    "accent-soft": "#f2e6df",
    "success": "#2f654a",
    "success-soft": "#e6f0e9",
    "warning": "#866219",
    "warning-soft": "#f6eed8",
    "danger": "#943c3c",
    "danger-soft": "#f7e6e4",
    "info": "#345f72",
    "info-soft": "#e5eff3",
    "focus": "#176b8a",
    "shadow": "rgba(32, 28, 24, 0.10)",
    "chart-grid": "#d8d2c8",
    "chart-label": "#34434c",
}

DARK_TOKENS = {
    "background": "#11171b",
    "surface": "#182126",
    "surface-raised": "#202a30",
    "surface-muted": "#28343b",
    "text-primary": "#f3f0e9",
    "text-secondary": "#b8c1c5",
    "text-inverse": "#11171b",
    "border": "#3b484f",
    "border-strong": "#65737a",
    "accent": "#d58a6d",
    "accent-strong": "#efaa8f",
    "accent-soft": "#3d2a25",
    "success": "#8fc8a6",
    "success-soft": "#20372b",
    "warning": "#e1c37a",
    "warning-soft": "#3c3421",
    "danger": "#ee9994",
    "danger-soft": "#422827",
    "info": "#91c5d7",
    "info-soft": "#213740",
    "focus": "#76c8e6",
    "shadow": "rgba(0, 0, 0, 0.30)",
    "chart-grid": "#46545b",
    "chart-label": "#dce3e5",
}

PUBLICATION_CHART_COLORS = (
    "#9f4528",
    "#c77d3f",
    "#326b78",
    "#4f7658",
    "#705d8f",
)


def publication_chart(chart: alt.Chart) -> alt.Chart:
    """Apply a stable light publication treatment independent of UI appearance."""

    return (
        chart.configure(background="#fffdf9")
        .configure_view(stroke="#d9d3c8")
        .configure_axis(
            domainColor="#a9a197",
            gridColor="#e3ded5",
            labelColor="#34434c",
            titleColor="#17242d",
        )
        .configure_legend(
            labelColor="#34434c",
            titleColor="#17242d",
        )
        .configure_title(color="#17242d")
    )


@dataclass(frozen=True)
class ModulePreset:
    label: str
    description: str
    lexicon_ids: tuple[str, ...]
    modules: tuple[str, ...]


MODULE_PRESETS = {
    "Essential": ModulePreset(
        label="Essential",
        description="VAD, emotion association, and emotion intensity.",
        lexicon_ids=(
            "nrc_vad_v2_1",
            "nrc_emotion_v0_92",
            "nrc_emotion_intensity_v1",
        ),
        modules=(),
    ),
    "Literary": ModulePreset(
        label="Literary",
        description="Core affective evidence plus lexical character and structure.",
        lexicon_ids=(
            "warriner_vad_2013",
            "nrc_vad_v2_1",
            "nrc_emotion_v0_92",
            "nrc_emotion_intensity_v1",
        ),
        modules=(
            "include_concreteness",
            "include_frequency",
            "include_aoa",
            "include_lexical_style",
            "include_poetry_id",
        ),
    ),
    "Sound and Form": ModulePreset(
        label="Sound and Form",
        description="Pronunciation, meter, rhyme/sound, and structural measures.",
        lexicon_ids=(),
        modules=(
            "include_pronunciation",
            "include_meter",
            "include_phonology",
            "include_lexical_style",
        ),
    ),
    "Complete": ModulePreset(
        label="Complete",
        description="Every installed analytical module.",
        lexicon_ids=(
            "warriner_vad_2013",
            "nrc_vad_v1",
            "nrc_vad_v2_1",
            "nrc_emotion_v0_92",
            "nrc_emotion_intensity_v1",
        ),
        modules=(
            "include_concreteness",
            "include_frequency",
            "include_aoa",
            "include_lexical_style",
            "include_poetry_id",
            "include_pronunciation",
            "include_meter",
            "include_phonology",
        ),
    ),
    "Custom": ModulePreset(
        label="Custom",
        description="Keep the current manual module selection.",
        lexicon_ids=(),
        modules=(),
    ),
}

_OPTIONAL_MODULE_KEYS = frozenset(
    key
    for preset in MODULE_PRESETS.values()
    for key in preset.modules
)


def preset_widget_state(
    preset_name: str,
    *,
    available_lexicon_ids: Sequence[str],
) -> dict[str, object]:
    """Return only module-selection state; advanced settings are never touched."""

    preset = MODULE_PRESETS[preset_name]
    if preset_name == "Custom":
        return {}
    available = set(available_lexicon_ids)
    selected = [item for item in preset.lexicon_ids if item in available]
    state: dict[str, object] = {"selected_lexicons": selected}
    enabled = set(preset.modules)
    state.update({key: key in enabled for key in _OPTIONAL_MODULE_KEYS})
    return state


def _token_declarations(tokens: Mapping[str, str]) -> str:
    return "\n".join(f"      --color-{name}: {value};" for name, value in tokens.items())


def stylesheet_for(mode: AppearanceMode | str) -> str:
    appearance = AppearanceMode(mode)
    base = DARK_TOKENS if appearance is AppearanceMode.DARK else LIGHT_TOKENS
    system_override = ""
    if appearance is AppearanceMode.SYSTEM:
        system_override = f"""
    @media (prefers-color-scheme: dark) {{
      :root {{
{_token_declarations(DARK_TOKENS)}
        color-scheme: dark;
      }}
    }}
"""
    return f"""
    <style>
    :root {{
{_token_declarations(base)}
      color-scheme: {"dark" if appearance is AppearanceMode.DARK else "light"};
      --font-interface: Inter, "Segoe UI", Arial, sans-serif;
      --font-literary: Georgia, "Times New Roman", serif;
      --space-1: .25rem;
      --space-2: .5rem;
      --space-3: .75rem;
      --space-4: 1rem;
      --space-6: 1.5rem;
      --space-8: 2rem;
      --radius-small: .35rem;
      --radius-medium: .7rem;
      --radius-large: 1rem;
      --transition-fast: 120ms ease;
    }}
{system_override}
    html, body, [class*="css"] {{
      font-family: var(--font-interface);
      color: var(--color-text-primary);
    }}
    .stApp {{
      background: var(--color-background);
      color: var(--color-text-primary);
      transition: background-color var(--transition-fast), color var(--transition-fast);
    }}
    .main .block-container {{
      max-width: 92rem;
      padding-top: 1rem;
      padding-bottom: 4rem;
    }}
    h1, h2, h3, h4 {{
      color: var(--color-text-primary);
      letter-spacing: -.012em;
    }}
    h1, .versevad-literary {{
      font-family: var(--font-literary);
    }}
    p, label, [data-testid="stCaptionContainer"] {{
      color: var(--color-text-secondary);
    }}
    a {{
      color: var(--color-accent);
    }}
    [data-testid="stSidebar"] {{
      background: var(--color-surface-muted);
      border-right: 1px solid var(--color-border);
    }}
    [data-testid="stHeader"] {{
      background: transparent;
    }}
    [data-testid="stMetric"] {{
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-medium);
      padding: .75rem .9rem;
      box-shadow: none;
      font-variant-numeric: tabular-nums;
    }}
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
      color: var(--color-text-primary);
    }}
    [data-testid="stDataFrame"], [data-testid="stTable"] {{
      border: 1px solid var(--color-border);
      border-radius: var(--radius-small);
      overflow: auto;
    }}
    [data-testid="stExpander"], [data-testid="stForm"],
    div[data-testid="stVerticalBlockBorderWrapper"] {{
      background: var(--color-surface);
      border-color: var(--color-border) !important;
      border-radius: var(--radius-medium);
    }}
    [data-baseweb="tab-list"] {{
      gap: var(--space-2);
      overflow-x: auto;
      scrollbar-width: thin;
    }}
    [data-baseweb="tab"] {{
      color: var(--color-text-secondary);
      white-space: nowrap;
    }}
    [aria-selected="true"][data-baseweb="tab"] {{
      color: var(--color-accent-strong);
    }}
    [role="radiogroup"][aria-label="Workspace"] button {{
      background: var(--color-surface) !important;
      border-color: var(--color-border) !important;
      color: var(--color-text-secondary) !important;
    }}
    [role="radiogroup"][aria-label="Workspace"] button p {{
      color: inherit !important;
    }}
    [role="radiogroup"][aria-label="Workspace"] button[data-selected="true"] {{
      background: var(--color-accent-soft) !important;
      border-color: var(--color-accent) !important;
      color: var(--color-accent-strong) !important;
    }}
    button:focus-visible, input:focus-visible, textarea:focus-visible,
    [role="button"]:focus-visible, [role="tab"]:focus-visible {{
      outline: 3px solid var(--color-focus) !important;
      outline-offset: 2px !important;
    }}
    .versevad-shell {{
      background: var(--color-surface-raised);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-large);
      padding: .7rem 1rem;
      box-shadow: 0 .35rem 1rem var(--color-shadow);
      margin-bottom: var(--space-4);
    }}
    .st-key-versevad_global_header {{
      background: var(--color-surface-raised);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-large);
      box-shadow: 0 .35rem 1rem var(--color-shadow);
      margin-bottom: var(--space-4);
      padding: .55rem .8rem;
      position: sticky;
      top: .5rem;
      z-index: 900;
    }}
    .versevad-wordmark {{
      color: var(--color-text-primary);
      font-family: var(--font-literary);
      font-size: 1.55rem;
      font-weight: 700;
      line-height: 1.05;
      white-space: nowrap;
    }}
    .versevad-platform {{
      color: var(--color-text-secondary);
      font-size: .73rem;
      letter-spacing: .08em;
      text-transform: uppercase;
    }}
    .versevad-kicker {{
      color: var(--color-accent);
      font-size: .75rem;
      font-weight: 700;
      letter-spacing: .11em;
      margin-bottom: -.55rem;
      text-transform: uppercase;
    }}
    .versevad-workspace-header {{
      border-bottom: 1px solid var(--color-border);
      margin-bottom: var(--space-6);
      padding: .4rem 0 var(--space-4);
    }}
    .versevad-workspace-header h1 {{
      margin: 0 0 var(--space-2);
    }}
    .versevad-workspace-header p {{
      font-size: 1.02rem;
      margin: 0;
      max-width: 72ch;
    }}
    .versevad-empty {{
      background: var(--color-surface);
      border: 1px dashed var(--color-border-strong);
      border-radius: var(--radius-large);
      padding: var(--space-8);
      text-align: center;
    }}
    .versevad-empty h3 {{
      margin-top: 0;
    }}
    .versevad-callout {{
      background: var(--color-info-soft);
      border-left: 4px solid var(--color-info);
      border-radius: var(--radius-small);
      color: var(--color-text-primary);
      padding: .8rem 1rem;
      margin: .5rem 0 1rem;
    }}
    .versevad-section-intro {{
      color: var(--color-text-secondary);
      margin-top: -.5rem;
      max-width: 76ch;
    }}
    .versevad-status {{
      border: 1px solid var(--color-border);
      border-radius: 999px;
      color: var(--color-text-secondary);
      display: inline-block;
      font-size: .76rem;
      font-weight: 650;
      padding: .18rem .55rem;
    }}
    .versevad-status--complete {{
      background: var(--color-success-soft);
      color: var(--color-success);
    }}
    .versevad-status--warning {{
      background: var(--color-warning-soft);
      color: var(--color-warning);
    }}
    code, pre {{
      background: var(--color-surface-muted) !important;
      color: var(--color-text-primary) !important;
    }}
    #MainMenu, footer {{
      visibility: hidden;
    }}
    @media (max-width: 800px) {{
      .main .block-container {{
        padding-left: .8rem;
        padding-right: .8rem;
      }}
      .st-key-versevad_global_header [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap;
        gap: var(--space-2);
      }}
      .st-key-versevad_global_header [data-testid="stColumn"]:first-child {{
        flex: 1 1 100% !important;
        width: 100% !important;
      }}
      .st-key-versevad_global_header [data-testid="stColumn"]:not(:first-child) {{
        flex: 1 1 7rem !important;
        min-width: 7rem !important;
        width: auto !important;
      }}
      .st-key-versevad_global_header button {{
        white-space: nowrap;
      }}
      .versevad-shell {{
        padding: .6rem;
      }}
      .versevad-empty {{
        padding: var(--space-6) var(--space-4);
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: .01ms !important;
      }}
    }}
    </style>
    """


def apply_design_system(mode: AppearanceMode | str) -> None:
    st.markdown(stylesheet_for(mode), unsafe_allow_html=True)


def _persist_appearance() -> None:
    save_appearance(st.session_state["appearance_mode"])


def render_app_shell() -> tuple[str, AppearanceMode]:
    """Render the shared application header and return active workspace/theme."""

    preferences = load_preferences()
    st.session_state.setdefault("appearance_mode", preferences.appearance.value)
    legacy_workspace = {
        "One Poem": "Single Poem",
        "Projects & Corpus": "Project / Corpus",
    }
    if (
        "workspace_page" in st.session_state
        and st.session_state["workspace_page"] not in WORKSPACES
    ):
        st.session_state["workspace_page"] = legacy_workspace.get(
            st.session_state["workspace_page"],
            WORKSPACES[0],
        )
    appearance = AppearanceMode(st.session_state["appearance_mode"])
    apply_design_system(appearance)

    with st.container(key="versevad_global_header"):
        brand, appearance_column, settings_column, help_column = st.columns(
            [4.5, 1.3, 1, 1],
            vertical_alignment="center",
        )
        with brand:
            st.markdown(
                '<div class="versevad-wordmark">VerseVAD</div>'
                '<div class="versevad-platform">'
                f"Computational Poetics · Version {__version__}"
                "</div>",
                unsafe_allow_html=True,
            )
        with appearance_column:
            st.selectbox(
                "Appearance",
                options=[mode.value for mode in AppearanceMode],
                key="appearance_mode",
                on_change=_persist_appearance,
                help="System follows the browser or operating-system preference.",
            )
        with settings_column:
            with st.popover("Settings", width="stretch"):
                st.markdown("**Interface**")
                st.caption(
                    "Appearance is application-level and never changes an analysis."
                )
                st.markdown("**Analysis defaults**")
                st.caption(
                    "Weighting, thresholds, filtering, pronunciation, and module "
                    "parameters remain explicit in each analysis configuration."
                )
                st.markdown("**Exports & performance**")
                st.caption(
                    "Exports remain publication-light. Cache and worker controls "
                    "will be addressed in the dedicated performance pass."
                )
        with help_column:
            with st.popover("Help", width="stretch"):
                st.markdown("**How to use VerseVAD**")
                st.caption(
                    "Choose a workspace, add or select text, configure evidence, "
                    "run the analysis, then begin with Overview."
                )
                st.caption(
                    "Detailed methodology, values, testing, and user guidance are "
                    "available in the local docs folder and every completed "
                    "module's methodology panel."
                )
        workspace = st.segmented_control(
            "Workspace",
            options=WORKSPACES,
            default=WORKSPACES[0],
            selection_mode="single",
            key="workspace_page",
        )
    return workspace or WORKSPACES[0], appearance


def render_workspace_header(
    title: str,
    description: str,
    *,
    kicker: str,
    status: str | None = None,
) -> None:
    st.markdown(
        f'<div class="versevad-kicker">{escape(kicker)}</div>',
        unsafe_allow_html=True,
    )
    st.title(title)
    if status:
        st.markdown(
            f'<span class="versevad-status">{escape(status)}</span>',
            unsafe_allow_html=True,
        )
    st.write(description)
    st.divider()


def render_empty_state(title: str, description: str, action: str) -> None:
    st.markdown(
        '<div class="versevad-empty">'
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(description)}</p>"
        f"<strong>{escape(action)}</strong>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_section_intro(title: str, purpose: str, *, status: str = "Complete") -> None:
    modifier = "complete" if status == "Complete" else "warning"
    st.markdown(
        f"### {escape(title)} "
        f'<span class="versevad-status versevad-status--{modifier}">'
        f"{escape(status)}</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p class="versevad-section-intro">{escape(purpose)}</p>',
        unsafe_allow_html=True,
    )
