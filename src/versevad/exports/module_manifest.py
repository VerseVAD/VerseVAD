"""Common CSV manifest for optional-module configuration and provenance."""

from __future__ import annotations

import csv
import io
from dataclasses import fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable, Mapping


def _flatten(value: object, *, path: str) -> Iterable[dict[str, object]]:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            yield from _flatten(
                getattr(value, field.name),
                path=f"{path}.{field.name}",
            )
        return
    if isinstance(value, Mapping):
        for key in sorted(value):
            yield from _flatten(
                value[key],
                path=f"{path}.{key}",
            )
        if not value:
            yield {"path": path, "value": ""}
        return
    if isinstance(value, (tuple, list)):
        for index, item in enumerate(value, start=1):
            yield from _flatten(item, path=f"{path}[{index}]")
        if not value:
            yield {"path": path, "value": ""}
        return
    if isinstance(value, Enum):
        value = value.value
    elif isinstance(value, Path):
        value = str(value)
    yield {"path": path, "value": "" if value is None else value}


def export_module_manifest_csv(result: object) -> bytes:
    """Expose identifiers, configuration, provenance, coverage, and warnings."""

    module_result = getattr(result, "module_result")
    sections: list[tuple[str, object]] = [
        (
            "module",
            {
                "result_id": module_result.result_id,
                "module_name": module_result.module_name,
                "module_version": module_result.module_version,
                "text_id": module_result.text_id,
                "text_version_id": module_result.text_version_id,
            },
        ),
        ("configuration", getattr(result, "configuration")),
        ("provenance", module_result.provenance),
        ("coverage", module_result.coverage),
        ("warnings", module_result.warnings),
    ]
    for name in ("resource_status", "resource_validation"):
        if hasattr(result, name):
            sections.append((name, getattr(result, name)))
    rows = [
        row
        for section, value in sections
        for row in _flatten(value, path=section)
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["path", "value"])
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


__all__ = ["export_module_manifest_csv"]
