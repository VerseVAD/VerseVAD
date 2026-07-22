"""Read-only adapter for the NRC Emotion Intensity Lexicon source."""

from __future__ import annotations

import csv
from pathlib import Path

from versevad.adapters.base import (
    LexiconAdapterError,
    current_utc_timestamp,
    source_sha256,
    validate_readable_utf8,
)
from versevad.models import (
    EmotionIntensityEntry,
    EmotionIntensityLexicon,
    LexiconMetadata,
    LexiconValidation,
    LexiconValueKind,
)
from versevad.normalization import normalize_lookup


INTENSITY_CATEGORIES = (
    "anger",
    "anticipation",
    "disgust",
    "fear",
    "joy",
    "sadness",
    "surprise",
    "trust",
)


class NrcEmotionIntensityAdapter:
    adapter_version = "0.2.0"

    @property
    def metadata(self) -> LexiconMetadata:
        return LexiconMetadata(
            lexicon_id="nrc_emotion_intensity_v1",
            display_name="NRC Emotion Intensity Lexicon v1",
            family="NRC Emotion Intensity Lexicon",
            version="1 (March 2020)",
            language="English",
            unit_of_analysis="independently scored word-emotion pairs",
            source_scale_min=0.0,
            source_scale_max=1.0,
            normalization_formula="normalized = original (identity)",
            adapter_version=self.adapter_version,
            citation=(
                "Mohammad, S. M. (2018). Word Affect Intensities. Proceedings "
                "of the 11th Language Resources and Evaluation Conference."
            ),
            license_notice=(
                "Free for non-commercial research and educational use with "
                "attribution; source-data redistribution is prohibited."
            ),
            phrase_support=False,
            value_kind=LexiconValueKind.EMOTION_INTENSITY,
            dimensions=INTENSITY_CATEGORIES,
            source_format="UTF-8 headerless term-category-intensity TSV",
            column_mapping=(
                ("term", "column 1"),
                ("category", "column 2"),
                ("intensity", "column 3"),
            ),
            expected_duplicate_behavior="Each term-category pair must be unique",
            preprocessing_assumptions="Word-level source; no phrase matching",
        )

    def load(self, source_path: Path) -> EmotionIntensityLexicon:
        source_path = Path(source_path)
        validate_readable_utf8(source_path, self.metadata.display_name)
        grouped: dict[str, dict[str, object]] = {}
        seen_pairs: set[tuple[str, str]] = set()
        total_rows = blank_terms = malformed_rows = duplicate_keys = 0
        out_of_range = phrase_entries = 0
        with source_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, delimiter="\t")
            for source_row, columns in enumerate(reader, start=1):
                total_rows += 1
                if len(columns) != 3:
                    malformed_rows += 1
                    continue
                term, category, raw_value = columns
                term = term.strip()
                category = category.strip()
                if not term:
                    blank_terms += 1
                    continue
                if any(character.isspace() for character in term):
                    phrase_entries += 1
                try:
                    value = float(raw_value)
                except ValueError:
                    malformed_rows += 1
                    continue
                if category not in INTENSITY_CATEGORIES or not 0.0 <= value <= 1.0:
                    out_of_range += 1
                    continue
                lookup = normalize_lookup(term)
                pair = (lookup, category)
                if pair in seen_pairs:
                    duplicate_keys += 1
                    continue
                seen_pairs.add(pair)
                group = grouped.setdefault(
                    lookup,
                    {"term": term, "rows": [], "intensities": []},
                )
                if group["term"] != term:
                    duplicate_keys += 1
                    continue
                group["rows"].append(source_row)
                group["intensities"].append((category, value))

        errors = []
        if blank_terms:
            errors.append(f"Found {blank_terms} blank terms.")
        if malformed_rows:
            errors.append(f"Found {malformed_rows} malformed rows.")
        if duplicate_keys:
            errors.append(f"Found {duplicate_keys} duplicate or conflicting pairs.")
        if out_of_range:
            errors.append(f"Found {out_of_range} invalid categories or scores.")
        if errors:
            raise LexiconAdapterError(
                "VerseVAD found structural problems in the NRC Emotion Intensity "
                "Lexicon and stopped before analysis. No source file was changed.",
                technical_detail=" ".join(errors),
            )
        entries = {
            lookup: EmotionIntensityEntry(
                lexicon_id=self.metadata.lexicon_id,
                source_term=str(group["term"]),
                lookup_form=lookup,
                source_rows=tuple(group["rows"]),
                intensities=tuple(sorted(group["intensities"])),
            )
            for lookup, group in grouped.items()
        }
        validation = LexiconValidation(
            source_path=source_path.resolve(),
            source_sha256=source_sha256(source_path),
            total_rows=total_rows,
            usable_entries=len(entries),
            phrase_entries=phrase_entries,
            blank_terms=blank_terms,
            malformed_rows=malformed_rows,
            duplicate_keys=duplicate_keys,
            conflicting_normalized_keys=0,
            out_of_range_scores=out_of_range,
            loaded_at_utc=current_utc_timestamp(),
        )
        return EmotionIntensityLexicon.create(self.metadata, entries, validation)
