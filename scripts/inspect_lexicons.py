"""Read-only structural validation for the five VerseVAD source lexicons.

This script uses only the Python standard library. It reads the source files,
computes hashes and structural statistics, and prints JSON to standard output.
It never writes to or modifies ``source_lexicons``.
"""

from __future__ import annotations

import argparse
import codecs
import csv
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class LexiconSpec:
    lexicon_id: str
    relative_path: str
    delimiter: str
    has_header: bool
    term_column: str | int
    key_columns: tuple[str | int, ...]
    score_columns: tuple[str | int, ...]
    expected_score_min: float
    expected_score_max: float
    category_column: str | int | None = None


SPECS = (
    LexiconSpec(
        lexicon_id="warriner_vad_2013",
        relative_path="XANEW-master/XANEW-master/Ratings_Warriner_et_al.csv",
        delimiter=",",
        has_header=True,
        term_column="Word",
        key_columns=("Word",),
        score_columns=("V.Mean.Sum", "A.Mean.Sum", "D.Mean.Sum"),
        expected_score_min=1.0,
        expected_score_max=9.0,
    ),
    LexiconSpec(
        lexicon_id="nrc_vad_v1",
        relative_path="NRC-VAD-Lexicon/NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt",
        delimiter="\t",
        has_header=False,
        term_column=0,
        key_columns=(0,),
        score_columns=(1, 2, 3),
        expected_score_min=0.0,
        expected_score_max=1.0,
    ),
    LexiconSpec(
        lexicon_id="nrc_vad_v2_1",
        relative_path=(
            "NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1/"
            "NRC-VAD-Lexicon-v2.1.txt"
        ),
        delimiter="\t",
        has_header=True,
        term_column="term",
        key_columns=("term",),
        score_columns=("valence", "arousal", "dominance"),
        expected_score_min=-1.0,
        expected_score_max=1.0,
    ),
    LexiconSpec(
        lexicon_id="nrc_emotion_v0_92",
        relative_path=(
            "NRC-Emotion-Lexicon/NRC-Emotion-Lexicon/"
            "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt"
        ),
        delimiter="\t",
        has_header=False,
        term_column=0,
        key_columns=(0, 1),
        score_columns=(2,),
        expected_score_min=0.0,
        expected_score_max=1.0,
        category_column=1,
    ),
    LexiconSpec(
        lexicon_id="nrc_emotion_intensity_v1",
        relative_path=(
            "NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon/"
            "NRC-Emotion-Intensity-Lexicon-v1.txt"
        ),
        delimiter="\t",
        has_header=False,
        term_column=0,
        key_columns=(0, 1),
        score_columns=(2,),
        expected_score_min=0.0,
        expected_score_max=1.0,
        category_column=1,
    ),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def detect_encoding(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    for encoding in ("utf-8", "cp1252"):
        try:
            raw.decode(encoding)
            return encoding
        except UnicodeDecodeError:
            continue
    return "undetermined"


def get_value(row: dict[str, str] | list[str], column: str | int) -> str:
    if isinstance(row, dict):
        assert isinstance(column, str)
        return row[column]
    assert isinstance(column, int)
    return row[column]


def parse_rows(
    path: Path, spec: LexiconSpec, encoding: str
) -> tuple[Iterable[dict[str, str] | list[str]], Callable[[], None], list[str]]:
    source = path.open("r", encoding=encoding, newline="")
    if spec.has_header:
        reader = csv.DictReader(source, delimiter=spec.delimiter)
        fieldnames = list(reader.fieldnames or [])
    else:
        reader = csv.reader(source, delimiter=spec.delimiter)
        fieldnames = []
    return reader, source.close, fieldnames


def inspect_one(source_root: Path, spec: LexiconSpec) -> dict[str, object]:
    path = source_root / Path(spec.relative_path)
    result: dict[str, object] = {
        "lexicon_id": spec.lexicon_id,
        "source_file": spec.relative_path,
        "exists": path.is_file(),
    }
    if not path.is_file():
        result["errors"] = ["Source file is missing."]
        return result

    encoding = detect_encoding(path)
    result.update(
        {
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
            "encoding": encoding,
            "expected_score_range": [
                spec.expected_score_min,
                spec.expected_score_max,
            ],
        }
    )
    if encoding == "undetermined":
        result["errors"] = ["Encoding could not be determined."]
        return result

    rows, close, fieldnames = parse_rows(path, spec, encoding)
    required_named_columns = {
        column
        for column in (
            spec.term_column,
            *spec.key_columns,
            *spec.score_columns,
            spec.category_column,
        )
        if isinstance(column, str)
    }
    missing_columns = sorted(required_named_columns.difference(fieldnames))

    row_count = 0
    malformed_rows = 0
    blank_terms = 0
    phrase_rows = 0
    out_of_range_scores = 0
    keys: Counter[tuple[str, ...]] = Counter()
    normalized_key_sources: dict[tuple[str, ...], set[tuple[str, ...]]] = {}
    terms: set[str] = set()
    categories: Counter[str] = Counter()
    observed_min: dict[str, float] = {}
    observed_max: dict[str, float] = {}

    try:
        if missing_columns:
            return {
                **result,
                "header": fieldnames,
                "missing_required_columns": missing_columns,
                "errors": ["Required named columns are missing."],
            }

        for row in rows:
            row_count += 1
            try:
                term = get_value(row, spec.term_column).strip()
                key = tuple(get_value(row, column).strip() for column in spec.key_columns)
                score_pairs = [
                    (str(column), float(get_value(row, column)))
                    for column in spec.score_columns
                ]
                category = (
                    get_value(row, spec.category_column).strip()
                    if spec.category_column is not None
                    else None
                )
            except (IndexError, KeyError, TypeError, ValueError):
                malformed_rows += 1
                continue

            if not term:
                blank_terms += 1
            if any(character.isspace() for character in term):
                phrase_rows += 1
            terms.add(term)
            keys[key] += 1
            normalized_key = (
                unicodedata.normalize("NFC", term).casefold(),
                *key[1:],
            )
            normalized_key_sources.setdefault(normalized_key, set()).add(key)
            if category is not None:
                categories[category] += 1

            for score_name, score in score_pairs:
                observed_min[score_name] = min(observed_min.get(score_name, score), score)
                observed_max[score_name] = max(observed_max.get(score_name, score), score)
                if not spec.expected_score_min <= score <= spec.expected_score_max:
                    out_of_range_scores += 1
    finally:
        close()

    duplicate_key_count = sum(1 for count in keys.values() if count > 1)
    duplicate_row_excess = sum(count - 1 for count in keys.values() if count > 1)
    conflicting_normalized_keys = sum(
        1 for sources in normalized_key_sources.values() if len(sources) > 1
    )
    result.update(
        {
            "header": fieldnames,
            "missing_required_columns": missing_columns,
            "rows": row_count,
            "unique_terms": len(terms),
            "phrase_rows": phrase_rows,
            "blank_terms": blank_terms,
            "malformed_rows": malformed_rows,
            "duplicate_keys": duplicate_key_count,
            "duplicate_row_excess": duplicate_row_excess,
            "conflicting_normalized_keys": conflicting_normalized_keys,
            "observed_score_min": observed_min,
            "observed_score_max": observed_max,
            "out_of_range_scores": out_of_range_scores,
            "categories": dict(sorted(categories.items())),
            "errors": [],
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect VerseVAD source lexicons without modifying them."
    )
    parser.add_argument(
        "source_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "source_lexicons",
        help="Path to the source_lexicons directory.",
    )
    args = parser.parse_args()

    report = {
        "source_root": str(args.source_root.resolve()),
        "read_only": True,
        "lexicons": [inspect_one(args.source_root, spec) for spec in SPECS],
    }
    json.dump(report, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 1 if any(item["errors"] for item in report["lexicons"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
