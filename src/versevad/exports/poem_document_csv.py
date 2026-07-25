"""Tabular exports for the shared processing representation."""

from __future__ import annotations

import csv
import io
from dataclasses import asdict
from enum import Enum
from typing import Iterable, Mapping

from versevad.core.documents import PoemDocument


def _value(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return " | ".join(str(_value(item)) for item in value)
    if isinstance(value, dict):
        return " | ".join(
            f"{key}={_value(item)}" for key, item in sorted(value.items())
        )
    return value


def _row(value: object) -> dict[str, object]:
    return {key: _value(item) for key, item in asdict(value).items()}


def _csv_bytes(
    fieldnames: list[str],
    rows: Iterable[Mapping[str, object]],
) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def _records_csv(records: tuple[object, ...], fallback_fields: list[str]) -> bytes:
    rows = [_row(record) for record in records]
    fields = list(rows[0]) if rows else fallback_fields
    return _csv_bytes(fields, rows)


def export_poem_document_csv_bundle(
    poem_document: PoemDocument,
) -> dict[str, bytes]:
    """Return CSV files that losslessly expose the shared processing evidence."""

    source = poem_document.source
    configuration = _row(poem_document.configuration)
    configuration["configuration_id"] = (
        poem_document.configuration.configuration_id
    )
    preprocessing = _row(poem_document.preprocessing)
    source_row = {
        **_row(source),
        **{f"preprocessing_{key}": value for key, value in preprocessing.items()},
    }
    classifications = {
        row.token_id: _row(row)
        for row in poem_document.token_classifications
    }
    token_rows: list[dict[str, object]] = []
    for token in poem_document.tokens:
        row = _row(token)
        row["is_lexical"] = token.is_lexical
        classification = classifications.get(token.token_id, {})
        for key, value in classification.items():
            if key != "token_id":
                row[f"classification_{key}"] = value
        token_rows.append(row)

    return {
        "processing_source.csv": _csv_bytes(list(source_row), [source_row]),
        "processing_configuration.csv": _csv_bytes(
            list(configuration),
            [configuration],
        ),
        "processing_structure.csv": _records_csv(
            poem_document.structural_units,
            [
                "unit_id",
                "text_id",
                "text_version_id",
                "kind",
                "ordinal",
                "parent_id",
                "character_start",
                "character_end",
                "raw_text",
                "content_text",
                "line_ending",
                "indentation",
                "is_blank",
            ],
        ),
        "processing_sentences.csv": _records_csv(
            poem_document.sentences,
            [
                "sentence_id",
                "text_id",
                "text_version_id",
                "ordinal",
                "character_start",
                "character_end",
                "raw_text",
                "token_ids",
                "line_numbers",
                "stanza_numbers",
                "crosses_line_boundary",
                "crosses_stanza_boundary",
            ],
        ),
        "processing_tokens.csv": _csv_bytes(
            list(token_rows[0]) if token_rows else ["token_id"],
            token_rows,
        ),
        "processing_dependencies.csv": _records_csv(
            poem_document.dependencies,
            [
                "token_id",
                "head_token_id",
                "dependency_label",
                "sentence_id",
                "crosses_line_boundary",
                "crosses_stanza_boundary",
                "confidence",
            ],
        ),
        "processing_entities.csv": _records_csv(
            poem_document.entities,
            [
                "entity_id",
                "label",
                "character_start",
                "character_end",
                "raw_text",
                "token_ids",
                "line_numbers",
                "stanza_numbers",
            ],
        ),
        "processing_orthographic_spans.csv": _records_csv(
            poem_document.orthographic_spans,
            [
                "span_id",
                "kind",
                "character_start",
                "character_end",
                "raw_text",
                "token_ids",
                "line_number",
                "stanza_number",
            ],
        ),
        "processing_coverage.csv": _csv_bytes(
            list(asdict(poem_document.coverage)),
            [_row(poem_document.coverage)],
        ),
        "processing_warnings.csv": _records_csv(
            poem_document.warnings,
            ["code", "message", "severity", "technical_detail"],
        ),
    }


__all__ = ["export_poem_document_csv_bundle"]
