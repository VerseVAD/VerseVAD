"""Transparent candidate-meter estimation from Stage 5 stress evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from enum import StrEnum
from functools import lru_cache
from itertools import product
from statistics import fmean, median, pstdev
from typing import TYPE_CHECKING, Iterable

from versevad import __version__
from versevad.core.modules import (
    ModuleCoverage,
    ModuleInput,
    ModuleMetric,
    ModuleProvenance,
    ModuleResult,
    ModuleWarning,
    ResultLayer,
    WarningSeverity,
)
from versevad.core.resources import ResourceStatus
from versevad.prosody.pronunciation import (
    PronunciationAnalysisResult,
    PronunciationStatus,
    PronunciationTokenResult,
)

if TYPE_CHECKING:
    from versevad.prosody.performance_meter import PerformanceAwareMeterResult


class MeterModuleError(RuntimeError):
    """Plain-language failure raised before a partial meter result is published."""


class FootPattern(StrEnum):
    IAMBIC = "iambic"
    TROCHAIC = "trochaic"
    ANAPESTIC = "anapestic"
    DACTYLIC = "dactylic"
    AMPHIBRACHIC = "amphibrachic"
    SPONDAIC = "spondaic"
    PYRRHIC = "pyrrhic"


class MeterAnalysisMode(StrEnum):
    """Keep the validated candidate layer separate from optional realization."""

    CANDIDATE = "candidate_meter"
    PERFORMANCE_AWARE = "performance_aware"
    COMPARE_BOTH = "compare_both"


class MeterStyleProfile(StrEnum):
    """Broad, declared interpretation profiles; never inferred as literary period."""

    GENERAL = "general_english_verse"
    TRADITIONAL = "traditional_accentual_syllabic"
    ROMANTIC_VICTORIAN = "romantic_victorian"
    MODERNIST = "modernist"
    CONTEMPORARY_FORMAL = "contemporary_formal"
    FREE_VERSE_CADENTIAL = "free_verse_cadential"
    CUSTOM = "custom"


class MeterInterpretationDepth(StrEnum):
    SUMMARY = "summary"
    STANDARD = "standard"
    DETAILED = "detailed"


@dataclass(frozen=True)
class MeterScholarRevision:
    """A separate scholar-supplied reading; never an edited automatic result."""

    line_number: int
    pattern: FootPattern
    foot_count: int
    realized_scansion: str
    note: str

    def __post_init__(self) -> None:
        if self.line_number < 1:
            raise ValueError("A meter revision line number must be positive.")
        if self.pattern not in PRIMARY_FOOT_PATTERNS:
            raise ValueError(
                "A meter revision must use one of the five base patterns."
            )
        if self.foot_count not in FOOT_COUNT_NAMES:
            raise ValueError(
                "A meter revision foot count must be one through eight."
            )
        if not self.realized_scansion.strip():
            raise ValueError("A meter revision requires visible scansion.")
        if not self.note.strip():
            raise ValueError("A meter revision requires a scholarly note.")

    @property
    def candidate_label(self) -> str:
        return (
            f"{self.pattern.value.capitalize()} "
            f"{FOOT_COUNT_NAMES[self.foot_count]}"
        )


PRIMARY_FOOT_PATTERNS: tuple[FootPattern, ...] = (
    FootPattern.IAMBIC,
    FootPattern.TROCHAIC,
    FootPattern.ANAPESTIC,
    FootPattern.DACTYLIC,
    FootPattern.AMPHIBRACHIC,
)

FOOT_STRESS_PATTERNS: dict[FootPattern, str] = {
    FootPattern.IAMBIC: "01",
    FootPattern.TROCHAIC: "10",
    FootPattern.ANAPESTIC: "001",
    FootPattern.DACTYLIC: "100",
    FootPattern.AMPHIBRACHIC: "010",
    FootPattern.SPONDAIC: "11",
    FootPattern.PYRRHIC: "00",
}

FOOT_COUNT_NAMES: dict[int, str] = {
    1: "monometer",
    2: "dimeter",
    3: "trimeter",
    4: "tetrameter",
    5: "pentameter",
    6: "hexameter",
    7: "heptameter",
    8: "octameter",
}

FUNCTION_WORD_POS = frozenset(
    {"ADP", "AUX", "CCONJ", "DET", "PART", "PRON", "SCONJ"}
)

_PATTERN_ORDER = {
    pattern: index for index, pattern in enumerate(PRIMARY_FOOT_PATTERNS)
}


def parse_meter_scholar_revisions(
    text: str,
) -> tuple[MeterScholarRevision, ...]:
    """Parse `line = pattern foot-name | scansion | note` records."""

    revisions = []
    foot_counts = {
        name.casefold(): count for count, name in FOOT_COUNT_NAMES.items()
    }
    patterns = {pattern.value: pattern for pattern in PRIMARY_FOOT_PATTERNS}
    for source_line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            assignment, scansion, note = (
                part.strip() for part in line.split("|", maxsplit=2)
            )
            line_label, candidate = (
                part.strip() for part in assignment.split("=", maxsplit=1)
            )
            normalized_line = line_label.casefold().removeprefix("line").strip()
            line_number = int(normalized_line)
            pattern_label, foot_label = candidate.casefold().split(
                maxsplit=1
            )
            pattern = patterns[pattern_label]
            foot_count = (
                int(foot_label)
                if foot_label.isdigit()
                else foot_counts[foot_label]
            )
            revisions.append(
                MeterScholarRevision(
                    line_number=line_number,
                    pattern=pattern,
                    foot_count=foot_count,
                    realized_scansion=scansion,
                    note=note,
                )
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "Meter revision line "
                f"{source_line_number} must use: "
                "`line 2 = iambic pentameter | x / x / x / x / x / | "
                "scholarly note`."
            ) from error
    line_numbers = [item.line_number for item in revisions]
    if len(line_numbers) != len(set(line_numbers)):
        raise ValueError("Only one meter revision may be supplied per line.")
    return tuple(revisions)


@dataclass(frozen=True)
class MeterConfiguration:
    """Auditable penalties and thresholds used by the candidate estimator."""

    minimum_foot_count: int = 1
    maximum_foot_count: int = 8
    primary_stress_in_weak_cost: float = 1.0
    secondary_stress_in_weak_cost: float = 0.45
    secondary_stress_in_strong_cost: float = 0.10
    unstressed_content_in_strong_cost: float = 0.75
    unstressed_function_in_strong_cost: float = 0.25
    extra_syllable_cost: float = 0.80
    omitted_syllable_cost: float = 0.80
    feminine_ending_cost: float = 0.20
    catalectic_ending_cost: float = 0.25
    initial_inversion_cost: float = 0.25
    line_match_threshold: float = 0.75
    irregular_fit_threshold: float = 0.65
    ambiguity_margin_threshold: float = 0.03
    stable_foot_count_threshold: float = 0.60
    low_line_coverage_warning_threshold: float = 0.70
    minimum_analyzable_lines: int = 2
    maximum_line_variants: int = 256
    retained_alternative_candidates: int = 4
    analysis_mode: MeterAnalysisMode = MeterAnalysisMode.CANDIDATE
    style_profile: MeterStyleProfile = MeterStyleProfile.GENERAL
    interpretation_depth: MeterInterpretationDepth = (
        MeterInterpretationDepth.STANDARD
    )
    performance_candidate_limit: int = 8
    retained_realized_alternatives: int = 2
    allow_visible_poetic_elision: bool = False
    scholar_revisions: tuple[MeterScholarRevision, ...] = ()
    contextual_fit_weight: float = 0.24
    phrase_fit_weight: float = 0.08
    poem_consistency_weight: float = 0.10
    stanza_consistency_weight: float = 0.05
    style_compatibility_weight: float = 0.08
    scenario_id: str = "candidate-meter-alignment-v1"

    def __post_init__(self) -> None:
        if (
            self.analysis_mode is not MeterAnalysisMode.CANDIDATE
            and self.scenario_id == "candidate-meter-alignment-v1"
        ):
            object.__setattr__(
                self,
                "scenario_id",
                "performance-aware-meter-realization-v1",
            )
        if self.minimum_foot_count < 1:
            raise ValueError("The minimum foot count must be at least one.")
        if self.maximum_foot_count > 8:
            raise ValueError("Stage 6 supports at most eight feet per line.")
        if self.minimum_foot_count > self.maximum_foot_count:
            raise ValueError("The minimum foot count cannot exceed the maximum.")
        penalties = {
            "primary stress in weak position": self.primary_stress_in_weak_cost,
            "secondary stress in weak position": self.secondary_stress_in_weak_cost,
            "secondary stress in strong position": self.secondary_stress_in_strong_cost,
            "unstressed content syllable in strong position": (
                self.unstressed_content_in_strong_cost
            ),
            "unstressed function syllable in strong position": (
                self.unstressed_function_in_strong_cost
            ),
            "extra syllable": self.extra_syllable_cost,
            "omitted syllable": self.omitted_syllable_cost,
            "feminine ending": self.feminine_ending_cost,
            "catalectic ending": self.catalectic_ending_cost,
            "initial inversion": self.initial_inversion_cost,
        }
        negative = [label for label, value in penalties.items() if value < 0]
        if negative:
            raise ValueError(
                "Meter-alignment costs cannot be negative: "
                + ", ".join(negative)
                + "."
            )
        thresholds = {
            "line match": self.line_match_threshold,
            "irregular fit": self.irregular_fit_threshold,
            "ambiguity margin": self.ambiguity_margin_threshold,
            "stable foot count": self.stable_foot_count_threshold,
            "low line coverage": self.low_line_coverage_warning_threshold,
        }
        outside = [
            label for label, value in thresholds.items() if not 0 <= value <= 1
        ]
        if outside:
            raise ValueError(
                "Meter thresholds must be between 0 and 1: "
                + ", ".join(outside)
                + "."
            )
        if self.minimum_analyzable_lines < 1:
            raise ValueError("At least one analyzable line must be required.")
        if self.maximum_line_variants < 1:
            raise ValueError("At least one stress variant per line must be allowed.")
        if self.retained_alternative_candidates < 1:
            raise ValueError("At least one alternative candidate must be retained.")
        if self.performance_candidate_limit < 2:
            raise ValueError(
                "Performance-aware meter requires at least two candidate paths."
            )
        if self.retained_realized_alternatives < 1:
            raise ValueError(
                "At least one alternate realized scansion must be retained."
            )
        revision_lines = [
            revision.line_number for revision in self.scholar_revisions
        ]
        if len(revision_lines) != len(set(revision_lines)):
            raise ValueError(
                "Only one scholar meter revision may be supplied per line."
            )
        realization_weights = {
            "contextual fit": self.contextual_fit_weight,
            "phrase fit": self.phrase_fit_weight,
            "poem consistency": self.poem_consistency_weight,
            "stanza consistency": self.stanza_consistency_weight,
            "style compatibility": self.style_compatibility_weight,
        }
        invalid_weights = [
            label
            for label, value in realization_weights.items()
            if not 0 <= value <= 1
        ]
        if invalid_weights:
            raise ValueError(
                "Performance-aware meter weights must be between zero and one: "
                + ", ".join(invalid_weights)
                + "."
            )
        if sum(realization_weights.values()) >= 0.85:
            raise ValueError(
                "Context, phrase, poem, stanza, and style weights must leave "
                "at least 0.15 for the preserved candidate evidence."
            )
        if not self.scenario_id.strip():
            raise ValueError("A meter scenario requires a stable ID.")

    @property
    def configuration_id(self) -> str:
        payload = json.dumps(
            asdict(self),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"meter-config-v2:{digest}"


@dataclass(frozen=True)
class MeterTemplate:
    pattern: FootPattern
    foot_pattern: str
    foot_count: int
    foot_count_name: str
    stress_template: str
    label: str


def candidate_templates(
    configuration: MeterConfiguration,
) -> tuple[MeterTemplate, ...]:
    """Return the fixed five-pattern by configured-foot-count candidate grid."""

    return _candidate_templates(
        configuration.minimum_foot_count,
        configuration.maximum_foot_count,
    )


@lru_cache(maxsize=16)
def _candidate_templates(
    minimum_foot_count: int,
    maximum_foot_count: int,
) -> tuple[MeterTemplate, ...]:
    return tuple(
        MeterTemplate(
            pattern=pattern,
            foot_pattern=FOOT_STRESS_PATTERNS[pattern],
            foot_count=foot_count,
            foot_count_name=FOOT_COUNT_NAMES[foot_count],
            stress_template=FOOT_STRESS_PATTERNS[pattern] * foot_count,
            label=(
                f"{pattern.value.capitalize()} {FOOT_COUNT_NAMES[foot_count]}"
            ),
        )
        for pattern in PRIMARY_FOOT_PATTERNS
        for foot_count in range(
            minimum_foot_count,
            maximum_foot_count + 1,
        )
    )


@dataclass(frozen=True)
class StressSyllable:
    stress_digit: str
    token_id: str
    surface_form: str
    part_of_speech: str
    word_index: int
    syllable_index_in_word: int

    def __post_init__(self) -> None:
        if self.stress_digit not in {"0", "1", "2"}:
            raise ValueError("Stress syllables must use CMUdict digits 0, 1, or 2.")
        if not self.token_id or not self.surface_form:
            raise ValueError("A stress syllable requires its source token and form.")
        if self.word_index < 0 or self.syllable_index_in_word < 0:
            raise ValueError("Stress-syllable positions cannot be negative.")

    @property
    def binary_stress(self) -> str:
        return "0" if self.stress_digit == "0" else "1"

    @property
    def is_function_word(self) -> bool:
        return self.part_of_speech in FUNCTION_WORD_POS


@dataclass(frozen=True)
class StressVariant:
    variant_id: str
    syllables: tuple[StressSyllable, ...]
    word_stress_sequence: str
    pronunciation_choices: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.variant_id:
            raise ValueError("A stress variant requires a stable ID.")
        if not self.syllables:
            raise ValueError("A stress variant requires at least one syllable.")

    @property
    def compact_stress_sequence(self) -> str:
        return "".join(item.stress_digit for item in self.syllables)


@dataclass(frozen=True)
class MeterLineInput:
    line_id: str
    line_number: int
    stanza_number: int
    source_text: str
    eligible_token_count: int
    supported_token_count: int
    missing_forms: tuple[str, ...]
    stress_variants: tuple[StressVariant, ...]
    variant_count_before_limit: int = 1
    variants_truncated: bool = False

    def __post_init__(self) -> None:
        if not self.line_id or self.line_number < 1:
            raise ValueError("Meter line evidence requires a valid physical line.")
        if (
            self.eligible_token_count < 0
            or self.supported_token_count < 0
            or self.supported_token_count > self.eligible_token_count
        ):
            raise ValueError("Meter line coverage counts are inconsistent.")
        if self.variant_count_before_limit < 0:
            raise ValueError("The stress-variant count cannot be negative.")


class AlignmentKind(StrEnum):
    MATCH = "match"
    SUBSTITUTION = "substitution"
    EXTRA_SYLLABLE = "extra_syllable"
    OMITTED_SYLLABLE = "omitted_syllable"
    SECONDARY_FLEXIBILITY = "secondary_stress_flexibility"


@dataclass(frozen=True)
class AlignmentOperation:
    kind: AlignmentKind
    observed_index: int | None
    template_index: int | None
    observed_stress: str | None
    template_stress: str | None
    cost: float
    token_id: str = ""
    surface_form: str = ""
    part_of_speech: str = ""
    feminine_ending: bool = False
    catalectic_ending: bool = False


@dataclass(frozen=True)
class CandidateMeterFit:
    pattern: FootPattern
    foot_pattern: str
    foot_count: int
    foot_count_name: str
    label: str
    base_template_stress: str
    evaluated_template_stress: str
    selected_variant_id: str
    selected_stress_sequence: str
    selected_word_stress_sequence: str
    selected_pronunciation_choices: tuple[str, ...]
    total_cost: float
    fit_score: float
    fit_label: str
    substitution_count: int
    extra_syllable_count: int
    omitted_syllable_count: int
    initial_inversion_count: int
    feminine_ending_count: int
    catalectic_count: int
    spondee_substitution_count: int
    pyrrhic_substitution_count: int
    aligned_observed: str
    aligned_template: str
    operations: tuple[AlignmentOperation, ...]


class MeterLineStatus(StrEnum):
    ANALYZED = "analyzed"
    NO_LEXICAL_TOKENS = "no_lexical_tokens"
    MISSING_PRONUNCIATION = "missing_pronunciation"
    TOO_MANY_VARIANTS = "too_many_pronunciation_variants"


@dataclass(frozen=True)
class MeterLineResult:
    line_id: str
    line_number: int
    stanza_number: int
    source_text: str
    status: MeterLineStatus
    eligible_token_count: int
    supported_token_count: int
    pronunciation_coverage: float | None
    missing_forms: tuple[str, ...]
    pronunciation_variant_count: int
    variants_truncated: bool
    closest_candidate: CandidateMeterFit | None
    alternative_candidates: tuple[CandidateMeterFit, ...]
    candidate_fits: tuple[CandidateMeterFit, ...]
    reason: str


@dataclass(frozen=True)
class MeterCandidateSummary:
    rank: int
    pattern: FootPattern
    foot_count: int
    foot_count_name: str
    label: str
    analyzed_line_count: int
    mean_fit: float | None
    median_fit: float | None
    fit_variability: float | None
    matching_line_count: int
    matching_line_proportion: float | None


class MeterAssessment(StrEnum):
    RECURRING_CANDIDATE = "recurring_candidate"
    MIXED_LINE_LENGTHS = "mixed_line_lengths"
    MIXED_OR_IRREGULAR = "mixed_or_irregular"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class MeterSummary:
    eligible_line_count: int
    analyzable_line_count: int
    unanalyzable_line_count: int
    line_coverage: float | None
    closest_candidate_kind: str
    closest_candidate_label: str
    closest_pattern: FootPattern | None
    closest_foot_count: int | None
    closest_foot_count_name: str
    alternative_candidate_label: str
    dominant_pattern: FootPattern | None
    dominant_pattern_mean_fit: float | None
    dominant_foot_count: int | None
    dominant_foot_count_name: str
    dominant_foot_count_share: float | None
    assessment: MeterAssessment
    candidate_confidence: str
    confidence_explanation: str
    whole_poem_mean_fit: float | None
    whole_poem_median_fit: float | None
    candidate_margin: float | None
    matching_line_count: int
    matching_line_proportion: float | None
    rhythmic_regularity: float | None
    rhythmic_variability: float | None
    substitution_count: int
    initial_inversion_count: int
    extra_syllable_count: int
    omitted_syllable_count: int
    feminine_ending_count: int
    catalectic_count: int
    spondee_substitution_count: int
    pyrrhic_substitution_count: int
    common_deviation: str
    pronunciation_alternative_line_count: int
    is_sparse: bool


@dataclass(frozen=True)
class MeterAnalysisResult:
    module_result: ModuleResult
    configuration: MeterConfiguration
    pronunciation_configuration_id: str
    line_results: tuple[MeterLineResult, ...]
    candidate_summaries: tuple[MeterCandidateSummary, ...]
    summary: MeterSummary
    performance_aware: PerformanceAwareMeterResult | None = None

    def __post_init__(self) -> None:
        analyzed = sum(
            item.status is MeterLineStatus.ANALYZED for item in self.line_results
        )
        if analyzed != self.summary.analyzable_line_count:
            raise ValueError(
                "Meter summary counts must agree with the line-level audit."
            )


@dataclass(frozen=True)
class _Alignment:
    cost: float
    operations: tuple[AlignmentOperation, ...]
    aligned_observed: str
    aligned_template: str


@dataclass(frozen=True)
class _AlignmentPlanOperation:
    kind: AlignmentKind
    observed_index: int | None
    template_index: int | None
    observed_stress: str | None
    template_stress: str | None
    cost: float
    feminine_ending: bool = False
    catalectic_ending: bool = False


@dataclass(frozen=True)
class _AlignmentPlan:
    cost: float
    operations: tuple[_AlignmentPlanOperation, ...]
    aligned_observed: str
    aligned_template: str


@dataclass(frozen=True)
class _AlignmentCostConfiguration:
    primary_stress_in_weak_cost: float
    secondary_stress_in_weak_cost: float
    secondary_stress_in_strong_cost: float
    unstressed_content_in_strong_cost: float
    unstressed_function_in_strong_cost: float
    extra_syllable_cost: float
    omitted_syllable_cost: float
    feminine_ending_cost: float
    catalectic_ending_cost: float


def _alignment_cost_configuration(
    configuration: MeterConfiguration,
) -> _AlignmentCostConfiguration:
    return _AlignmentCostConfiguration(
        primary_stress_in_weak_cost=(
            configuration.primary_stress_in_weak_cost
        ),
        secondary_stress_in_weak_cost=(
            configuration.secondary_stress_in_weak_cost
        ),
        secondary_stress_in_strong_cost=(
            configuration.secondary_stress_in_strong_cost
        ),
        unstressed_content_in_strong_cost=(
            configuration.unstressed_content_in_strong_cost
        ),
        unstressed_function_in_strong_cost=(
            configuration.unstressed_function_in_strong_cost
        ),
        extra_syllable_cost=configuration.extra_syllable_cost,
        omitted_syllable_cost=configuration.omitted_syllable_cost,
        feminine_ending_cost=configuration.feminine_ending_cost,
        catalectic_ending_cost=configuration.catalectic_ending_cost,
    )


def _fit_label(score: float) -> str:
    if score >= 0.90:
        return "Close candidate fit"
    if score >= 0.75:
        return "Plausible candidate fit"
    if score >= 0.60:
        return "Weak candidate fit"
    return "Poor candidate fit"


def _aligned_cost(
    syllable: StressSyllable,
    template_stress: str,
    configuration: MeterConfiguration,
) -> tuple[float, AlignmentKind]:
    return _aligned_cost_values(
        syllable.stress_digit,
        syllable.is_function_word,
        template_stress,
        configuration,
    )


def _aligned_cost_values(
    stress_digit: str,
    is_function_word: bool,
    template_stress: str,
    configuration: MeterConfiguration | _AlignmentCostConfiguration,
) -> tuple[float, AlignmentKind]:
    if template_stress == "0":
        if stress_digit == "0":
            return 0.0, AlignmentKind.MATCH
        if stress_digit == "2":
            return (
                configuration.secondary_stress_in_weak_cost,
                AlignmentKind.SUBSTITUTION,
            )
        return (
            configuration.primary_stress_in_weak_cost,
            AlignmentKind.SUBSTITUTION,
        )
    if stress_digit == "1":
        return 0.0, AlignmentKind.MATCH
    if stress_digit == "2":
        return (
            configuration.secondary_stress_in_strong_cost,
            AlignmentKind.SECONDARY_FLEXIBILITY,
        )
    return (
        (
            configuration.unstressed_function_in_strong_cost
            if is_function_word
            else configuration.unstressed_content_in_strong_cost
        ),
        AlignmentKind.SUBSTITUTION,
    )


@lru_cache(maxsize=16_384)
def _alignment_plan(
    syllable_signature: tuple[tuple[str, bool], ...],
    template: str,
    configuration: _AlignmentCostConfiguration,
) -> _AlignmentPlan:
    """Cache token-independent DP paths for refrains and repeated stress shapes."""

    n = len(syllable_signature)
    m = len(template)
    costs = [[float("inf")] * (m + 1) for _ in range(n + 1)]
    edits = [[10**9] * (m + 1) for _ in range(n + 1)]
    back: list[list[tuple[str, float, bool, bool] | None]] = [
        [None] * (m + 1) for _ in range(n + 1)
    ]
    costs[0][0] = 0.0
    edits[0][0] = 0

    for i in range(n + 1):
        for j in range(m + 1):
            if i == 0 and j == 0:
                continue
            options: list[
                tuple[float, int, int, str, float, bool, bool]
            ] = []
            if i and j:
                stress_digit, is_function_word = syllable_signature[i - 1]
                operation_cost, kind = _aligned_cost_values(
                    stress_digit,
                    is_function_word,
                    template[j - 1],
                    configuration,
                )
                options.append(
                    (
                        costs[i - 1][j - 1] + operation_cost,
                        edits[i - 1][j - 1]
                        + (kind is AlignmentKind.SUBSTITUTION),
                        0,
                        "align",
                        operation_cost,
                        False,
                        False,
                    )
                )
            if i:
                feminine = (
                    i == n
                    and j == m
                    and syllable_signature[i - 1][0] == "0"
                )
                operation_cost = (
                    configuration.feminine_ending_cost
                    if feminine
                    else configuration.extra_syllable_cost
                )
                options.append(
                    (
                        costs[i - 1][j] + operation_cost,
                        edits[i - 1][j] + 1,
                        1,
                        "insert",
                        operation_cost,
                        feminine,
                        False,
                    )
                )
            if j:
                catalectic = i == n and j == m
                operation_cost = (
                    configuration.catalectic_ending_cost
                    if catalectic
                    else configuration.omitted_syllable_cost
                )
                options.append(
                    (
                        costs[i][j - 1] + operation_cost,
                        edits[i][j - 1] + 1,
                        2,
                        "delete",
                        operation_cost,
                        False,
                        catalectic,
                    )
                )
            best = min(
                options,
                key=lambda item: (round(item[0], 12), item[1], item[2]),
            )
            costs[i][j] = best[0]
            edits[i][j] = best[1]
            back[i][j] = (best[3], best[4], best[5], best[6])

    operations_reversed: list[_AlignmentPlanOperation] = []
    observed_reversed: list[str] = []
    template_reversed: list[str] = []
    i, j = n, m
    while i or j:
        pointer = back[i][j]
        if pointer is None:
            raise MeterModuleError("The meter alignment could not be reconstructed.")
        operation, operation_cost, feminine, catalectic = pointer
        if operation == "align":
            stress_digit, is_function_word = syllable_signature[i - 1]
            target = template[j - 1]
            _, kind = _aligned_cost_values(
                stress_digit,
                is_function_word,
                target,
                configuration,
            )
            operations_reversed.append(
                _AlignmentPlanOperation(
                    kind=kind,
                    observed_index=i - 1,
                    template_index=j - 1,
                    observed_stress=stress_digit,
                    template_stress=target,
                    cost=operation_cost,
                )
            )
            observed_reversed.append(stress_digit)
            template_reversed.append(target)
            i -= 1
            j -= 1
        elif operation == "insert":
            stress_digit = syllable_signature[i - 1][0]
            operations_reversed.append(
                _AlignmentPlanOperation(
                    kind=AlignmentKind.EXTRA_SYLLABLE,
                    observed_index=i - 1,
                    template_index=None,
                    observed_stress=stress_digit,
                    template_stress=None,
                    cost=operation_cost,
                    feminine_ending=feminine,
                )
            )
            observed_reversed.append(stress_digit)
            template_reversed.append("-")
            i -= 1
        else:
            target = template[j - 1]
            operations_reversed.append(
                _AlignmentPlanOperation(
                    kind=AlignmentKind.OMITTED_SYLLABLE,
                    observed_index=None,
                    template_index=j - 1,
                    observed_stress=None,
                    template_stress=target,
                    cost=operation_cost,
                    catalectic_ending=catalectic,
                )
            )
            observed_reversed.append("-")
            template_reversed.append(target)
            j -= 1
    return _AlignmentPlan(
        cost=costs[n][m],
        operations=tuple(reversed(operations_reversed)),
        aligned_observed="".join(reversed(observed_reversed)),
        aligned_template="".join(reversed(template_reversed)),
    )


def _align(
    syllables: tuple[StressSyllable, ...],
    template: str,
    configuration: MeterConfiguration,
) -> _Alignment:
    signature = tuple(
        (syllable.stress_digit, syllable.is_function_word)
        for syllable in syllables
    )
    plan = _alignment_plan(
        signature,
        template,
        _alignment_cost_configuration(configuration),
    )
    operations = []
    for operation in plan.operations:
        syllable = (
            syllables[operation.observed_index]
            if operation.observed_index is not None
            else None
        )
        operations.append(
            AlignmentOperation(
                kind=operation.kind,
                observed_index=operation.observed_index,
                template_index=operation.template_index,
                observed_stress=operation.observed_stress,
                template_stress=operation.template_stress,
                cost=operation.cost,
                token_id=syllable.token_id if syllable is not None else "",
                surface_form=(
                    syllable.surface_form if syllable is not None else ""
                ),
                part_of_speech=(
                    syllable.part_of_speech if syllable is not None else ""
                ),
                feminine_ending=operation.feminine_ending,
                catalectic_ending=operation.catalectic_ending,
            )
        )
    return _Alignment(
        cost=plan.cost,
        operations=tuple(operations),
        aligned_observed=plan.aligned_observed,
        aligned_template=plan.aligned_template,
    )


def meter_alignment_cache_info() -> dict[str, int]:
    """Developer-facing bounded-cache diagnostics without poem content."""

    info = _alignment_plan.cache_info()
    return {
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize or 0,
        "currsize": info.currsize,
    }


def clear_meter_alignment_cache() -> None:
    _alignment_plan.cache_clear()
    _candidate_templates.cache_clear()


def clear_candidate_template_cache() -> None:
    _candidate_templates.cache_clear()


def _local_binary_substitutions(
    alignment: _Alignment,
    template: MeterTemplate,
) -> tuple[int, int]:
    if len(template.foot_pattern) != 2:
        return 0, 0
    observed_by_template = {
        operation.template_index: (
            "0" if operation.observed_stress == "0" else "1"
        )
        for operation in alignment.operations
        if operation.template_index is not None
        and operation.observed_stress is not None
    }
    spondees = 0
    pyrrhics = 0
    for foot_index in range(template.foot_count):
        start = foot_index * 2
        pair = "".join(
            observed_by_template.get(start + offset, "-")
            for offset in range(2)
        )
        if pair == "11":
            spondees += 1
        elif pair == "00":
            pyrrhics += 1
    return spondees, pyrrhics


def _evaluate_variant_template(
    variant: StressVariant,
    template: MeterTemplate,
    configuration: MeterConfiguration,
) -> CandidateMeterFit:
    canonical = _align(variant.syllables, template.stress_template, configuration)
    selected = canonical
    evaluated_template = template.stress_template
    initial_inversion = 0
    total_cost = canonical.cost
    if template.pattern in {FootPattern.IAMBIC, FootPattern.TROCHAIC}:
        inverted_template = (
            template.stress_template[1::-1] + template.stress_template[2:]
        )
        inverted = _align(variant.syllables, inverted_template, configuration)
        inverted_total = inverted.cost + configuration.initial_inversion_cost
        if round(inverted_total, 12) < round(canonical.cost, 12):
            selected = inverted
            evaluated_template = inverted_template
            initial_inversion = 1
            total_cost = inverted_total
    denominator = max(len(variant.syllables), len(template.stress_template), 1)
    fit_score = max(0.0, min(1.0, 1.0 - (total_cost / denominator)))
    substitutions = sum(
        operation.kind is AlignmentKind.SUBSTITUTION
        for operation in selected.operations
    )
    extras = sum(
        operation.kind is AlignmentKind.EXTRA_SYLLABLE
        for operation in selected.operations
    )
    omissions = sum(
        operation.kind is AlignmentKind.OMITTED_SYLLABLE
        for operation in selected.operations
    )
    feminine = sum(operation.feminine_ending for operation in selected.operations)
    catalectic = sum(
        operation.catalectic_ending for operation in selected.operations
    )
    spondees, pyrrhics = _local_binary_substitutions(selected, template)
    return CandidateMeterFit(
        pattern=template.pattern,
        foot_pattern=template.foot_pattern,
        foot_count=template.foot_count,
        foot_count_name=template.foot_count_name,
        label=template.label,
        base_template_stress=template.stress_template,
        evaluated_template_stress=evaluated_template,
        selected_variant_id=variant.variant_id,
        selected_stress_sequence=variant.compact_stress_sequence,
        selected_word_stress_sequence=variant.word_stress_sequence,
        selected_pronunciation_choices=variant.pronunciation_choices,
        total_cost=total_cost,
        fit_score=fit_score,
        fit_label=_fit_label(fit_score),
        substitution_count=substitutions,
        extra_syllable_count=extras,
        omitted_syllable_count=omissions,
        initial_inversion_count=initial_inversion,
        feminine_ending_count=feminine,
        catalectic_count=catalectic,
        spondee_substitution_count=spondees,
        pyrrhic_substitution_count=pyrrhics,
        aligned_observed=selected.aligned_observed,
        aligned_template=selected.aligned_template,
        operations=selected.operations,
    )


def _candidate_sort_key(item: CandidateMeterFit) -> tuple[object, ...]:
    return (
        -round(item.fit_score, 12),
        round(item.total_cost, 12),
        item.substitution_count
        + item.extra_syllable_count
        + item.omitted_syllable_count,
        item.initial_inversion_count,
        _PATTERN_ORDER[item.pattern],
        item.foot_count,
        item.selected_stress_sequence,
        item.selected_variant_id,
    )


class MeterEstimator:
    """Evaluate line stress alternatives against the fixed candidate grid."""

    def __init__(self, configuration: MeterConfiguration) -> None:
        self.configuration = configuration
        self.templates = candidate_templates(configuration)

    def evaluate_line(self, line: MeterLineInput) -> MeterLineResult:
        coverage = (
            line.supported_token_count / line.eligible_token_count
            if line.eligible_token_count
            else None
        )
        if not line.eligible_token_count:
            return MeterLineResult(
                line_id=line.line_id,
                line_number=line.line_number,
                stanza_number=line.stanza_number,
                source_text=line.source_text,
                status=MeterLineStatus.NO_LEXICAL_TOKENS,
                eligible_token_count=0,
                supported_token_count=0,
                pronunciation_coverage=None,
                missing_forms=(),
                pronunciation_variant_count=0,
                variants_truncated=False,
                closest_candidate=None,
                alternative_candidates=(),
                candidate_fits=(),
                reason="The physical line contains no eligible lexical tokens.",
            )
        if line.supported_token_count < line.eligible_token_count:
            return MeterLineResult(
                line_id=line.line_id,
                line_number=line.line_number,
                stanza_number=line.stanza_number,
                source_text=line.source_text,
                status=MeterLineStatus.MISSING_PRONUNCIATION,
                eligible_token_count=line.eligible_token_count,
                supported_token_count=line.supported_token_count,
                pronunciation_coverage=coverage,
                missing_forms=line.missing_forms,
                pronunciation_variant_count=line.variant_count_before_limit,
                variants_truncated=False,
                closest_candidate=None,
                alternative_candidates=(),
                candidate_fits=(),
                reason=(
                    "At least one eligible token has no usable dictionary or "
                    "scholar-supplied stress alternative. No partial line meter "
                    "fit was fabricated."
                ),
            )
        if (
            line.variants_truncated
            or line.variant_count_before_limit
            > self.configuration.maximum_line_variants
        ):
            return MeterLineResult(
                line_id=line.line_id,
                line_number=line.line_number,
                stanza_number=line.stanza_number,
                source_text=line.source_text,
                status=MeterLineStatus.TOO_MANY_VARIANTS,
                eligible_token_count=line.eligible_token_count,
                supported_token_count=line.supported_token_count,
                pronunciation_coverage=coverage,
                missing_forms=(),
                pronunciation_variant_count=line.variant_count_before_limit,
                variants_truncated=True,
                closest_candidate=None,
                alternative_candidates=(),
                candidate_fits=(),
                reason=(
                    "The number of dictionary stress combinations exceeds the "
                    "configured transparent-analysis limit. The line remains "
                    "unscored rather than silently dropping alternatives."
                ),
            )
        if not line.stress_variants:
            raise MeterModuleError(
                "A fully supported meter line requires at least one stress variant."
            )
        best_by_template: list[CandidateMeterFit] = []
        for template in self.templates:
            fits = (
                _evaluate_variant_template(variant, template, self.configuration)
                for variant in line.stress_variants
            )
            best_by_template.append(min(fits, key=_candidate_sort_key))
        ranked = tuple(sorted(best_by_template, key=_candidate_sort_key))
        closest = ranked[0]
        alternatives = ranked[
            1 : 1 + self.configuration.retained_alternative_candidates
        ]
        return MeterLineResult(
            line_id=line.line_id,
            line_number=line.line_number,
            stanza_number=line.stanza_number,
            source_text=line.source_text,
            status=MeterLineStatus.ANALYZED,
            eligible_token_count=line.eligible_token_count,
            supported_token_count=line.supported_token_count,
            pronunciation_coverage=coverage,
            missing_forms=(),
            pronunciation_variant_count=line.variant_count_before_limit,
            variants_truncated=False,
            closest_candidate=closest,
            alternative_candidates=alternatives,
            candidate_fits=ranked,
            reason=(
                "All eligible tokens supplied at least one retained stress "
                "alternative. The displayed result is the nearest configured "
                "candidate, not a definitive scansion."
            ),
        )


def _token_stress_options(
    token: PronunciationTokenResult,
) -> tuple[str, ...]:
    if not token.eligible:
        return ()
    if token.resolved and token.resolved_stress_pattern:
        return (token.resolved_stress_pattern,)
    if token.status is PronunciationStatus.AMBIGUOUS_DICTIONARY:
        return tuple(
            sorted(
                {
                    pattern
                    for pattern in token.dictionary_candidate_stresses
                    if pattern and all(digit in "012" for digit in pattern)
                },
                key=lambda item: (len(item), item),
            )
        )
    return ()


def meter_line_inputs_from_pronunciation(
    pronunciation: PronunciationAnalysisResult,
    configuration: MeterConfiguration,
) -> tuple[MeterLineInput, ...]:
    """Create bounded, auditable stress combinations without changing Stage 5."""

    audit_by_line: dict[int, list[PronunciationTokenResult]] = {}
    for item in pronunciation.token_audit:
        audit_by_line.setdefault(item.line_number, []).append(item)
    evidence: list[MeterLineInput] = []
    for line in pronunciation.line_summaries:
        eligible = tuple(
            item
            for item in audit_by_line.get(line.line_number, ())
            if item.eligible
        )
        option_rows = tuple(
            (item, _token_stress_options(item)) for item in eligible
        )
        missing = tuple(
            item.surface_form for item, options in option_rows if not options
        )
        supported_count = sum(bool(options) for _, options in option_rows)
        variant_count = 0
        if option_rows and not missing:
            variant_count = 1
            for _, options in option_rows:
                variant_count *= len(options)
        variants_truncated = variant_count > configuration.maximum_line_variants
        variants: list[StressVariant] = []
        if variant_count and not variants_truncated:
            for variant_index, choices in enumerate(
                product(*(options for _, options in option_rows)),
                start=1,
            ):
                syllables: list[StressSyllable] = []
                choice_labels: list[str] = []
                for word_index, ((token, _), stress_pattern) in enumerate(
                    zip(option_rows, choices, strict=True)
                ):
                    choice_labels.append(
                        f"{token.surface_form}={stress_pattern}"
                    )
                    syllables.extend(
                        StressSyllable(
                            stress_digit=digit,
                            token_id=token.token_id,
                            surface_form=token.surface_form,
                            part_of_speech=token.part_of_speech,
                            word_index=word_index,
                            syllable_index_in_word=syllable_index,
                        )
                        for syllable_index, digit in enumerate(stress_pattern)
                    )
                identity = hashlib.sha256(
                    "\x1f".join(choice_labels).encode("utf-8")
                ).hexdigest()[:12]
                variants.append(
                    StressVariant(
                        variant_id=(
                            f"{line.line_id}-stress-{variant_index}-{identity}"
                        ),
                        syllables=tuple(syllables),
                        word_stress_sequence=" | ".join(choices),
                        pronunciation_choices=tuple(choice_labels),
                    )
                )
        evidence.append(
            MeterLineInput(
                line_id=line.line_id,
                line_number=line.line_number,
                stanza_number=line.stanza_number,
                source_text=line.source_text,
                eligible_token_count=len(eligible),
                supported_token_count=supported_count,
                missing_forms=missing,
                stress_variants=tuple(variants),
                variant_count_before_limit=variant_count,
                variants_truncated=variants_truncated,
            )
        )
    return tuple(evidence)


def _candidate_summaries(
    analyzed_lines: tuple[MeterLineResult, ...],
    configuration: MeterConfiguration,
) -> tuple[MeterCandidateSummary, ...]:
    if not analyzed_lines:
        return ()
    by_key: dict[tuple[FootPattern, int], list[CandidateMeterFit]] = {}
    for line in analyzed_lines:
        for fit in line.candidate_fits:
            by_key.setdefault((fit.pattern, fit.foot_count), []).append(fit)
    unranked: list[MeterCandidateSummary] = []
    for (pattern, foot_count), fits in by_key.items():
        values = [item.fit_score for item in fits]
        matching = sum(value >= configuration.line_match_threshold for value in values)
        unranked.append(
            MeterCandidateSummary(
                rank=0,
                pattern=pattern,
                foot_count=foot_count,
                foot_count_name=FOOT_COUNT_NAMES[foot_count],
                label=f"{pattern.value.capitalize()} {FOOT_COUNT_NAMES[foot_count]}",
                analyzed_line_count=len(values),
                mean_fit=fmean(values),
                median_fit=median(values),
                fit_variability=pstdev(values) if len(values) > 1 else None,
                matching_line_count=matching,
                matching_line_proportion=matching / len(values),
            )
        )
    ranked = sorted(
        unranked,
        key=lambda item: (
            -(item.mean_fit or 0),
            -(item.matching_line_proportion or 0),
            _PATTERN_ORDER[item.pattern],
            item.foot_count,
        ),
    )
    return tuple(
        MeterCandidateSummary(**{**asdict(item), "rank": rank})
        for rank, item in enumerate(ranked, start=1)
    )


def _fit_for(
    line: MeterLineResult,
    pattern: FootPattern,
    foot_count: int,
) -> CandidateMeterFit:
    return next(
        fit
        for fit in line.candidate_fits
        if fit.pattern is pattern and fit.foot_count == foot_count
    )


def _dominant_pattern(
    analyzed_lines: tuple[MeterLineResult, ...],
    configuration: MeterConfiguration,
) -> tuple[
    FootPattern | None,
    float | None,
    int | None,
    float | None,
]:
    if not analyzed_lines:
        return None, None, None, None
    family_values: dict[FootPattern, list[CandidateMeterFit]] = {
        pattern: [] for pattern in PRIMARY_FOOT_PATTERNS
    }
    for line in analyzed_lines:
        for pattern in PRIMARY_FOOT_PATTERNS:
            fits = [
                item for item in line.candidate_fits if item.pattern is pattern
            ]
            family_values[pattern].append(min(fits, key=_candidate_sort_key))
    pattern = min(
        PRIMARY_FOOT_PATTERNS,
        key=lambda item: (
            -fmean(fit.fit_score for fit in family_values[item]),
            _PATTERN_ORDER[item],
        ),
    )
    chosen = family_values[pattern]
    mean_fit = fmean(item.fit_score for item in chosen)
    plausible = [
        item.foot_count
        for item in chosen
        if item.fit_score >= configuration.line_match_threshold
    ]
    if not plausible:
        return pattern, mean_fit, None, None
    counts = Counter(plausible)
    most_common_count = max(counts.values())
    tied = sorted(
        foot_count
        for foot_count, count in counts.items()
        if count == most_common_count
    )
    foot_count = tied[0] if len(tied) == 1 else None
    share = most_common_count / len(plausible)
    return pattern, mean_fit, foot_count, share


def _common_deviation(fits: Iterable[CandidateMeterFit]) -> str:
    counters: Counter[str] = Counter()
    for fit in fits:
        counters.update(
            {
                "Substitution": fit.substitution_count,
                "Initial inversion": fit.initial_inversion_count,
                "Extra syllable": fit.extra_syllable_count,
                "Omitted syllable": fit.omitted_syllable_count,
                "Feminine ending": fit.feminine_ending_count,
                "Catalectic ending": fit.catalectic_count,
                "Spondaic substitution": fit.spondee_substitution_count,
                "Pyrrhic substitution": fit.pyrrhic_substitution_count,
            }
        )
    if not counters or max(counters.values(), default=0) == 0:
        return "No recurring deviation in the selected alignments"
    maximum = max(counters.values())
    return sorted(label for label, count in counters.items() if count == maximum)[0]


def _confidence(
    *,
    assessment: MeterAssessment,
    analyzable_lines: int,
    coverage: float | None,
    mean_fit: float | None,
    margin: float | None,
    matching_proportion: float | None,
    configuration: MeterConfiguration,
) -> tuple[str, str]:
    if assessment is MeterAssessment.INSUFFICIENT_EVIDENCE:
        return (
            "Insufficient evidence",
            (
                "Fewer than the configured minimum lines were analyzable or "
                "line coverage was too sparse for a poem-level candidate."
            ),
        )
    if assessment is MeterAssessment.MIXED_OR_IRREGULAR:
        return (
            "Low",
            (
                "The nearest configured candidate is weak or too close to an "
                "alternative. This rule-based label is not a probability."
            ),
        )
    assert coverage is not None and mean_fit is not None and margin is not None
    assert matching_proportion is not None
    if (
        analyzable_lines >= 4
        and coverage >= 0.80
        and mean_fit >= 0.85
        and margin >= 0.08
        and matching_proportion >= 0.75
    ):
        return (
            "High",
            (
                "At least four lines, strong line coverage, high mean fit, a "
                "clear candidate margin, and broad line agreement met the "
                "configured rule. This is not a calibrated probability."
            ),
        )
    if (
        analyzable_lines >= max(3, configuration.minimum_analyzable_lines)
        and coverage >= 0.60
        and mean_fit >= 0.70
        and margin >= configuration.ambiguity_margin_threshold
        and matching_proportion >= 0.50
    ):
        return (
            "Moderate",
            (
                "The configured evidence, fit, margin, and agreement rules were "
                "met at a moderate level. This is not a calibrated probability."
            ),
        )
    return (
        "Low",
        (
            "The candidate remains reportable as a nearest template, but one "
            "or more configured evidence, fit, margin, or agreement rules were "
            "not met. This is not a calibrated probability."
        ),
    )


def _summary(
    line_results: tuple[MeterLineResult, ...],
    candidate_summaries: tuple[MeterCandidateSummary, ...],
    configuration: MeterConfiguration,
) -> MeterSummary:
    eligible_lines = tuple(
        item
        for item in line_results
        if item.status is not MeterLineStatus.NO_LEXICAL_TOKENS
    )
    analyzed = tuple(
        item for item in line_results if item.status is MeterLineStatus.ANALYZED
    )
    coverage = len(analyzed) / len(eligible_lines) if eligible_lines else None
    selected = candidate_summaries[0] if candidate_summaries else None
    alternative = (
        candidate_summaries[1] if len(candidate_summaries) > 1 else None
    )
    selected_label = selected.label if selected else ""
    selected_pattern = selected.pattern if selected else None
    selected_foot_count = selected.foot_count if selected else None
    selected_foot_name = selected.foot_count_name if selected else ""
    selected_mean_fit = selected.mean_fit if selected else None
    selected_median_fit = selected.median_fit if selected else None
    selected_matching_count = selected.matching_line_count if selected else 0
    selected_matching_proportion = (
        selected.matching_line_proportion if selected else None
    )
    selected_fits = (
        tuple(
            _fit_for(
                line,
                selected.pattern,
                selected.foot_count,
            )
            for line in analyzed
        )
        if selected is not None
        else ()
    )
    comparison_score = alternative.mean_fit or 0 if alternative else 0
    alternative_label = alternative.label if alternative else ""
    margin = (
        (selected_mean_fit or 0) - comparison_score
        if selected_mean_fit is not None and alternative_label
        else None
    )
    dominant_pattern, family_fit, dominant_feet, foot_share = _dominant_pattern(
        analyzed,
        configuration,
    )
    if (
        len(analyzed) < configuration.minimum_analyzable_lines
        or coverage is None
        or coverage < 0.50
    ):
        assessment = MeterAssessment.INSUFFICIENT_EVIDENCE
    elif (
        not selected_label
        or (selected_mean_fit or 0) < configuration.irregular_fit_threshold
        or margin is None
        or margin < configuration.ambiguity_margin_threshold
    ):
        assessment = MeterAssessment.MIXED_OR_IRREGULAR
    elif (
        dominant_feet is None
        or foot_share is None
        or foot_share < configuration.stable_foot_count_threshold
    ):
        assessment = MeterAssessment.MIXED_LINE_LENGTHS
    else:
        assessment = MeterAssessment.RECURRING_CANDIDATE
    confidence, explanation = _confidence(
        assessment=assessment,
        analyzable_lines=len(analyzed),
        coverage=coverage,
        mean_fit=selected_mean_fit,
        margin=margin,
        matching_proportion=selected_matching_proportion,
        configuration=configuration,
    )
    values = [fit.fit_score for fit in selected_fits]
    return MeterSummary(
        eligible_line_count=len(eligible_lines),
        analyzable_line_count=len(analyzed),
        unanalyzable_line_count=len(eligible_lines) - len(analyzed),
        line_coverage=coverage,
        closest_candidate_kind="fixed pattern and foot count",
        closest_candidate_label=selected_label,
        closest_pattern=selected_pattern,
        closest_foot_count=selected_foot_count,
        closest_foot_count_name=selected_foot_name,
        alternative_candidate_label=alternative_label,
        dominant_pattern=dominant_pattern,
        dominant_pattern_mean_fit=family_fit,
        dominant_foot_count=dominant_feet,
        dominant_foot_count_name=(
            FOOT_COUNT_NAMES[dominant_feet] if dominant_feet else ""
        ),
        dominant_foot_count_share=foot_share,
        assessment=assessment,
        candidate_confidence=confidence,
        confidence_explanation=explanation,
        whole_poem_mean_fit=selected_mean_fit,
        whole_poem_median_fit=selected_median_fit,
        candidate_margin=margin,
        matching_line_count=selected_matching_count,
        matching_line_proportion=selected_matching_proportion,
        rhythmic_regularity=selected_matching_proportion,
        rhythmic_variability=(
            pstdev(values) if len(values) > 1 else None
        ),
        substitution_count=sum(item.substitution_count for item in selected_fits),
        initial_inversion_count=sum(
            item.initial_inversion_count for item in selected_fits
        ),
        extra_syllable_count=sum(
            item.extra_syllable_count for item in selected_fits
        ),
        omitted_syllable_count=sum(
            item.omitted_syllable_count for item in selected_fits
        ),
        feminine_ending_count=sum(
            item.feminine_ending_count for item in selected_fits
        ),
        catalectic_count=sum(item.catalectic_count for item in selected_fits),
        spondee_substitution_count=sum(
            item.spondee_substitution_count for item in selected_fits
        ),
        pyrrhic_substitution_count=sum(
            item.pyrrhic_substitution_count for item in selected_fits
        ),
        common_deviation=_common_deviation(selected_fits),
        pronunciation_alternative_line_count=sum(
            item.pronunciation_variant_count > 1 for item in analyzed
        ),
        is_sparse=len(analyzed) < configuration.minimum_analyzable_lines,
    )


def summarize_meter_lines(
    line_results: tuple[MeterLineResult, ...],
    configuration: MeterConfiguration,
) -> tuple[
    MeterSummary,
    tuple[MeterCandidateSummary, ...],
]:
    """Summarize fixed pattern-and-foot-count candidates from line audits."""

    analyzed = tuple(
        item for item in line_results if item.status is MeterLineStatus.ANALYZED
    )
    candidate_summaries = _candidate_summaries(analyzed, configuration)
    return (
        _summary(
            line_results,
            candidate_summaries,
            configuration,
        ),
        candidate_summaries,
    )


def _warnings(
    summary: MeterSummary,
    line_results: tuple[MeterLineResult, ...],
    configuration: MeterConfiguration,
) -> tuple[ModuleWarning, ...]:
    warnings = [
        ModuleWarning(
            code="candidate_meter_not_fact",
            message=(
                "Stage 6 reports the closest configured meter candidate and "
                "alignment evidence. It does not establish a definitive meter, "
                "performed rhythm, authorial intention, or correct scansion."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
        ModuleWarning(
            code="fit_not_probability",
            message=(
                "Fit is a normalized configured alignment similarity, and "
                "confidence is a rule-based category. Neither is a probability."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
        ModuleWarning(
            code="dictionary_stress_caution",
            message=(
                "The estimator begins from North American dictionary lexical "
                "stress. Contextual promotion, demotion, dialect, historical "
                "pronunciation, elision, and performance may differ."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
    ]
    if summary.line_coverage is None:
        warnings.append(
            ModuleWarning(
                code="no_eligible_lines",
                message="No physical line contained eligible lexical tokens.",
            )
        )
    elif summary.line_coverage < configuration.low_line_coverage_warning_threshold:
        warnings.append(
            ModuleWarning(
                code="low_meter_line_coverage",
                message=(
                    "Fewer than the configured share of eligible physical lines "
                    "could be aligned because pronunciation evidence was missing "
                    "or combinatorially unresolved."
                ),
                technical_detail=(
                    f"{summary.analyzable_line_count} of "
                    f"{summary.eligible_line_count} eligible lines analyzed."
                ),
            )
        )
    if summary.assessment is MeterAssessment.INSUFFICIENT_EVIDENCE:
        warnings.append(
            ModuleWarning(
                code="insufficient_meter_evidence",
                message=(
                    "There is insufficient analyzable line evidence for a "
                    "poem-level recurring meter candidate."
                ),
            )
        )
    elif summary.assessment is MeterAssessment.MIXED_OR_IRREGULAR:
        warnings.append(
            ModuleWarning(
                code="mixed_or_irregular_meter",
                message=(
                    "The nearest configured candidates are weak or too close under "
                    "the configured method. Treat the poem-level assessment as "
                    "mixed or irregular."
                ),
            )
        )
    elif summary.assessment is MeterAssessment.MIXED_LINE_LENGTHS:
        warnings.append(
            ModuleWarning(
                code="mixed_line_lengths",
                message=(
                    "A recurring stress-pattern family is visible, but no single "
                    "foot count dominates the analyzable lines."
                ),
                severity=WarningSeverity.INFORMATION,
            )
        )
    if summary.pronunciation_alternative_line_count:
        warnings.append(
            ModuleWarning(
                code="metrical_pronunciation_paths",
                message=(
                    "Some line fits selected among retained dictionary stress "
                    "alternatives. Those choices are candidate-specific and do "
                    "not replace the Stage 5 pronunciation audit."
                ),
                severity=WarningSeverity.INFORMATION,
                technical_detail=(
                    f"{summary.pronunciation_alternative_line_count} line(s)."
                ),
            )
        )
    missing = sum(
        item.status is MeterLineStatus.MISSING_PRONUNCIATION
        for item in line_results
    )
    if missing:
        warnings.append(
            ModuleWarning(
                code="missing_pronunciation_lines",
                message=(
                    "Some lines remain unscored because at least one eligible "
                    "word has no usable pronunciation evidence."
                ),
                technical_detail=f"{missing} line(s).",
            )
        )
    exceeded = sum(
        item.status is MeterLineStatus.TOO_MANY_VARIANTS
        for item in line_results
    )
    if exceeded:
        warnings.append(
            ModuleWarning(
                code="pronunciation_variant_limit",
                message=(
                    "Some lines exceeded the configured stress-combination "
                    "limit and remain unscored without dropping alternatives."
                ),
                technical_detail=f"{exceeded} line(s).",
            )
        )
    return tuple(warnings)


def _metrics(
    summary: MeterSummary,
    line_results: tuple[MeterLineResult, ...],
    performance_aware: PerformanceAwareMeterResult | None = None,
) -> tuple[ModuleMetric, ...]:
    metrics: list[ModuleMetric] = [
        ModuleMetric(
            metric_id="meter.closest_candidate",
            value=summary.closest_candidate_label or None,
            layer=ResultLayer.INTERPRETATION,
            unit="candidate pattern and foot-count label",
            denominator=f"{summary.analyzable_line_count} analyzable lines",
            note="Nearest configured candidate; not a definitive classification.",
        ),
        ModuleMetric(
            metric_id="meter.closest_candidate_kind",
            value=summary.closest_candidate_kind or None,
            layer=ResultLayer.INTERPRETATION,
            unit="candidate structure kind",
            denominator=f"{summary.analyzable_line_count} analyzable lines",
        ),
        ModuleMetric(
            metric_id="meter.whole_poem_mean_fit",
            value=summary.whole_poem_mean_fit,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="normalized alignment similarity 0-1",
            weighting="equal analyzable physical lines",
            denominator=f"{summary.analyzable_line_count} analyzable lines",
            note="Configured similarity, not a probability.",
        ),
        ModuleMetric(
            metric_id="meter.matching_line_proportion",
            value=summary.matching_line_proportion,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="proportion",
            weighting="equal analyzable physical lines",
            denominator=f"{summary.analyzable_line_count} analyzable lines",
        ),
        ModuleMetric(
            metric_id="meter.rhythmic_variability",
            value=summary.rhythmic_variability,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="population SD of selected-candidate line fit",
            weighting="equal analyzable physical lines",
            denominator=f"{summary.analyzable_line_count} analyzable lines",
        ),
        ModuleMetric(
            metric_id="meter.candidate_confidence",
            value=summary.candidate_confidence,
            layer=ResultLayer.INTERPRETATION,
            unit="rule-based category",
            denominator=f"{summary.analyzable_line_count} analyzable lines",
            note="Not a calibrated probability.",
        ),
    ]
    for line in line_results:
        candidate = line.closest_candidate
        metrics.extend(
            (
                ModuleMetric(
                    metric_id="meter.line_closest_candidate",
                    value=candidate.label if candidate else None,
                    layer=ResultLayer.INTERPRETATION,
                    scope="line",
                    scope_id=line.line_id,
                    unit="candidate pattern and foot-count label",
                    denominator=(
                        f"{line.supported_token_count} of "
                        f"{line.eligible_token_count} eligible tokens supported"
                    ),
                    note="Nearest configured candidate for this physical line.",
                ),
                ModuleMetric(
                    metric_id="meter.line_fit",
                    value=candidate.fit_score if candidate else None,
                    layer=ResultLayer.COMPUTED_SUMMARY,
                    scope="line",
                    scope_id=line.line_id,
                    unit="normalized alignment similarity 0-1",
                    denominator=(
                        f"{line.supported_token_count} of "
                        f"{line.eligible_token_count} eligible tokens supported"
                    ),
                ),
            )
        )
    if performance_aware is not None:
        performance_summary = performance_aware.poem_summary
        metrics.extend(
            (
                ModuleMetric(
                    metric_id="meter.performance.rhythmic_organization",
                    value=performance_summary.rhythmic_organization.value,
                    layer=ResultLayer.INTERPRETATION,
                    unit="rule-based organization category",
                    denominator=(
                        f"{performance_summary.analyzable_line_count} "
                        "performance-aware line realizations"
                    ),
                    note=(
                        "A profile-dependent interpretation, not a recovered "
                        "performance or authorial intention."
                    ),
                ),
                ModuleMetric(
                    metric_id="meter.performance.primary_candidate",
                    value=performance_summary.primary_meter or None,
                    layer=ResultLayer.INTERPRETATION,
                    unit="reranked candidate label",
                    denominator=(
                        f"{performance_summary.analyzable_line_count} "
                        "performance-aware line realizations"
                    ),
                ),
                ModuleMetric(
                    metric_id="meter.performance.mean_realized_score",
                    value=performance_summary.mean_realized_score,
                    layer=ResultLayer.COMPUTED_SUMMARY,
                    unit="inspectable component score 0-1",
                    weighting="equal analyzable physical lines",
                    denominator=(
                        f"{performance_summary.analyzable_line_count} "
                        "performance-aware line realizations"
                    ),
                    note="Configured score, not a probability.",
                ),
                ModuleMetric(
                    metric_id="meter.performance.confidence",
                    value=performance_summary.confidence.value,
                    layer=ResultLayer.INTERPRETATION,
                    unit="rule-based category",
                    denominator=(
                        f"{performance_summary.analyzable_line_count} "
                        "performance-aware line realizations"
                    ),
                    note="Not a calibrated probability.",
                ),
            )
        )
    return tuple(metrics)


class MeterModule:
    """Stage 6 dependent module using only retained Stage 5 stress evidence."""

    name = "candidate_meter_and_rhythmic_regularity"
    version = "2.0.0"

    def validate_resources(self) -> tuple[ResourceStatus, ...]:
        return ()

    def analyze_detailed(
        self,
        module_input: ModuleInput,
        pronunciation: PronunciationAnalysisResult,
        configuration: MeterConfiguration | None = None,
    ) -> MeterAnalysisResult:
        configuration = configuration or MeterConfiguration()
        if (
            pronunciation.module_result.text_id != module_input.document.text_id
            or pronunciation.module_result.text_version_id
            != module_input.document.text_version_id
        ):
            raise MeterModuleError(
                "Stage 6 and Stage 5 must describe the same preserved text version."
            )
        line_inputs = meter_line_inputs_from_pronunciation(
            pronunciation,
            configuration,
        )
        estimator = MeterEstimator(configuration)
        line_results = tuple(estimator.evaluate_line(item) for item in line_inputs)
        summary, candidate_summaries = summarize_meter_lines(
            line_results,
            configuration,
        )
        performance_aware = None
        if configuration.analysis_mode is not MeterAnalysisMode.CANDIDATE:
            from versevad.prosody.performance_meter import (
                analyze_performance_aware_meter,
            )

            performance_aware = analyze_performance_aware_meter(
                module_input,
                line_results,
                configuration,
            )
        warnings = _warnings(summary, line_results, configuration)
        coverage = ModuleCoverage.from_counts(
            coverage_id="meter.analyzable_physical_lines",
            eligible_count=summary.eligible_line_count,
            matched_count=summary.analyzable_line_count,
            unit="physical lines containing lexical tokens",
            unmatched_items=tuple(
                f"line {item.line_number}: {', '.join(item.missing_forms)}"
                for item in line_results
                if item.status is not MeterLineStatus.ANALYZED
                and item.status is not MeterLineStatus.NO_LEXICAL_TOKENS
            ),
            note=(
                "A line is analyzable only when every eligible word supplies at "
                "least one retained stress alternative within the configured "
                "combination limit."
            ),
        )
        provenance = ModuleProvenance(
            software_version=__version__,
            source_text_sha256=module_input.document.text_sha256,
            preprocessing_recipe=module_input.preprocessing.recipe_id,
            pipeline_name=module_input.preprocessing.pipeline_name,
            pipeline_version=module_input.preprocessing.pipeline_version,
            configuration_id=configuration.configuration_id,
            scenario_id=configuration.scenario_id,
            lookup_policy=(
                "Consumes retained Stage 5 exact observed-form dictionary or "
                "scholar-override stress evidence. Material dictionary "
                "alternatives are explored as candidate paths without changing "
                "the pronunciation result. When performance-aware analysis is "
                "selected, retained candidates are reranked by separately "
                "reported context, phrase, recurrence, and declared-profile "
                "components; source lexical stress remains unchanged."
            ),
            inclusion_policy=(
                "Physical lines require stress evidence for every eligible "
                "lexical token. Five recurring patterns are compared at one "
                "through eight feet; spondees and pyrrhics are local "
                "substitution labels. No named stanza-form classification is "
                "added."
            ),
            resources=pronunciation.module_result.provenance.resources,
        )
        identity_payload = json.dumps(
            {
                "text_sha256": module_input.document.text_sha256,
                "configuration_id": configuration.configuration_id,
                "pronunciation_configuration_id": (
                    pronunciation.configuration.configuration_id
                ),
                "closest_candidate": summary.closest_candidate_label,
                "closest_candidate_kind": summary.closest_candidate_kind,
                "analysis_mode": configuration.analysis_mode.value,
                "style_profile": configuration.style_profile.value,
                "performance_primary_candidate": (
                    performance_aware.poem_summary.primary_meter
                    if performance_aware is not None
                    else ""
                ),
                "line_statuses": [
                    (item.line_id, item.status.value) for item in line_results
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        result_id = "meter-result-v2:" + hashlib.sha256(
            identity_payload.encode("utf-8")
        ).hexdigest()[:20]
        module_result = ModuleResult(
            result_id=result_id,
            module_name=self.name,
            module_version=self.version,
            text_id=module_input.document.text_id,
            text_version_id=module_input.document.text_version_id,
            metrics=_metrics(summary, line_results, performance_aware),
            coverage=(coverage,),
            warnings=warnings,
            provenance=provenance,
        )
        return MeterAnalysisResult(
            module_result=module_result,
            configuration=configuration,
            pronunciation_configuration_id=(
                pronunciation.configuration.configuration_id
            ),
            line_results=line_results,
            candidate_summaries=candidate_summaries,
            summary=summary,
            performance_aware=performance_aware,
        )
