"""Invented Phase 1 materials with hand-calculated expected results."""

from __future__ import annotations

import hashlib
import math

from versevad.models import (
    AnalysisResult,
    LexiconMetadata,
    LexiconValidation,
    VadEntry,
    VadLexicon,
    VadScores,
)
from versevad.normalization import normalize_lookup


PHASE1_DEMO_TEXT = """Bright stone, bright stone.
Mountains cried.

Broken arms rest.
"""

_SYNTHETIC_VALUES = (
    ("bright", 8.0, 6.0, 7.0),
    ("stone", 3.0, 4.0, 5.0),
    ("mountain", 6.0, 5.0, 7.0),
    ("cry", 2.0, 7.0, 3.0),
    ("broken", 1.0, 8.0, 2.0),
    ("break", 4.0, 6.0, 5.0),
)


def phase1_synthetic_lexicon() -> VadLexicon:
    """Return invented ratings; no supplied source lexicon data are copied."""

    metadata = LexiconMetadata(
        lexicon_id="synthetic_vad_phase1",
        display_name="VerseVAD Phase 1 synthetic VAD fixture",
        family="VerseVAD validation fixtures",
        version="1",
        language="English",
        unit_of_analysis="invented words",
        source_scale_min=1.0,
        source_scale_max=9.0,
        normalization_formula="normalized = (original - 1) / 8",
        adapter_version="synthetic-1",
        citation="Invented VerseVAD validation data; no external citation required.",
        license_notice="Invented public-domain validation data.",
        phrase_support=False,
    )
    entries = {}
    canonical_lines = []
    for source_row, (term, valence, arousal, dominance) in enumerate(
        _SYNTHETIC_VALUES, start=1
    ):
        original = VadScores(valence, arousal, dominance)
        normalized = VadScores(
            (valence - 1.0) / 8.0,
            (arousal - 1.0) / 8.0,
            (dominance - 1.0) / 8.0,
        )
        lookup_form = normalize_lookup(term)
        entries[lookup_form] = VadEntry(
            lexicon_id=metadata.lexicon_id,
            source_term=term,
            lookup_form=lookup_form,
            source_row=source_row,
            original=original,
            normalized=normalized,
        )
        canonical_lines.append(f"{term}\t{valence}\t{arousal}\t{dominance}")
    source_hash = hashlib.sha256("\n".join(canonical_lines).encode("utf-8")).hexdigest()
    validation = LexiconValidation(
        source_path=None,
        source_sha256=source_hash,
        total_rows=len(entries),
        usable_entries=len(entries),
        phrase_entries=0,
        blank_terms=0,
        malformed_rows=0,
        duplicate_keys=0,
        conflicting_normalized_keys=0,
        out_of_range_scores=0,
    )
    return VadLexicon.create(metadata, entries, validation)


def validate_phase1_demo(result: AnalysisResult) -> tuple[str, ...]:
    """Compare engine output with the hand-calculated demonstration worksheet."""

    problems: list[str] = []
    expected_counts = {
        "total_lexical_tokens": 9,
        "matched_token_count": 7,
        "unmatched_token_count": 2,
        "total_unique_types": 7,
        "matched_type_count": 5,
        "exact_match_count": 5,
        "lemma_fallback_count": 2,
    }
    for field, expected in expected_counts.items():
        actual = getattr(result.coverage, field)
        if actual != expected:
            problems.append(f"{field}: expected {expected}, found {actual}")

    expected_means = {
        "token valence": (result.vad_summary.token_weighted_original.valence.mean, 31 / 7),
        "token arousal": (result.vad_summary.token_weighted_original.arousal.mean, 40 / 7),
        "token dominance": (
            result.vad_summary.token_weighted_original.dominance.mean,
            36 / 7,
        ),
        "type valence": (result.vad_summary.type_weighted_original.valence.mean, 4.0),
        "type arousal": (result.vad_summary.type_weighted_original.arousal.mean, 6.0),
        "type dominance": (
            result.vad_summary.type_weighted_original.dominance.mean,
            4.8,
        ),
    }
    for label, (actual, expected) in expected_means.items():
        if actual is None or not math.isclose(actual, expected, rel_tol=1e-12):
            problems.append(f"{label}: expected {expected}, found {actual}")
    return tuple(problems)
