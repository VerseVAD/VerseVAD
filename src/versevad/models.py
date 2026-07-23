"""Core immutable data models for the VerseVAD analysis engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


DIMENSIONS = ("valence", "arousal", "dominance")


class LexiconValueKind(StrEnum):
    VAD = "vad"
    CATEGORICAL_ASSOCIATION = "categorical_association"
    EMOTION_INTENSITY = "emotion_intensity"


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
    value_kind: LexiconValueKind = LexiconValueKind.VAD
    dimensions: tuple[str, ...] = DIMENSIONS
    source_format: str = ""
    encoding: str = "utf-8"
    case_behavior: str = "Unicode-normalized case-insensitive lookup"
    expected_duplicate_behavior: str = "Duplicate normalized keys are invalid"
    column_mapping: tuple[tuple[str, str], ...] = ()
    preprocessing_assumptions: str = ""


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
    loaded_at_utc: str = ""

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
    standard_deviation: VadScores | None = None
    rater_count: VadScores | None = None


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
class EmotionAssociationEntry:
    lexicon_id: str
    source_term: str
    lookup_form: str
    source_rows: tuple[int, ...]
    associations: tuple[str, ...]


@dataclass(frozen=True)
class EmotionAssociationLexicon:
    metadata: LexiconMetadata
    entries: Mapping[str, EmotionAssociationEntry]
    validation: LexiconValidation

    @classmethod
    def create(
        cls,
        metadata: LexiconMetadata,
        entries: Mapping[str, EmotionAssociationEntry],
        validation: LexiconValidation,
    ) -> "EmotionAssociationLexicon":
        return cls(metadata, MappingProxyType(dict(entries)), validation)

    def resolve(
        self, normalized_form: str, observed_form: str
    ) -> tuple[EmotionAssociationEntry | None, bool]:
        del observed_form
        return self.entries.get(normalized_form), False


@dataclass(frozen=True)
class EmotionIntensityEntry:
    lexicon_id: str
    source_term: str
    lookup_form: str
    source_rows: tuple[int, ...]
    intensities: tuple[tuple[str, float], ...]

    def intensity_map(self) -> Mapping[str, float]:
        return MappingProxyType(dict(self.intensities))


@dataclass(frozen=True)
class EmotionIntensityLexicon:
    metadata: LexiconMetadata
    entries: Mapping[str, EmotionIntensityEntry]
    validation: LexiconValidation

    @classmethod
    def create(
        cls,
        metadata: LexiconMetadata,
        entries: Mapping[str, EmotionIntensityEntry],
        validation: LexiconValidation,
    ) -> "EmotionIntensityLexicon":
        return cls(metadata, MappingProxyType(dict(entries)), validation)

    def resolve(
        self, normalized_form: str, observed_form: str
    ) -> tuple[EmotionIntensityEntry | None, bool]:
        del observed_form
        return self.entries.get(normalized_form), False


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
    PHRASE = "exact_phrase"
    LEMMA = "pos_sensitive_lemma"
    USER_MAPPING = "approved_user_mapping"
    UNMATCHED = "unmatched"
    NOT_ELIGIBLE = "not_eligible"


class PhrasePolicy(StrEnum):
    PHRASE_PREFERRED = "phrase_preferred"
    UNIGRAM_ONLY = "unigram_only"
    PHRASE_AND_COMPONENT = "phrase_and_component_exploratory"


class StopwordMode(StrEnum):
    """Policy used only for the secondary stopword-sensitivity view."""

    ALL_MATCHED = "all_matched"
    STANDARD = "standard"
    CUSTOM = "custom"


@dataclass(frozen=True)
class StopwordPolicy:
    mode: StopwordMode
    source: str
    library_version: str
    list_version: str
    standard_word_count: int
    standard_list_sha256: str
    active_words: tuple[str, ...]
    active_list_sha256: str
    protected_words: tuple[str, ...]
    custom_additions: tuple[str, ...]
    custom_removals: tuple[str, ...]


class MatchSelection(StrEnum):
    INCLUDED = "included"
    UNMATCHED = "unmatched"
    NOT_ELIGIBLE = "not_eligible"
    SUPPRESSED_COMPONENT = "suppressed_component"
    SUPPRESSED_OVERLAP = "suppressed_overlap"
    EXCLUDED_REVIEW = "excluded_by_review"


class ReviewAction(StrEnum):
    """Effect of one explicit scholarly review decision."""

    FLAG = "flag"
    EXCLUDE = "exclude"
    MAP = "map"


class ReviewScope(StrEnum):
    """Where a review decision is eligible to apply."""

    OCCURRENCE = "occurrence"
    WORK = "work"
    PROJECT = "project"
    GLOBAL = "global"


@dataclass(frozen=True)
class ReviewRule:
    """One immutable, versioned rule supplied by a named review scenario."""

    decision_id: str
    decision_revision_id: str
    action: ReviewAction
    scope: ReviewScope
    lexicon_id: str
    source_form: str
    mapping_target: str = ""
    project_id: str = ""
    text_id: str = ""
    text_version_id: str = ""
    token_position: int | None = None
    risk_category: str = ""
    rationale: str = ""


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
class StopwordCoverageStatistics:
    """Coverage for the secondary view with an explicitly adjusted denominator."""

    eligible_token_count: int
    eligible_unique_type_count: int
    matched_token_count: int
    unmatched_token_count: int
    matched_type_count: int
    unmatched_type_count: int
    lexical_token_coverage: float | None
    type_coverage: float | None
    excluded_matched_observation_count: int
    excluded_matched_token_count: int
    excluded_matched_type_count: int


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
    stopword_excluded_token_weighted_original: WeightedVadStatistics | None = None
    stopword_excluded_type_weighted_original: WeightedVadStatistics | None = None
    stopword_excluded_token_weighted_normalized: WeightedVadStatistics | None = None
    stopword_excluded_type_weighted_normalized: WeightedVadStatistics | None = None
    stopword_excluded_is_sparse: bool | None = None


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


@dataclass(frozen=True)
class AffectMatchRecord:
    match_id: str
    lexicon_id: str
    token_ids: tuple[str, ...]
    start_token_position: int
    end_token_position: int
    line_number: int
    stanza_number: int
    method: MatchMethod
    selection: MatchSelection
    matched_term: str | None
    matched_lookup_form: str | None
    source_rows: tuple[int, ...]
    original_scores: VadScores | None
    normalized_scores: VadScores | None
    associations: tuple[str, ...]
    intensities: tuple[tuple[str, float], ...]
    included: bool
    suppressed_by_match_id: str | None
    reason: str
    stopword_status: str = "not a stopword"
    included_in_stopword_view: bool = False
    stopword_exclusion_reason: str = ""

    def intensity_map(self) -> Mapping[str, float]:
        return MappingProxyType(dict(self.intensities))


@dataclass(frozen=True)
class TermContribution:
    term: str
    token_count: int
    source_value: float | None = None


@dataclass(frozen=True)
class EmotionCategoryStatistics:
    category: str
    associated_token_count: int
    associated_unique_type_count: int
    proportion_of_lexical_tokens: float | None
    proportion_of_matched_emotion_bearing_tokens: float | None
    proportion_of_unique_lexical_types: float | None
    line_distribution: tuple[tuple[int, int], ...]
    stanza_distribution: tuple[tuple[int, int], ...]
    top_contributing_terms: tuple[TermContribution, ...]


@dataclass(frozen=True)
class EmotionIntensityStatistics:
    category: str
    matched_word_emotion_pairs: int
    matched_token_occurrences: int
    prevalence_among_lexical_tokens: float | None
    prevalence_among_emotion_intensity_matches: float | None
    token_weighted: DescriptiveStatistics
    type_weighted: DescriptiveStatistics
    line_distribution: tuple[tuple[int, int], ...]
    stanza_distribution: tuple[tuple[int, int], ...]
    top_contributing_terms: tuple[TermContribution, ...]


@dataclass(frozen=True)
class Phase2AnalysisResult:
    analysis_id: str
    scenario_id: str
    phrase_policy: PhrasePolicy
    document: TextDocument
    lexicon_metadata: LexiconMetadata
    lexicon_validation: LexiconValidation
    preprocessing: PreprocessingMetadata
    tokens: tuple[TokenRecord, ...]
    matches: tuple[AffectMatchRecord, ...]
    coverage: CoverageStatistics
    vad_summary: VadSummary | None
    category_statistics: tuple[EmotionCategoryStatistics, ...]
    intensity_statistics: tuple[EmotionIntensityStatistics, ...]
    warnings: tuple[str, ...]
    stopword_policy: StopwordPolicy | None = None
    stopword_coverage: StopwordCoverageStatistics | None = None
    scenario_version_id: str = ""
    review_rules: tuple[ReviewRule, ...] = ()


@dataclass(frozen=True)
class ComparisonMetric:
    lexicon_id: str
    display_name: str
    family: str
    version: str
    value_kind: LexiconValueKind
    metric: str
    weighting: str
    scale: str
    denominator: str
    value: float | int | None
    analysis_view: str = "all_matched"


@dataclass(frozen=True)
class CrossLexiconComparison:
    comparison_id: str
    text_version_id: str
    scenario_id: str
    phrase_policy: PhrasePolicy
    lexicon_ids: tuple[str, ...]
    metrics: tuple[ComparisonMetric, ...]
    consensus_score: None = None
