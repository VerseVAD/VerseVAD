"""Machine-readable export of the shared poetry-processing representation."""

from __future__ import annotations

import json
from dataclasses import asdict

from versevad.core.documents import PoemDocument


def export_poem_document_json(poem_document: PoemDocument) -> bytes:
    """Serialize exact source, annotations, coverage, warnings, and provenance."""

    payload = asdict(poem_document)
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
