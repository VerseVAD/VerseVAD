"""Transparent contextual realization above VerseVAD's candidate-meter layer.

This module never rewrites dictionary stress or replaces the Stage 6 candidate
grid.  It interprets retained alignment paths as plausible performances under
one declared broad style profile.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from enum import StrEnum
from statistics import fmean, median, pstdev
from typing import Iterable

from versevad.core.modules import ModuleInput
from versevad.models import TokenRecord
from versevad.prosody.meter import (
    FUNCTION_WORD_POS,
    AlignmentKind,
    CandidateMeterFit,
    FootPattern,
    MeterAnalysisMode,
    MeterConfiguration,
    MeterInterpretationDepth,
    MeterLineResult,
    MeterLineStatus,
    MeterStyleProfile,
)


class MetricalPosition(StrEnum):
    WEAK = "weak"
    STRONG = "strong"
    EXTRAMETRICAL = "extrametrical"
    OMITTED = "omitted"


class MetricalAdjustment(StrEnum):
    NONE = "none"
    PROMOTION = "promotion"
    DEMOTION = "demotion"
    SECONDARY_FLEXIBILITY = "secondary_stress_flexibility"
    EXTRAMETRICAL = "extrametrical"
    OMITTED = "omitted"


class MetricalConfidence(StrEnum):
    STRONG = "strong"
    MODERATE = "moderate"
    TENTATIVE = "tentative"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT = "insufficient_evidence"


class RhythmicOrganization(StrEnum):
    ACCENTUAL_SYLLABIC = "accentual_syllabic"
    ACCENTUAL = "accentual"
    SYLLABIC = "syllabic"
    LOCALLY_METRICAL = "locally_metrical"
    MIXED = "mixed"
    NO_STABLE_PATTERN = "no_stable_recurring_meter"
    INSUFFICIENT = "insufficient_evidence"


@dataclass(frozen=True)
class MeterStyleDefinition:
    profile: MeterStyleProfile
    label: str
    version: str
    substitution_tolerance: float
    promotion_tolerance: float
    demotion_tolerance: float
    phrase_sensitivity: float
    regularity_preference: float
    accentual_preference: float
    note: str


STYLE_DEFINITIONS: dict[MeterStyleProfile, MeterStyleDefinition] = {
    MeterStyleProfile.GENERAL: MeterStyleDefinition(
        MeterStyleProfile.GENERAL,
        "General English Verse",
        "1.0",
        0.55,
        0.55,
        0.55,
        0.65,
        0.65,
        0.45,
        "Neutral broad-English settings; no period or author is inferred.",
    ),
    MeterStyleProfile.TRADITIONAL: MeterStyleDefinition(
        MeterStyleProfile.TRADITIONAL,
        "Traditional Accentual-Syllabic Verse",
        "1.0",
        0.48,
        0.52,
        0.56,
        0.58,
        0.92,
        0.20,
        "Favors a stable base while permitting established local substitutions.",
    ),
    MeterStyleProfile.ROMANTIC_VICTORIAN: MeterStyleDefinition(
        MeterStyleProfile.ROMANTIC_VICTORIAN,
        "Romantic / Victorian Verse",
        "1.0",
        0.70,
        0.72,
        0.68,
        0.78,
        0.72,
        0.42,
        "Allows broader expressive substitution and phrase-sensitive movement.",
    ),
    MeterStyleProfile.MODERNIST: MeterStyleDefinition(
        MeterStyleProfile.MODERNIST,
        "Modernist Verse",
        "1.0",
        0.86,
        0.82,
        0.82,
        0.88,
        0.34,
        0.72,
        "Tolerates local meter, disrupted periodicity, and speech-based rhythm.",
    ),
    MeterStyleProfile.CONTEMPORARY_FORMAL: MeterStyleDefinition(
        MeterStyleProfile.CONTEMPORARY_FORMAL,
        "Contemporary Formal Verse",
        "1.0",
        0.68,
        0.70,
        0.68,
        0.72,
        0.82,
        0.38,
        "Expects an intentional base while allowing looser contemporary diction.",
    ),
    MeterStyleProfile.FREE_VERSE_CADENTIAL: MeterStyleDefinition(
        MeterStyleProfile.FREE_VERSE_CADENTIAL,
        "Free Verse / Cadential",
        "1.0",
        0.94,
        0.90,
        0.90,
        0.96,
        0.12,
        0.95,
        "Prioritizes beats, phrasing, recurrence, cadence, and local passages.",
    ),
    MeterStyleProfile.CUSTOM: MeterStyleDefinition(
        MeterStyleProfile.CUSTOM,
        "Custom",
        "1.0",
        0.60,
        0.60,
        0.60,
        0.70,
        0.60,
        0.50,
        "Uses the explicit Stage 14 configuration weights; no hidden profile.",
    ),
}


@dataclass(frozen=True)
class CaesuraEvidence:
    after_syllable: int
    punctuation: str
    strength: str
    confidence: float
    evidence: str


@dataclass(frozen=True)
class RealizedSyllable:
    observed_index: int | None
    template_index: int | None
    token_id: str
    surface_form: str
    part_of_speech: str
    lexical_stress: str | None
    metrical_position: MetricalPosition
    adjustment: MetricalAdjustment
    contextual_prominence: float | None
    position_fit: float
    symbol: str
    evidence: str


@dataclass(frozen=True)
class MetricalSubstitution:
    kind: str
    label: str
    start_syllable: int | None
    end_syllable: int | None
    evidence: str
    confidence: float


@dataclass(frozen=True)
class RealizationScores:
    candidate_fit: float
    contextual_fit: float
    syllable_count_fit: float
    phrase_fit: float
    line_ending_fit: float
    pronunciation_plausibility: float
    poem_consistency: float
    stanza_consistency: float
    style_compatibility: float
    substitution_penalty: float
    overall: float
    weights: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class RealizedScansion:
    candidate_label: str
    pattern: FootPattern
    foot_count: int
    lexical_stress: str
    candidate_template: str
    realized_display: str
    syllables: tuple[RealizedSyllable, ...]
    substitutions: tuple[MetricalSubstitution, ...]
    promotions: int
    demotions: int
    stress_clashes: tuple[int, ...]
    stress_lapses: tuple[tuple[int, int], ...]
    caesurae: tuple[CaesuraEvidence, ...]
    selected_pronunciation_path: tuple[str, ...]
    scores: RealizationScores


@dataclass(frozen=True)
class PerformanceLineResult:
    line_id: str
    line_number: int
    stanza_number: int
    source_text: str
    status: MeterLineStatus
    raw_lexical_stress: str
    candidate_meter: str
    primary_realization: RealizedScansion | None
    alternate_realizations: tuple[RealizedScansion, ...]
    confidence: MetricalConfidence
    score_margin: float | None
    explanation: str


@dataclass(frozen=True)
class ScholarScansionRevision:
    line_id: str
    line_number: int
    source_text: str
    applied_to_existing_line: bool
    automatic_candidate: str
    automatic_scansion: str
    revised_candidate: str
    revised_scansion: str
    note: str


@dataclass(frozen=True)
class StanzaMeterSummary:
    stanza_number: int
    line_numbers: tuple[int, ...]
    primary_candidate: str
    alternate_candidate: str
    analyzable_lines: int
    mean_realized_score: float | None
    regularity: float | None
    line_position_pattern: tuple[str, ...]
    exceptions: tuple[int, ...]


@dataclass(frozen=True)
class RhythmTrajectoryPoint:
    line_number: int
    stanza_number: int
    candidate_meter: str
    realized_score: float | None
    syllable_count: int | None
    realized_beats: int | None
    lexical_stress_density: float | None
    substitution_count: int | None
    caesura_after_syllable: int | None


@dataclass(frozen=True)
class PerformancePoemSummary:
    rhythmic_organization: RhythmicOrganization
    primary_meter: str
    secondary_meter: str
    confidence: MetricalConfidence
    confidence_explanation: str
    analyzable_line_count: int
    line_coverage: float | None
    mean_realized_score: float | None
    primary_meter_line_proportion: float | None
    stress_position_agreement: float | None
    substitution_frequency_per_line: float | None
    syllable_count_variability: float | None
    beat_count_variability: float | None
    candidate_entropy: float | None
    ambiguous_line_proportion: float | None
    generic_composite_pattern: str
    common_substitutions: tuple[tuple[str, int], ...]


@dataclass(frozen=True)
class PerformanceAwareMeterResult:
    analysis_mode: MeterAnalysisMode
    style_profile: MeterStyleDefinition
    poem_summary: PerformancePoemSummary
    stanza_summaries: tuple[StanzaMeterSummary, ...]
    line_results: tuple[PerformanceLineResult, ...]
    scholar_revisions: tuple[ScholarScansionRevision, ...]
    trajectory: tuple[RhythmTrajectoryPoint, ...]
    methodology: tuple[str, ...]
    warnings: tuple[str, ...]

    def __post_init__(self) -> None:
        analyzed = sum(
            line.primary_realization is not None for line in self.line_results
        )
        if analyzed != self.poem_summary.analyzable_line_count:
            raise ValueError(
                "Performance-aware poem and line counts must agree."
            )


def _profile(configuration: MeterConfiguration) -> MeterStyleDefinition:
    base = STYLE_DEFINITIONS[configuration.style_profile]
    if configuration.style_profile is not MeterStyleProfile.CUSTOM:
        return base
    # The custom profile remains explicit through the configuration's visible
    # weighting fields.  It does not infer a style from date or author.
    return replace(
        base,
        substitution_tolerance=min(
            1.0,
            0.45
            + configuration.contextual_fit_weight
            + configuration.phrase_fit_weight,
        ),
        phrase_sensitivity=min(
            1.0,
            0.50 + configuration.phrase_fit_weight * 2,
        ),
        regularity_preference=max(
            0.0,
            1.0 - configuration.poem_consistency_weight * 2,
        ),
    )


def _token_maps(
    module_input: ModuleInput,
) -> tuple[dict[str, TokenRecord], dict[int, tuple[TokenRecord, ...]]]:
    token_by_id = {token.token_id: token for token in module_input.tokens}
    by_line: dict[int, list[TokenRecord]] = defaultdict(list)
    for token in module_input.tokens:
        by_line[token.line_number].append(token)
    return token_by_id, {
        line: tuple(sorted(tokens, key=lambda item: item.token_position))
        for line, tokens in by_line.items()
    }


def _caesurae(
    line: MeterLineResult,
    fit: CandidateMeterFit,
    tokens: tuple[TokenRecord, ...],
) -> tuple[CaesuraEvidence, ...]:
    if not tokens:
        return ()
    lexical = tuple(token for token in tokens if token.is_lexical)
    if len(lexical) < 2:
        return ()
    last_syllable_by_token = {
        operation.token_id: operation.observed_index
        for operation in fit.operations
        if operation.token_id and operation.observed_index is not None
    }
    results = []
    # Use escapes so source-code encoding cannot change the punctuation policy.
    strong_marks = {";", ":", "\u2014", "\u2013", "!", "?"}
    moderate_marks = {",", "-", "\u2026"}
    for index, token in enumerate(tokens):
        if not token.is_punctuation:
            continue
        mark = token.surface_form
        if not any(item in mark for item in strong_marks | moderate_marks):
            continue
        previous = next(
            (
                candidate
                for candidate in reversed(tokens[:index])
                if candidate.is_lexical
            ),
            None,
        )
        following = next(
            (
                candidate
                for candidate in tokens[index + 1 :]
                if candidate.is_lexical
            ),
            None,
        )
        if previous is None or following is None:
            continue
        after = last_syllable_by_token.get(previous.token_id)
        if after is None:
            continue
        strong = any(item in mark for item in strong_marks)
        results.append(
            CaesuraEvidence(
                after_syllable=after + 1,
                punctuation=mark,
                strength="strong" if strong else "moderate",
                confidence=0.86 if strong else 0.68,
                evidence=(
                    "Internal punctuation between retained lexical tokens "
                    "supplies phrase-boundary evidence; it does not mandate a pause."
                ),
            )
        )
    return tuple(results)


def _prominence(
    lexical_stress: str,
    part_of_speech: str,
    *,
    phrase_final: bool,
) -> float:
    if lexical_stress == "1":
        value = 1.0
    elif lexical_stress == "2":
        value = 0.68
    elif part_of_speech in FUNCTION_WORD_POS:
        value = 0.12
    else:
        value = 0.34
    if phrase_final:
        value += 0.08
    return min(value, 1.0)


def _position_fit(prominence: float, strong: bool) -> float:
    if strong:
        # Promotion is possible, so low lexical prominence is evidence against
        # a position but not an automatic zero.
        return 0.42 + 0.58 * prominence
    return 1.0 - 0.58 * prominence


def _adjustment(
    observed: str | None,
    target: str | None,
) -> MetricalAdjustment:
    if observed is None:
        return MetricalAdjustment.OMITTED
    if target is None:
        return MetricalAdjustment.EXTRAMETRICAL
    if target == "1" and observed == "0":
        return MetricalAdjustment.PROMOTION
    if target == "0" and observed in {"1", "2"}:
        return MetricalAdjustment.DEMOTION
    if target == "1" and observed == "2":
        return MetricalAdjustment.SECONDARY_FLEXIBILITY
    return MetricalAdjustment.NONE


def _realized_syllables(
    fit: CandidateMeterFit,
    caesurae: tuple[CaesuraEvidence, ...],
) -> tuple[RealizedSyllable, ...]:
    boundary_indices = {item.after_syllable - 1 for item in caesurae}
    rows = []
    for operation in fit.operations:
        adjustment = _adjustment(
            operation.observed_stress,
            operation.template_stress,
        )
        if operation.template_stress is None:
            position = MetricalPosition.EXTRAMETRICAL
            prominence = (
                _prominence(
                    operation.observed_stress or "0",
                    operation.part_of_speech,
                    phrase_final=(
                        operation.observed_index in boundary_indices
                        if operation.observed_index is not None
                        else False
                    ),
                )
                if operation.observed_stress is not None
                else None
            )
            fit_value = 1.0 - min(operation.cost, 1.0)
            symbol = "(x)"
        elif operation.observed_stress is None:
            position = MetricalPosition.OMITTED
            prominence = None
            fit_value = 1.0 - min(operation.cost, 1.0)
            symbol = "[/]" if operation.template_stress == "1" else "[x]"
        else:
            strong = operation.template_stress == "1"
            position = (
                MetricalPosition.STRONG if strong else MetricalPosition.WEAK
            )
            prominence = _prominence(
                operation.observed_stress,
                operation.part_of_speech,
                phrase_final=operation.observed_index in boundary_indices,
            )
            fit_value = _position_fit(prominence, strong)
            symbol = "/" if strong else "x"
            if adjustment is MetricalAdjustment.PROMOTION:
                symbol += "^"
            elif adjustment is MetricalAdjustment.DEMOTION:
                symbol += "v"
            elif adjustment is MetricalAdjustment.SECONDARY_FLEXIBILITY:
                symbol += "2"
        rows.append(
            RealizedSyllable(
                observed_index=operation.observed_index,
                template_index=operation.template_index,
                token_id=operation.token_id,
                surface_form=operation.surface_form,
                part_of_speech=operation.part_of_speech,
                lexical_stress=operation.observed_stress,
                metrical_position=position,
                adjustment=adjustment,
                contextual_prominence=prominence,
                position_fit=max(0.0, min(1.0, fit_value)),
                symbol=symbol,
                evidence=(
                    "Lexical stress is preserved; the arrow marks a proposed "
                    "contextual metrical adjustment."
                    if adjustment
                    in {
                        MetricalAdjustment.PROMOTION,
                        MetricalAdjustment.DEMOTION,
                    }
                    else "No promotion or demotion is proposed at this position."
                ),
            )
        )
    return tuple(rows)


def _substitutions(
    fit: CandidateMeterFit,
    syllables: tuple[RealizedSyllable, ...],
    *,
    allow_visible_elision: bool,
) -> tuple[MetricalSubstitution, ...]:
    rows: list[MetricalSubstitution] = []

    def add(
        kind: str,
        label: str,
        start: int | None,
        end: int | None,
        evidence: str,
        confidence: float,
    ) -> None:
        rows.append(
            MetricalSubstitution(
                kind=kind,
                label=label,
                start_syllable=start,
                end_syllable=end,
                evidence=evidence,
                confidence=confidence,
            )
        )

    if fit.initial_inversion_count:
        add(
            "initial_inversion",
            "Initial inversion",
            1,
            min(2, len(syllables)),
            "The reversed opening binary foot lowered the configured alignment cost.",
            0.90,
        )
    first = next((row for row in syllables if row.template_index == 0), None)
    if (
        first is not None
        and first.metrical_position is MetricalPosition.OMITTED
        and fit.base_template_stress.startswith("0")
    ):
        add(
            "headless_line",
            "Headless opening",
            None,
            1,
            "The selected path omits the candidate's initial weak position.",
            0.76,
        )
    for row in syllables:
        index = row.observed_index + 1 if row.observed_index is not None else None
        if row.adjustment is MetricalAdjustment.PROMOTION:
            add(
                "promotion",
                "Promotion",
                index,
                index,
                f"{row.surface_form or 'An unstressed syllable'} occupies a proposed strong position.",
                0.72 if row.part_of_speech not in FUNCTION_WORD_POS else 0.58,
            )
        elif row.adjustment is MetricalAdjustment.DEMOTION:
            add(
                "demotion",
                "Demotion",
                index,
                index,
                f"{row.surface_form or 'A stressed syllable'} occupies a proposed weak position.",
                0.72 if row.lexical_stress == "2" else 0.62,
            )
        if (
            allow_visible_elision
            and row.surface_form.casefold()
            in {"o'er", "e'en", "heav'n", "flow'r"}
        ):
            add(
                "visible_orthographic_elision",
                "Visible poetic contraction",
                index,
                index,
                "The preserved spelling visibly marks a conventional contraction; no unmarked elision was imposed.",
                0.90,
            )
    if fit.feminine_ending_count:
        add(
            "feminine_ending",
            "Feminine ending",
            len([row for row in syllables if row.observed_index is not None]),
            len([row for row in syllables if row.observed_index is not None]),
            "The selected path retains an extra final unstressed syllable.",
            0.90,
        )
    if fit.catalectic_count:
        add(
            "catalexis",
            "Catalectic ending",
            None,
            len(fit.base_template_stress),
            "The selected path omits a final candidate position.",
            0.86,
        )
    if fit.spondee_substitution_count:
        add(
            "spondee",
            "Local spondaic movement",
            None,
            None,
            f"{fit.spondee_substitution_count} binary foot/feet align as two lexically stressed syllables.",
            0.72,
        )
    if fit.pyrrhic_substitution_count:
        add(
            "pyrrhic",
            "Local pyrrhic movement",
            None,
            None,
            f"{fit.pyrrhic_substitution_count} binary foot/feet align as two lexically unstressed syllables.",
            0.68,
        )
    if fit.extra_syllable_count > fit.feminine_ending_count:
        add(
            "extrametrical_syllable",
            "Internal or non-feminine extra syllable",
            None,
            None,
            "The alignment retains an observed syllable outside the main candidate positions.",
            0.58,
        )
    if fit.omitted_syllable_count > fit.catalectic_count:
        add(
            "omitted_position",
            "Internal omitted candidate position",
            None,
            None,
            "The alignment leaves an internal candidate position without an observed syllable.",
            0.55,
        )
    return tuple(rows)


def _clashes_and_lapses(
    syllables: tuple[RealizedSyllable, ...],
) -> tuple[tuple[int, ...], tuple[tuple[int, int], ...]]:
    observed = tuple(
        row
        for row in syllables
        if row.observed_index is not None
        and row.contextual_prominence is not None
    )
    clashes = tuple(
        index + 1
        for index, (left, right) in enumerate(
            zip(observed, observed[1:], strict=False)
        )
        if (left.contextual_prominence or 0) >= 0.68
        and (right.contextual_prominence or 0) >= 0.68
    )
    lapses = []
    start = None
    for index, row in enumerate(observed):
        weak = (row.contextual_prominence or 0) < 0.42
        if weak and start is None:
            start = index
        if (not weak or index == len(observed) - 1) and start is not None:
            end = index if weak and index == len(observed) - 1 else index - 1
            if end - start + 1 >= 3:
                lapses.append((start + 1, end + 1))
            start = None
    return clashes, tuple(lapses)


def _display(
    syllables: tuple[RealizedSyllable, ...],
    foot_length: int,
    caesurae: tuple[CaesuraEvidence, ...],
) -> str:
    caesura_after = {item.after_syllable for item in caesurae}
    parts = []
    observed_number = 0
    template_number = 0
    for row in syllables:
        parts.append(row.symbol)
        if row.observed_index is not None:
            observed_number += 1
        if row.template_index is not None:
            template_number += 1
        if observed_number in caesura_after:
            parts.append("||")
        elif (
            row.template_index is not None
            and foot_length
            and template_number % foot_length == 0
            and template_number < max(
                (
                    item.template_index + 1
                    for item in syllables
                    if item.template_index is not None
                ),
                default=0,
            )
        ):
            parts.append("|")
    return " ".join(parts)


def _style_compatibility(
    fit: CandidateMeterFit,
    syllables: tuple[RealizedSyllable, ...],
    profile: MeterStyleDefinition,
) -> float:
    promotions = sum(
        row.adjustment is MetricalAdjustment.PROMOTION for row in syllables
    )
    demotions = sum(
        row.adjustment is MetricalAdjustment.DEMOTION for row in syllables
    )
    positions = max(len(syllables), 1)
    other = (
        fit.extra_syllable_count
        + fit.omitted_syllable_count
        + fit.initial_inversion_count
    )
    penalty = (
        promotions * (1 - profile.promotion_tolerance)
        + demotions * (1 - profile.demotion_tolerance)
        + other * (1 - profile.substitution_tolerance)
    ) / positions
    regularity_bonus = fit.fit_score * profile.regularity_preference * 0.15
    return max(0.0, min(1.0, 1.0 - penalty + regularity_bonus))


def _scores(
    fit: CandidateMeterFit,
    syllables: tuple[RealizedSyllable, ...],
    caesurae: tuple[CaesuraEvidence, ...],
    profile: MeterStyleDefinition,
    configuration: MeterConfiguration,
    *,
    pronunciation_variant_count: int,
    poem_consistency: float,
    stanza_consistency: float,
) -> RealizationScores:
    observed = tuple(
        row for row in syllables if row.observed_index is not None
    )
    contextual = (
        fmean(row.position_fit for row in observed) if observed else 0.0
    )
    length_denominator = max(
        len(fit.base_template_stress),
        len(observed),
        1,
    )
    syllable_fit = max(
        0.0,
        1.0
        - (fit.extra_syllable_count + fit.omitted_syllable_count)
        / length_denominator,
    )
    if caesurae:
        foot_length = len(fit.foot_pattern)
        boundary_matches = sum(
            item.after_syllable % foot_length == 0 for item in caesurae
        )
        phrase_fit = (
            0.68
            + 0.32 * boundary_matches / len(caesurae)
        ) * profile.phrase_sensitivity + 0.5 * (
            1 - profile.phrase_sensitivity
        )
    else:
        phrase_fit = 0.78
    ending_fit = max(
        0.0,
        1.0
        - (
            fit.feminine_ending_count * 0.18
            + fit.catalectic_count * 0.22
            + max(
                fit.extra_syllable_count - fit.feminine_ending_count,
                0,
            )
            * 0.45
            + max(fit.omitted_syllable_count - fit.catalectic_count, 0)
            * 0.48
        ),
    )
    pronunciation = 1.0 if pronunciation_variant_count <= 1 else 0.92
    style_fit = _style_compatibility(fit, syllables, profile)
    adjustment_count = sum(
        row.adjustment
        in {MetricalAdjustment.PROMOTION, MetricalAdjustment.DEMOTION}
        for row in syllables
    )
    substitution_penalty = min(
        1.0,
        (
            adjustment_count
            + fit.extra_syllable_count
            + fit.omitted_syllable_count
        )
        / length_denominator,
    )
    allocated = (
        configuration.contextual_fit_weight
        + configuration.phrase_fit_weight
        + configuration.poem_consistency_weight
        + configuration.stanza_consistency_weight
        + configuration.style_compatibility_weight
    )
    remaining = 1.0 - allocated
    weights = (
        ("candidate_fit", remaining * 0.65),
        ("contextual_fit", configuration.contextual_fit_weight),
        ("syllable_count_fit", remaining * 0.18),
        ("phrase_fit", configuration.phrase_fit_weight),
        ("line_ending_fit", remaining * 0.10),
        ("pronunciation_plausibility", remaining * 0.07),
        ("poem_consistency", configuration.poem_consistency_weight),
        ("stanza_consistency", configuration.stanza_consistency_weight),
        ("style_compatibility", configuration.style_compatibility_weight),
    )
    values = {
        "candidate_fit": fit.fit_score,
        "contextual_fit": contextual,
        "syllable_count_fit": syllable_fit,
        "phrase_fit": phrase_fit,
        "line_ending_fit": ending_fit,
        "pronunciation_plausibility": pronunciation,
        "poem_consistency": poem_consistency,
        "stanza_consistency": stanza_consistency,
        "style_compatibility": style_fit,
    }
    overall = sum(values[label] * weight for label, weight in weights)
    overall -= substitution_penalty * (1 - profile.substitution_tolerance) * 0.08
    return RealizationScores(
        candidate_fit=fit.fit_score,
        contextual_fit=contextual,
        syllable_count_fit=syllable_fit,
        phrase_fit=phrase_fit,
        line_ending_fit=ending_fit,
        pronunciation_plausibility=pronunciation,
        poem_consistency=poem_consistency,
        stanza_consistency=stanza_consistency,
        style_compatibility=style_fit,
        substitution_penalty=substitution_penalty,
        overall=max(0.0, min(1.0, overall)),
        weights=weights,
    )


def _realization(
    line: MeterLineResult,
    fit: CandidateMeterFit,
    tokens: tuple[TokenRecord, ...],
    profile: MeterStyleDefinition,
    configuration: MeterConfiguration,
    *,
    poem_consistency: float,
    stanza_consistency: float,
) -> RealizedScansion:
    caesurae = _caesurae(line, fit, tokens)
    syllables = _realized_syllables(fit, caesurae)
    substitutions = _substitutions(
        fit,
        syllables,
        allow_visible_elision=configuration.allow_visible_poetic_elision,
    )
    clashes, lapses = _clashes_and_lapses(syllables)
    scores = _scores(
        fit,
        syllables,
        caesurae,
        profile,
        configuration,
        pronunciation_variant_count=line.pronunciation_variant_count,
        poem_consistency=poem_consistency,
        stanza_consistency=stanza_consistency,
    )
    return RealizedScansion(
        candidate_label=fit.label,
        pattern=fit.pattern,
        foot_count=fit.foot_count,
        lexical_stress=fit.selected_stress_sequence,
        candidate_template=fit.evaluated_template_stress,
        realized_display=_display(
            syllables,
            len(fit.foot_pattern),
            caesurae,
        ),
        syllables=syllables,
        substitutions=substitutions,
        promotions=sum(
            row.adjustment is MetricalAdjustment.PROMOTION for row in syllables
        ),
        demotions=sum(
            row.adjustment is MetricalAdjustment.DEMOTION for row in syllables
        ),
        stress_clashes=clashes,
        stress_lapses=lapses,
        caesurae=caesurae,
        selected_pronunciation_path=fit.selected_pronunciation_choices,
        scores=scores,
    )


def _candidate_mean_scores(
    lines: tuple[MeterLineResult, ...],
    tokens_by_line: dict[int, tuple[TokenRecord, ...]],
    profile: MeterStyleDefinition,
    configuration: MeterConfiguration,
) -> dict[str, float]:
    values: dict[str, list[float]] = defaultdict(list)
    for line in lines:
        if line.status is not MeterLineStatus.ANALYZED:
            continue
        for fit in line.candidate_fits[: _candidate_limit(configuration)]:
            realized = _realization(
                line,
                fit,
                tokens_by_line.get(line.line_number, ()),
                profile,
                configuration,
                poem_consistency=0.5,
                stanza_consistency=0.5,
            )
            values[fit.label].append(realized.scores.overall)
    return {
        label: fmean(scores)
        for label, scores in values.items()
        if scores
    }


def _candidate_limit(configuration: MeterConfiguration) -> int:
    if configuration.interpretation_depth is MeterInterpretationDepth.SUMMARY:
        return min(configuration.performance_candidate_limit, 3)
    if configuration.interpretation_depth is MeterInterpretationDepth.STANDARD:
        return min(configuration.performance_candidate_limit, 8)
    return configuration.performance_candidate_limit


def _retained_alternative_limit(configuration: MeterConfiguration) -> int:
    if configuration.interpretation_depth is MeterInterpretationDepth.SUMMARY:
        return 0
    if configuration.interpretation_depth is MeterInterpretationDepth.STANDARD:
        return min(configuration.retained_realized_alternatives, 2)
    return configuration.retained_realized_alternatives


def _governing_label(scores: dict[str, float]) -> str:
    return min(scores, key=lambda label: (-scores[label], label)) if scores else ""


def _consistency(candidate: CandidateMeterFit, governing: str) -> float:
    if not governing:
        return 0.5
    if candidate.label == governing:
        return 1.0
    governing_pattern = governing.split(" ", 1)[0].casefold()
    if candidate.pattern.value == governing_pattern:
        return 0.72
    return 0.25


def _line_confidence(
    primary: RealizedScansion,
    alternatives: tuple[RealizedScansion, ...],
) -> tuple[MetricalConfidence, float | None, str]:
    margin = (
        primary.scores.overall - alternatives[0].scores.overall
        if alternatives
        else None
    )
    if margin is not None and margin < 0.025:
        return (
            MetricalConfidence.AMBIGUOUS,
            margin,
            "The two highest realized candidates are within the configured "
            "ambiguity range; both are retained as plausible readings.",
        )
    if primary.scores.overall >= 0.86 and (margin is None or margin >= 0.08):
        return (
            MetricalConfidence.STRONG,
            margin,
            "Candidate, contextual, and consistency components align strongly "
            "under the selected profile.",
        )
    if primary.scores.overall >= 0.74 and (margin is None or margin >= 0.04):
        return (
            MetricalConfidence.MODERATE,
            margin,
            "The primary realized candidate has useful support but still "
            "depends on declared contextual adjustments.",
        )
    return (
        MetricalConfidence.TENTATIVE,
        margin,
        "The closest realized reading is retained as tentative because fit, "
        "context, or separation from alternatives is limited.",
    )


def _entropy(labels: tuple[str, ...]) -> float | None:
    if not labels:
        return None
    counts = Counter(labels)
    total = len(labels)
    if len(counts) == 1:
        return 0.0
    raw = -sum(
        (count / total) * math.log(count / total)
        for count in counts.values()
    )
    return raw / math.log(len(counts))


def _mode_share(values: Iterable[int]) -> tuple[int | None, float | None]:
    materialized = tuple(values)
    if not materialized:
        return None, None
    counts = Counter(materialized)
    maximum = max(counts.values())
    modes = sorted(value for value, count in counts.items() if count == maximum)
    return modes[0], maximum / len(materialized)


def _generic_composite(lines: tuple[PerformanceLineResult, ...]) -> str:
    labels = tuple(
        line.primary_realization.candidate_label
        for line in lines
        if line.primary_realization is not None
    )
    if len(labels) >= 4:
        evens = labels[0::2]
        odds = labels[1::2]
        if (
            len(set(evens)) == 1
            and len(set(odds)) == 1
            and evens[0] != odds[0]
        ):
            return (
                "Recurring alternating sequence: "
                f"{evens[0]} / {odds[0]}"
            )
    return ""


def _stanza_summaries(
    lines: tuple[PerformanceLineResult, ...],
) -> tuple[StanzaMeterSummary, ...]:
    by_stanza: dict[int, list[PerformanceLineResult]] = defaultdict(list)
    for line in lines:
        by_stanza[line.stanza_number].append(line)
    rows = []
    for stanza_number, stanza_lines in sorted(by_stanza.items()):
        analyzed = tuple(
            line for line in stanza_lines if line.primary_realization is not None
        )
        labels = tuple(
            line.primary_realization.candidate_label for line in analyzed
        )
        counts = Counter(labels)
        ranked = sorted(counts, key=lambda label: (-counts[label], label))
        primary = ranked[0] if ranked else ""
        alternative = ranked[1] if len(ranked) > 1 else ""
        scores = tuple(
            line.primary_realization.scores.overall for line in analyzed
        )
        rows.append(
            StanzaMeterSummary(
                stanza_number=stanza_number,
                line_numbers=tuple(line.line_number for line in stanza_lines),
                primary_candidate=primary,
                alternate_candidate=alternative,
                analyzable_lines=len(analyzed),
                mean_realized_score=fmean(scores) if scores else None,
                regularity=(
                    counts[primary] / len(analyzed)
                    if primary and analyzed
                    else None
                ),
                line_position_pattern=labels,
                exceptions=tuple(
                    line.line_number
                    for line in analyzed
                    if line.primary_realization.candidate_label != primary
                ),
            )
        )
    return tuple(rows)


def _poem_summary(
    lines: tuple[PerformanceLineResult, ...],
    profile: MeterStyleDefinition,
) -> PerformancePoemSummary:
    eligible = tuple(
        line
        for line in lines
        if line.status is not MeterLineStatus.NO_LEXICAL_TOKENS
    )
    analyzed = tuple(
        line for line in lines if line.primary_realization is not None
    )
    coverage = len(analyzed) / len(eligible) if eligible else None
    if not analyzed:
        return PerformancePoemSummary(
            rhythmic_organization=RhythmicOrganization.INSUFFICIENT,
            primary_meter="",
            secondary_meter="",
            confidence=MetricalConfidence.INSUFFICIENT,
            confidence_explanation=(
                "No complete line supplied enough pronunciation evidence for "
                "a performance-aware realization."
            ),
            analyzable_line_count=0,
            line_coverage=coverage,
            mean_realized_score=None,
            primary_meter_line_proportion=None,
            stress_position_agreement=None,
            substitution_frequency_per_line=None,
            syllable_count_variability=None,
            beat_count_variability=None,
            candidate_entropy=None,
            ambiguous_line_proportion=None,
            generic_composite_pattern="",
            common_substitutions=(),
        )
    labels = tuple(
        line.primary_realization.candidate_label for line in analyzed
    )
    counts = Counter(labels)
    ranked = sorted(counts, key=lambda label: (-counts[label], label))
    primary = ranked[0]
    secondary = ranked[1] if len(ranked) > 1 else ""
    scores = tuple(
        line.primary_realization.scores.overall for line in analyzed
    )
    position_fits = tuple(
        syllable.position_fit
        for line in analyzed
        for syllable in line.primary_realization.syllables
        if syllable.observed_index is not None
    )
    substitutions = Counter(
        substitution.label
        for line in analyzed
        for substitution in line.primary_realization.substitutions
    )
    syllable_counts = tuple(
        sum(
            syllable.observed_index is not None
            for syllable in line.primary_realization.syllables
        )
        for line in analyzed
    )
    beat_counts = tuple(
        sum(
            syllable.metrical_position is MetricalPosition.STRONG
            for syllable in line.primary_realization.syllables
        )
        for line in analyzed
    )
    _, beat_share = _mode_share(beat_counts)
    _, syllable_share = _mode_share(syllable_counts)
    primary_share = counts[primary] / len(analyzed)
    mean_score = fmean(scores)
    if (
        profile.profile is MeterStyleProfile.FREE_VERSE_CADENTIAL
        and beat_share is not None
        and beat_share >= 0.70
    ):
        organization = RhythmicOrganization.ACCENTUAL
    elif primary_share >= 0.60 and mean_score >= 0.68:
        organization = RhythmicOrganization.ACCENTUAL_SYLLABIC
    elif (
        syllable_share is not None
        and syllable_share >= 0.70
        and primary_share < 0.50
    ):
        organization = RhythmicOrganization.SYLLABIC
    elif sum(score >= 0.72 for score in scores) >= max(2, len(scores) // 3):
        organization = RhythmicOrganization.LOCALLY_METRICAL
    elif len(set(labels)) > 1:
        organization = RhythmicOrganization.MIXED
    else:
        organization = RhythmicOrganization.NO_STABLE_PATTERN
    ambiguous = sum(
        line.confidence is MetricalConfidence.AMBIGUOUS for line in analyzed
    )
    mean_margin = median(
        line.score_margin
        for line in analyzed
        if line.score_margin is not None
    ) if any(line.score_margin is not None for line in analyzed) else None
    if (
        coverage is not None
        and coverage >= 0.80
        and mean_score >= 0.84
        and primary_share >= 0.70
        and (mean_margin is None or mean_margin >= 0.06)
    ):
        confidence = MetricalConfidence.STRONG
    elif (
        coverage is not None
        and coverage >= 0.60
        and mean_score >= 0.72
        and primary_share >= 0.50
    ):
        confidence = MetricalConfidence.MODERATE
    elif ambiguous / len(analyzed) >= 0.40:
        confidence = MetricalConfidence.AMBIGUOUS
    else:
        confidence = MetricalConfidence.TENTATIVE
    return PerformancePoemSummary(
        rhythmic_organization=organization,
        primary_meter=primary,
        secondary_meter=secondary,
        confidence=confidence,
        confidence_explanation=(
            "This rule-based label combines line coverage, realized component "
            "scores, recurrence, and candidate margins. It is not a probability."
        ),
        analyzable_line_count=len(analyzed),
        line_coverage=coverage,
        mean_realized_score=mean_score,
        primary_meter_line_proportion=primary_share,
        stress_position_agreement=(
            fmean(position_fits) if position_fits else None
        ),
        substitution_frequency_per_line=(
            sum(substitutions.values()) / len(analyzed)
        ),
        syllable_count_variability=(
            pstdev(syllable_counts) if len(syllable_counts) > 1 else None
        ),
        beat_count_variability=(
            pstdev(beat_counts) if len(beat_counts) > 1 else None
        ),
        candidate_entropy=_entropy(labels),
        ambiguous_line_proportion=ambiguous / len(analyzed),
        generic_composite_pattern=_generic_composite(lines),
        common_substitutions=tuple(
            sorted(substitutions.items(), key=lambda item: (-item[1], item[0]))
        ),
    )


def _trajectory(
    lines: tuple[PerformanceLineResult, ...],
) -> tuple[RhythmTrajectoryPoint, ...]:
    rows = []
    for line in lines:
        realization = line.primary_realization
        observed = (
            tuple(
                row
                for row in realization.syllables
                if row.observed_index is not None
            )
            if realization is not None
            else ()
        )
        rows.append(
            RhythmTrajectoryPoint(
                line_number=line.line_number,
                stanza_number=line.stanza_number,
                candidate_meter=(
                    realization.candidate_label if realization else ""
                ),
                realized_score=(
                    realization.scores.overall if realization else None
                ),
                syllable_count=len(observed) if realization else None,
                realized_beats=(
                    sum(
                        row.metrical_position is MetricalPosition.STRONG
                        for row in realization.syllables
                    )
                    if realization
                    else None
                ),
                lexical_stress_density=(
                    sum(row.lexical_stress in {"1", "2"} for row in observed)
                    / len(observed)
                    if observed
                    else None
                ),
                substitution_count=(
                    len(realization.substitutions) if realization else None
                ),
                caesura_after_syllable=(
                    realization.caesurae[0].after_syllable
                    if realization and realization.caesurae
                    else None
                ),
            )
        )
    return tuple(rows)


def _scholar_revisions(
    lines: tuple[PerformanceLineResult, ...],
    configuration: MeterConfiguration,
) -> tuple[ScholarScansionRevision, ...]:
    by_number = {line.line_number: line for line in lines}
    rows = []
    for revision in configuration.scholar_revisions:
        line = by_number.get(revision.line_number)
        automatic = line.primary_realization if line is not None else None
        rows.append(
            ScholarScansionRevision(
                line_id=line.line_id if line is not None else "",
                line_number=revision.line_number,
                source_text=line.source_text if line is not None else "",
                applied_to_existing_line=line is not None,
                automatic_candidate=(
                    automatic.candidate_label if automatic is not None else ""
                ),
                automatic_scansion=(
                    automatic.realized_display if automatic is not None else ""
                ),
                revised_candidate=revision.candidate_label,
                revised_scansion=revision.realized_scansion,
                note=revision.note,
            )
        )
    return tuple(rows)


def analyze_performance_aware_meter(
    module_input: ModuleInput,
    line_results: tuple[MeterLineResult, ...],
    configuration: MeterConfiguration,
) -> PerformanceAwareMeterResult:
    """Create explicit realized candidates without changing lexical evidence."""

    profile = _profile(configuration)
    _token_by_id, tokens_by_line = _token_maps(module_input)
    analyzed = tuple(
        line for line in line_results if line.status is MeterLineStatus.ANALYZED
    )
    poem_scores = _candidate_mean_scores(
        analyzed,
        tokens_by_line,
        profile,
        configuration,
    )
    governing = _governing_label(poem_scores)
    stanza_scores = {
        stanza: _candidate_mean_scores(
            tuple(line for line in analyzed if line.stanza_number == stanza),
            tokens_by_line,
            profile,
            configuration,
        )
        for stanza in sorted({line.stanza_number for line in analyzed})
    }
    stanza_governing = {
        stanza: _governing_label(scores)
        for stanza, scores in stanza_scores.items()
    }
    performance_lines = []
    for line in line_results:
        if line.status is not MeterLineStatus.ANALYZED:
            performance_lines.append(
                PerformanceLineResult(
                    line_id=line.line_id,
                    line_number=line.line_number,
                    stanza_number=line.stanza_number,
                    source_text=line.source_text,
                    status=line.status,
                    raw_lexical_stress="",
                    candidate_meter="",
                    primary_realization=None,
                    alternate_realizations=(),
                    confidence=MetricalConfidence.INSUFFICIENT,
                    score_margin=None,
                    explanation=line.reason,
                )
            )
            continue
        candidates = tuple(
            _realization(
                line,
                fit,
                tokens_by_line.get(line.line_number, ()),
                profile,
                configuration,
                poem_consistency=_consistency(fit, governing),
                stanza_consistency=_consistency(
                    fit,
                    stanza_governing.get(line.stanza_number, ""),
                ),
            )
            for fit in line.candidate_fits[
                : _candidate_limit(configuration)
            ]
        )
        ranked = tuple(
            sorted(
                candidates,
                key=lambda item: (
                    -round(item.scores.overall, 12),
                    -round(item.scores.candidate_fit, 12),
                    item.candidate_label,
                ),
            )
        )
        primary = ranked[0]
        confidence_alternatives = ranked[1:2]
        confidence, margin, explanation = _line_confidence(
            primary,
            confidence_alternatives,
        )
        alternatives = ranked[
            1 : 1 + _retained_alternative_limit(configuration)
        ]
        performance_lines.append(
            PerformanceLineResult(
                line_id=line.line_id,
                line_number=line.line_number,
                stanza_number=line.stanza_number,
                source_text=line.source_text,
                status=line.status,
                raw_lexical_stress=primary.lexical_stress,
                candidate_meter=(
                    line.closest_candidate.label
                    if line.closest_candidate is not None
                    else ""
                ),
                primary_realization=primary,
                alternate_realizations=alternatives,
                confidence=confidence,
                score_margin=margin,
                explanation=explanation,
            )
        )
    final_lines = tuple(performance_lines)
    scholar_revisions = _scholar_revisions(final_lines, configuration)
    warnings = [
        (
            "Metrical realization models plausible relationships among lexical "
            "stress, rhythmic expectation, pronunciation, phrasing, and a "
            "declared broad style profile. It does not recover one objectively "
            "mandatory performance or the poet's intention."
        ),
        (
            "Promotion, demotion, caesura, clash, lapse, and substitution labels "
            "are rule-based interpretations. Source lexical stress remains "
            "separate and unchanged."
        ),
    ]
    if not configuration.allow_visible_poetic_elision:
        warnings.append(
            "Conventional poetic elision is disabled. No unmarked written "
            "syllable is silently removed."
        )
    if profile.profile is MeterStyleProfile.CUSTOM:
        warnings.append(
            "The Custom style profile uses the visible configuration weights; "
            "compare it with General English Verse before drawing conclusions."
        )
    if analyzed:
        warnings.append(
            "Performance-aware reranking was bounded to "
            f"{_candidate_limit(configuration)} retained fixed candidate(s) "
            "per analyzable line under the selected interpretation depth."
        )
    missing_revision_lines = tuple(
        item.line_number
        for item in scholar_revisions
        if not item.applied_to_existing_line
    )
    if missing_revision_lines:
        warnings.append(
            "Scholar revisions for absent physical line number(s) were retained "
            "as unapplied audit records: "
            + ", ".join(str(item) for item in missing_revision_lines)
            + "."
        )
    return PerformanceAwareMeterResult(
        analysis_mode=configuration.analysis_mode,
        style_profile=profile,
        poem_summary=_poem_summary(final_lines, profile),
        stanza_summaries=_stanza_summaries(final_lines),
        line_results=final_lines,
        scholar_revisions=scholar_revisions,
        trajectory=_trajectory(final_lines),
        methodology=(
            "Layer 1 preserves CMUdict or scholar-supplied lexical stress.",
            "Layer 2 preserves all Stage 6 fixed candidate-meter alignments.",
            "Layer 3 scores contextual prominence, syllable count, phrasing, line ending, pronunciation path, poem/stanza recurrence, and style compatibility separately.",
            "Layer 4 reranks only the configured bounded candidate set and retains alternate realized readings.",
            "Style profiles change interpretation weights; they never rewrite source stress or silently infer a historical movement.",
            "Named stanza-form classification remains excluded; a stable alternating sequence is reported generically.",
        ),
        warnings=tuple(warnings),
    )
