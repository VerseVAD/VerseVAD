"""Read-only adapters for the two supplied NRC VAD source versions."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from versevad.adapters.base import (
    LexiconAdapterError,
    current_utc_timestamp,
    source_sha256,
    validate_readable_utf8,
)
from versevad.models import (
    LexiconMetadata,
    LexiconValidation,
    VadEntry,
    VadLexicon,
    VadScores,
)
from versevad.normalization import normalize_lookup


@dataclass(frozen=True)
class _NrcVadConfiguration:
    lexicon_id: str
    display_name: str
    version: str
    source_minimum: float
    source_maximum: float
    normalization_formula: str
    has_header: bool
    phrase_support: bool
    citation: str
    unit_of_analysis: str


class _NrcVadAdapter:
    adapter_version = "0.3.0"
    configuration: _NrcVadConfiguration

    @property
    def metadata(self) -> LexiconMetadata:
        config = self.configuration
        return LexiconMetadata(
            lexicon_id=config.lexicon_id,
            display_name=config.display_name,
            family="NRC VAD Lexicon",
            version=config.version,
            language="English",
            unit_of_analysis=config.unit_of_analysis,
            source_scale_min=config.source_minimum,
            source_scale_max=config.source_maximum,
            normalization_formula=config.normalization_formula,
            adapter_version=self.adapter_version,
            citation=config.citation,
            license_notice=(
                "Free for non-commercial research and educational use with "
                "attribution; source-data redistribution is prohibited."
            ),
            phrase_support=config.phrase_support,
            source_format=(
                "UTF-8 tab-separated values with header"
                if config.has_header
                else "UTF-8 headerless four-column tab-separated values"
            ),
            column_mapping=(
                ("term", "term"),
                ("valence", "valence"),
                ("arousal", "arousal"),
                ("dominance", "dominance"),
            ),
            preprocessing_assumptions=(
                "Whitespace-containing source entries use exact longest-first "
                "phrase matching under the selected phrase policy."
                if config.phrase_support
                else "Whitespace-containing source entries remain inactive."
            ),
        )

    def _normalize(self, value: float) -> float:
        if self.configuration.source_minimum == 0.0:
            return value
        return (value + 1.0) / 2.0

    def load(self, source_path: Path) -> VadLexicon:
        source_path = Path(source_path)
        validate_readable_utf8(source_path, self.configuration.display_name)
        entries: dict[str, VadEntry] = {}
        conflicts: dict[str, tuple[VadEntry, ...]] = {}
        total_rows = blank_terms = malformed_rows = duplicate_keys = 0
        out_of_range = phrase_entries = 0

        with source_path.open("r", encoding="utf-8-sig", newline="") as source:
            reader = csv.reader(source, delimiter="\t")
            first_data_row = 2 if self.configuration.has_header else 1
            if self.configuration.has_header:
                header = next(reader, None)
                if header != ["term", "valence", "arousal", "dominance"]:
                    raise LexiconAdapterError(
                        "VerseVAD could not find the expected NRC VAD v2.1 "
                        "header. No source file was changed.",
                        technical_detail=f"Found header: {header!r}",
                    )
            for source_row, columns in enumerate(reader, start=first_data_row):
                total_rows += 1
                if len(columns) != 4:
                    malformed_rows += 1
                    continue
                term = columns[0].strip()
                if not term:
                    blank_terms += 1
                    continue
                if any(character.isspace() for character in term):
                    phrase_entries += 1
                try:
                    original = VadScores(*(float(value) for value in columns[1:]))
                except ValueError:
                    malformed_rows += 1
                    continue
                limits = (
                    self.configuration.source_minimum,
                    self.configuration.source_maximum,
                )
                if any(not limits[0] <= value <= limits[1] for value in original.as_dict().values()):
                    out_of_range += 1
                    continue
                entry = VadEntry(
                    lexicon_id=self.metadata.lexicon_id,
                    source_term=term,
                    lookup_form=normalize_lookup(term),
                    source_row=source_row,
                    original=original,
                    normalized=VadScores(
                        self._normalize(original.valence),
                        self._normalize(original.arousal),
                        self._normalize(original.dominance),
                    ),
                )
                key = entry.lookup_form
                if key in entries:
                    existing = entries.pop(key)
                    if existing.source_term == term:
                        duplicate_keys += 1
                        entries[key] = existing
                    else:
                        conflicts[key] = (existing, entry)
                elif key in conflicts:
                    group = conflicts[key]
                    if any(item.source_term == term for item in group):
                        duplicate_keys += 1
                    else:
                        conflicts[key] = (*group, entry)
                else:
                    entries[key] = entry

        errors = []
        if blank_terms:
            errors.append(f"Found {blank_terms} blank terms.")
        if malformed_rows:
            errors.append(f"Found {malformed_rows} malformed rows.")
        if duplicate_keys:
            errors.append(f"Found {duplicate_keys} duplicate normalized terms.")
        if out_of_range:
            errors.append(f"Found {out_of_range} scores outside the declared scale.")
        if conflicts:
            errors.append(f"Found {len(conflicts)} conflicting normalized terms.")
        if errors:
            raise LexiconAdapterError(
                f"VerseVAD found structural problems in the {self.metadata.display_name} "
                "file and stopped before analysis. No source file was changed.",
                technical_detail=" ".join(errors),
            )
        warnings = ()
        if phrase_entries and not self.metadata.phrase_support:
            warnings = (
                f"Retained {phrase_entries} whitespace-containing source entries, "
                "but the documented word-level Phase 2 policy does not activate "
                "them as phrases.",
            )
        validation = LexiconValidation(
            source_path=source_path.resolve(),
            source_sha256=source_sha256(source_path),
            total_rows=total_rows,
            usable_entries=len(entries),
            phrase_entries=phrase_entries,
            blank_terms=blank_terms,
            malformed_rows=malformed_rows,
            duplicate_keys=duplicate_keys,
            conflicting_normalized_keys=len(conflicts),
            out_of_range_scores=out_of_range,
            warnings=warnings,
            loaded_at_utc=current_utc_timestamp(),
        )
        return VadLexicon.create(self.metadata, entries, validation)


class NrcVadV1Adapter(_NrcVadAdapter):
    configuration = _NrcVadConfiguration(
        lexicon_id="nrc_vad_v1",
        display_name="NRC VAD Lexicon v1",
        version="1 (July 2018)",
        source_minimum=0.0,
        source_maximum=1.0,
        normalization_formula="normalized = original (identity)",
        has_header=False,
        phrase_support=True,
        citation=(
            "Mohammad, S. M. (2018). Obtaining Reliable Human Ratings of "
            "Valence, Arousal, and Dominance for 20,000 English Words. ACL 2018."
        ),
        unit_of_analysis=(
            "English words plus source-supplied whitespace-containing entries "
            "available as exact phrase candidates"
        ),
    )


class NrcVadV21Adapter(_NrcVadAdapter):
    configuration = _NrcVadConfiguration(
        lexicon_id="nrc_vad_v2_1",
        display_name="NRC VAD Lexicon v2.1",
        version="2.1 (March 2025)",
        source_minimum=-1.0,
        source_maximum=1.0,
        normalization_formula="normalized = (original + 1) / 2",
        has_header=True,
        phrase_support=True,
        citation=(
            "Mohammad, S. M. (2025). NRC VAD Lexicon v2: Norms for Valence, "
            "Arousal, and Dominance for over 55k English Terms. arXiv:2503.23547; "
            "and Mohammad (2018), ACL 2018."
        ),
        unit_of_analysis="English unigrams and multiword expressions",
    )
