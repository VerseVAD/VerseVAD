"""Arrow-safe formatting helpers for heterogeneous Streamlit tables."""

from __future__ import annotations

import json


def heterogeneous_display_value(value: object) -> str:
    """Render a mixed-type analytical value as explicit display-only text."""

    if value is None:
        return "—"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)
