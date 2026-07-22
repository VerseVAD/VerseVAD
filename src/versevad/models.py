"""Core immutable data models for the VerseVAD analysis engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


DIMENSIONS = ("valence", "arousal", "dominance")


@dataclass(frozen=True)
class VadScores:
    """Valence, arousal, and dominance scores on a declared scale."""

    valence: float
    arousal: float
    dominance: float

    def as_dict(self) -> dict[str, float]:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
        }


@dataclass(frozen=True)
class LexiconMetadata:
    lexicon_id: str
    display_name: str
    family: str
    version: str
    language: str
    unit_of_analysis: str
    source_scale_min: float
    source_scale_max: float
    normalization_formula: str
    adapter_version: str
    citation: str
    license_notice: str
    phrase_support: bool


@dataclass(frozen=True)
class LexiconValidation:
    source_path: Path | None
    source_sha256: str
    total_rows: int
    usable_entries: int
    phrase_entries: int
    blank_terms: int
    malformed_rows: int
    duplicate_keys: int
    conflicting_normalized_keys: int
    out_of_range_scores: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class VadEntry:
    lexicon_id: str
    source_term: str
    lookup_form: str
    source_row: int
    original: VadScores
    normalized: VadScores


@dataclass(frozen=True)
class VadLexicon:
    metadata: LexiconMetadata
    entries: Mapping[str, VadEntry]
    conflicting_entries: Mapping[str, tuple[VadEntry, ...]]
    validation: LexiconValidation

    @classmethod
    def create(
        cls,
        metadata: LexiconMetadata,
        entries: Mapping[str, VadEntry],
        validation: LexiconValidation,
        conflicting_entries: Mapping[str, tuple[VadEntry, ...]] | None = None,
    ) -> "VadLexicon":
        return cls(
            metadata=metadata,
            entries=MappingProxyType(dict(entries)),
            conflicting_entries=MappingProxyType(dict(conflicting_entries or {})),
            validation=validation,
        )

    def lookup(self, normalized_form: str) -> VadEntry | None:
        return self.entries.get(normalized_form)

    def resolve(
        self, normalized_form: str, observed_form: str
    ) -> tuple[VadEntry | None, bool]:
        """Resolve a key, preserving case-colliding source entries.

        Returns ``(entry, unresolved_conflict)``. A source-form match may
        disambiguate entries whose case-folded keys collide. No arbitrary
        candidate is selected when capitalization does not resolve the group.
        """

        entry = self.entries.get(normalized_form)
        if entry is not None:
            return entry, False
        candidates = self.conflicting_entries.get(normalized_form, ())
        exact_source = [item for item in candidates if item.source_term == observed_form]
        if len(exact_source) == 1:
            return exact_source[0], False
        return None, bool(candidates)


@dataclass(frozen=True)
class TextDocument:
    text_id: str
    title: str
    original_text: str
    text_sha256: str
    text_version_id: str


@dataclass(frozen=True)
class TokenRecord:
    token_id: str
    text_id: str
    text_version_id: str
    section_number: int
    stanza_number: int
    line_number: int
    token_position: int
    sentence_number: int | None
    token_position_in_sentence: int | None
    character_start: int
    character_end: int
    surface_form: str
    lowercase_form: str
    punctuation_stripped_form: str
    normalized_form: str
    part_of_speech: str
    lemma: str
    normalized_lemma: str
    morphological_features: str
    is_punctuation: bool
    is_numeric: bool
    is_proper_noun: bool
    is_stopword: bool
    context: str
    preprocessing_warnings: tuple[str, ...] = ()

    @property
    def is_lexical(self) -> bool:
        return not self.is_punctuation and not self.is_numeric


class MatchMethod(StrEnum):
    EXACT = "exact"
    POSSESSIVE = "possessive_normalization"
    LEMMA = "pos_sensitive_lemma"
    UNMATCHED = "unmatched"
    NOT_ELIGIBLE = "not_eligible"


@dataclass(frozen=True)
class TokenMatch:
    token_id: str
    lexicon_id: str
    method: MatchMethod
    matched_term: str | None
    matched_lookup_form: str | None
    source_row: int | None
    original_scores: VadScores | None
    normalized_scores: VadScores | None
    included: bool
    reason: str


@dataclass(frozen=True)
class CoverageStatistics:
    total_tokens: int
    total_lexical_tokens: int
    total_unique_types: int
    matched_token_count: int
    unmatched_token_count: int
    matched_type_count: int
    unmatched_type_count: int
    token_coverage: float | None
    lexical_token_coverage: float | None
    type_coverage: float | None
    exact_match_count: int
    exact_match_coverage: float | None
    possessive_match_count: int
    possessive_match_coverage: float | None
    lemma_fallback_count: int
    lemma_fallback_coverage: float | None
    phrase_match_count: int
    phrase_match_coverage: float | None
    approved_mapping_count: int
    approved_mapping_coverage: float | None
    compound_derived_count: int
    compound_derived_coverage: float | None
    excluded_token_count: int
    excluded_token_rate: float | None


@dataclass(frozen=True)
class DescriptiveStatistics:
    count: int
    mean: float | None
    median: float | None
    population_standard_deviation: float | None
    minimum: float | None
    first_quartile: float | None
    third_quartile: float | None
    maximum: float | None


@dataclass(frozen=True)
class WeightedVadStatistics:
    valence: DescriptiveStatistics
    arousal: DescriptiveStatistics
    dominance: DescriptiveStatistics

    def by_dimension(self) -> dict[str, DescriptiveStatistics]:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "dominance": self.dominance,
        }


@dataclass(frozen=True)
class VadSummary:
    token_weighted_original: WeightedVadStatistics
    type_weighted_original: WeightedVadStatistics
    token_weighted_normalized: WeightedVadStatistics
    type_weighted_normalized: WeightedVadStatistics
    minimum_match_requirement: int
    is_sparse: bool


@dataclass(frozen=True)
class PreprocessingMetadata:
    recipe_id: str
    pipeline_name: str
    pipeline_version: str
    disabled_components: tuple[str, ...]


@dataclass(frozen=True)
class AnalysisResult:
    analysis_id: str
    scenario_id: str
    document: TextDocument
    lexicon_metadata: LexiconMetadata
    lexicon_validation: LexiconValidation
    preprocessing: PreprocessingMetadata
    tokens: tuple[TokenRecord, ...]
    matches: tuple[TokenMatch, ...]
    coverage: CoverageStatistics
    vad_summary: VadSummary
    warnings: tuple[str, ...]

    def match_map(self) -> Mapping[str, TokenMatch]:
        return MappingProxyType({match.token_id: match for match in self.matches})
