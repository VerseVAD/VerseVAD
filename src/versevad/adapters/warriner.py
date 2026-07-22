"""Read-only adapter for the supplied Warriner et al. VAD CSV file."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from versevad.adapters.base import LexiconAdapterError
from versevad.models import (
    LexiconMetadata,
    LexiconValidation,
    VadEntry,
    VadLexicon,
    VadScores,
)
from versevad.normalization import normalize_lookup


class WarrinerVadAdapter:
    adapter_version = "0.1.0"
    required_columns = ("Word", "V.Mean.Sum", "A.Mean.Sum", "D.Mean.Sum")

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _normalize_score(value: float) -> float:
        return (value - 1.0) / 8.0

    @property
    def metadata(self) -> LexiconMetadata:
        return LexiconMetadata(
            lexicon_id="warriner_vad_2013",
            display_name="Warriner et al. VAD ratings",
            family="Warriner affective norms",
            version="2013 (local XANEW package has no version tag)",
            language="English",
            unit_of_analysis=(
                "Source-described lemmas; whitespace-containing entries are retained"
            ),
            source_scale_min=1.0,
            source_scale_max=9.0,
            normalization_formula="normalized = (original - 1) / 8",
            adapter_version=self.adapter_version,
            citation=(
                "Warriner, A. B., Kuperman, V., & Brysbaert, M. (2013). "
                "Norms of valence, arousal, and dominance for 13,915 English "
                "lemmas. Behavior Research Methods, 45, 1191-1207."
            ),
            license_notice=(
                "The supplied secondary package states CC BY-NC-ND 3.0. "
                "Keep the source file private and do not redistribute it."
            ),
            phrase_support=False,
        )

    def load(self, source_path: Path) -> VadLexicon:
        source_path = Path(source_path)
        if not source_path.is_file():
            raise LexiconAdapterError(
                "VerseVAD could not find the Warriner source file. No data were "
                "changed. Restore the original file or select its location.",
                technical_detail=f"Missing path: {source_path}",
            )

        source_hash = self._sha256(source_path)
        entries: dict[str, VadEntry] = {}
        conflicting_entries: dict[str, tuple[VadEntry, ...]] = {}
        errors: list[str] = []
        warnings: list[str] = []
        total_rows = 0
        blank_terms = 0
        malformed_rows = 0
        duplicate_keys = 0
        out_of_range_scores = 0
        phrase_entries = 0

        try:
            source_path.read_bytes().decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise LexiconAdapterError(
                "VerseVAD could not read the Warriner file as UTF-8. No source "
                "file was changed.",
                technical_detail=str(error),
            ) from error

        source = source_path.open("r", encoding="utf-8-sig", newline="")
        with source:
            reader = csv.DictReader(source)
            fields = tuple(reader.fieldnames or ())
            missing = [column for column in self.required_columns if column not in fields]
            if missing:
                expected = ", ".join(self.required_columns)
                found = ", ".join(fields) if fields else "no header"
                raise LexiconAdapterError(
                    "VerseVAD could not find the expected columns in the Warriner "
                    "file. No source file was changed.",
                    technical_detail=(
                        f"Missing columns: {missing}. Expected: {expected}. Found: {found}."
                    ),
                )

            for source_row, row in enumerate(reader, start=2):
                total_rows += 1
                term = (row.get("Word") or "").strip()
                if not term:
                    blank_terms += 1
                    continue
                if any(character.isspace() for character in term):
                    phrase_entries += 1
                lookup_form = normalize_lookup(term)
                try:
                    original = VadScores(
                        valence=float(row["V.Mean.Sum"]),
                        arousal=float(row["A.Mean.Sum"]),
                        dominance=float(row["D.Mean.Sum"]),
                    )
                except (KeyError, TypeError, ValueError):
                    malformed_rows += 1
                    continue

                if any(not 1.0 <= value <= 9.0 for value in original.as_dict().values()):
                    out_of_range_scores += 1
                    continue

                normalized = VadScores(
                    valence=self._normalize_score(original.valence),
                    arousal=self._normalize_score(original.arousal),
                    dominance=self._normalize_score(original.dominance),
                )
                new_entry = VadEntry(
                    lexicon_id=self.metadata.lexicon_id,
                    source_term=term,
                    lookup_form=lookup_form,
                    source_row=source_row,
                    original=original,
                    normalized=normalized,
                )
                if lookup_form in entries:
                    existing = entries.pop(lookup_form)
                    if existing.source_term == term:
                        duplicate_keys += 1
                        entries[lookup_form] = existing
                        continue
                    conflicting_entries[lookup_form] = (existing, new_entry)
                elif lookup_form in conflicting_entries:
                    group = conflicting_entries[lookup_form]
                    if any(existing.source_term == term for existing in group):
                        duplicate_keys += 1
                        continue
                    conflicting_entries[lookup_form] = (*group, new_entry)
                else:
                    entries[lookup_form] = new_entry

        if blank_terms:
            errors.append(f"Found {blank_terms} blank terms.")
        if malformed_rows:
            errors.append(f"Found {malformed_rows} rows with malformed scores.")
        if duplicate_keys:
            errors.append(f"Found {duplicate_keys} duplicate normalized terms.")
        if out_of_range_scores:
            errors.append(f"Found {out_of_range_scores} rows outside the 1-9 scale.")
        if phrase_entries:
            warnings.append(
                f"Retained {phrase_entries} whitespace-containing entries. Phase 1 "
                "does not yet perform phrase matching, so they cannot contribute to "
                "the current token-level summaries."
            )
        if conflicting_entries:
            warnings.append(
                f"Preserved {len(conflicting_entries)} case-insensitive lookup "
                "collisions. Exact source capitalization may resolve them; otherwise "
                "VerseVAD leaves the token unmatched for review."
            )

        validation = LexiconValidation(
            source_path=source_path.resolve(),
            source_sha256=source_hash,
            total_rows=total_rows,
            usable_entries=(
                len(entries) + sum(len(group) for group in conflicting_entries.values())
            ),
            phrase_entries=phrase_entries,
            blank_terms=blank_terms,
            malformed_rows=malformed_rows,
            duplicate_keys=duplicate_keys,
            conflicting_normalized_keys=len(conflicting_entries),
            out_of_range_scores=out_of_range_scores,
            errors=tuple(errors),
            warnings=tuple(warnings),
        )
        if errors:
            raise LexiconAdapterError(
                "VerseVAD found structural problems in the Warriner source file and "
                "stopped before analysis. No source file was changed.",
                technical_detail=" ".join(errors),
            )
        return VadLexicon.create(
            self.metadata,
            entries,
            validation,
            conflicting_entries=conflicting_entries,
        )
