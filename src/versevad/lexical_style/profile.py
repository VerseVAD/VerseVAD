"""Auditable lexical diversity, word-length, and structural word counts.

The module consumes the shared poetry-preserving processing record. Its primary
lexical-diversity unit is the normalized observed surface form: lemmas are
retained in the audit but never silently substituted for surface forms.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Iterable

from versevad import __version__
from versevad.analysis.statistics import descriptive_statistics
from versevad.core.documents import StructuralUnit
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
from versevad.models import DescriptiveStatistics, TokenRecord


class LexicalStyleModuleError(RuntimeError):
    """Plain-language failure raised before a partial result is published."""


@dataclass(frozen=True)
class LexicalStyleConfiguration:
    """Explicit parameters for length-resistant lexical-diversity measures."""

    mattr_window_size: int = 50
    hdd_sample_size: int = 42
    mtld_threshold: float = 0.72
    short_text_warning_threshold: int = 50
    scenario_id: str = "lexical-style-surface-forms-v1"

    def __post_init__(self) -> None:
        if self.mattr_window_size < 2:
            raise ValueError("The MATTR window must contain at least two tokens.")
        if self.hdd_sample_size < 2:
            raise ValueError("The HD-D sample must contain at least two tokens.")
        if not 0 < self.mtld_threshold < 1:
            raise ValueError("The MTLD threshold must be strictly between 0 and 1.")
        if self.short_text_warning_threshold < 2:
            raise ValueError(
                "The short-text warning threshold must contain at least two tokens."
            )
        if not self.scenario_id.strip():
            raise ValueError("A lexical-style scenario requires a stable ID.")

    @property
    def configuration_id(self) -> str:
        payload = json.dumps(
            asdict(self),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"lexical-style-config-v1:{digest}"


def calculate_mattr(
    forms: Iterable[str],
    *,
    window_size: int,
) -> float | None:
    """Return the mean TTR over every overlapping fixed-length window."""

    observations = tuple(forms)
    if window_size < 2:
        raise ValueError("The MATTR window must contain at least two tokens.")
    if len(observations) < window_size:
        return None

    counts = Counter(observations[:window_size])
    total = len(counts) / window_size
    window_count = len(observations) - window_size + 1
    for start in range(1, window_count):
        leaving = observations[start - 1]
        entering = observations[start + window_size - 1]
        counts[leaving] -= 1
        if counts[leaving] == 0:
            del counts[leaving]
        counts[entering] += 1
        total += len(counts) / window_size
    return total / window_count


def calculate_hdd(
    forms: Iterable[str],
    *,
    sample_size: int,
) -> float | None:
    """Return HD-D as expected distinct types divided by sample size.

    Sampling is without replacement. A text shorter than the configured sample
    remains unavailable instead of being evaluated with a different denominator.
    """

    observations = tuple(forms)
    if sample_size < 2:
        raise ValueError("The HD-D sample must contain at least two tokens.")
    population_size = len(observations)
    if population_size < sample_size:
        return None
    denominator = math.comb(population_size, sample_size)
    expected_types = 0.0
    for frequency in Counter(observations).values():
        absent_count = population_size - frequency
        absent_combinations = (
            math.comb(absent_count, sample_size)
            if absent_count >= sample_size
            else 0
        )
        expected_types += 1 - (absent_combinations / denominator)
    return expected_types / sample_size


def _mtld_direction(
    forms: tuple[str, ...],
    *,
    threshold: float,
) -> float | None:
    factor_count = 0.0
    factor_size = 0
    types: set[str] = set()
    current_ttr = 1.0
    for form in forms:
        factor_size += 1
        types.add(form)
        current_ttr = len(types) / factor_size
        if current_ttr <= threshold:
            factor_count += 1
            factor_size = 0
            types.clear()
            current_ttr = 1.0

    if factor_size:
        partial_factor = (1 - current_ttr) / (1 - threshold)
        factor_count += partial_factor
    if factor_count <= 0:
        return None
    return len(forms) / factor_count


def calculate_mtld(
    forms: Iterable[str],
    *,
    threshold: float,
) -> float | None:
    """Return the mean of forward and reverse MTLD factorization."""

    if not 0 < threshold < 1:
        raise ValueError("The MTLD threshold must be strictly between 0 and 1.")
    observations = tuple(forms)
    if not observations:
        return None
    forward = _mtld_direction(observations, threshold=threshold)
    reverse = _mtld_direction(tuple(reversed(observations)), threshold=threshold)
    if forward is None or reverse is None:
        return None
    return statistics.fmean((forward, reverse))


@dataclass(frozen=True)
class LexicalTokenAudit:
    token_id: str
    token_position: int
    surface_form: str
    normalized_surface_type: str
    lemma: str
    normalized_lemma: str
    part_of_speech: str
    line_number: int
    stanza_number: int
    character_start: int
    character_end: int
    included: bool
    alphabetic_character_count: int | None
    reason: str


@dataclass(frozen=True)
class StructuralWordCountSummary:
    scope: str
    scope_id: str
    ordinal: int
    label: str
    source_text: str
    is_blank: bool
    line_count: int
    word_count: int
    normalized_surface_type_count: int
    surface_type_token_ratio: float | None
    mean_alphabetic_characters_per_token: float | None
    median_alphabetic_characters_per_token: float | None


@dataclass(frozen=True)
class WordLengthDistributionRow:
    alphabetic_character_count: int
    token_count: int
    token_proportion: float


@dataclass(frozen=True)
class LexicalStyleSummary:
    lexical_token_count: int
    normalized_surface_type_count: int
    surface_type_token_ratio: float | None
    mattr: float | None
    mattr_window_size: int
    mattr_window_count: int
    hdd: float | None
    hdd_sample_size: int
    mtld: float | None
    mtld_forward: float | None
    mtld_reverse: float | None
    mtld_threshold: float
    word_length_observation_count: int
    mean_alphabetic_characters_per_token: float | None
    median_alphabetic_characters_per_token: float | None
    population_standard_deviation_alphabetic_characters: float | None
    minimum_alphabetic_characters: float | None
    first_quartile_alphabetic_characters: float | None
    third_quartile_alphabetic_characters: float | None
    maximum_alphabetic_characters: float | None
    physical_line_count: int
    nonblank_line_count: int
    stanza_count: int
    nonblank_line_word_count_statistics: DescriptiveStatistics
    stanza_word_count_statistics: DescriptiveStatistics
    stanza_line_count_statistics: DescriptiveStatistics


@dataclass(frozen=True)
class LexicalStyleAnalysisResult:
    module_result: ModuleResult
    configuration: LexicalStyleConfiguration
    summary: LexicalStyleSummary
    word_length_distribution: tuple[WordLengthDistributionRow, ...]
    line_summaries: tuple[StructuralWordCountSummary, ...]
    stanza_summaries: tuple[StructuralWordCountSummary, ...]
    token_audit: tuple[LexicalTokenAudit, ...]

    def __post_init__(self) -> None:
        included_count = sum(item.included for item in self.token_audit)
        if included_count != self.summary.lexical_token_count:
            raise ValueError(
                "The lexical-style summary must agree with the token audit."
            )
        if sum(item.word_count for item in self.line_summaries) != included_count:
            raise ValueError("Line word counts must sum to the document count.")
        if sum(item.word_count for item in self.stanza_summaries) != included_count:
            raise ValueError("Stanza word counts must sum to the document count.")
        if (
            self.summary.nonblank_line_word_count_statistics.count
            != self.summary.nonblank_line_count
        ):
            raise ValueError(
                "Line word-count statistics must cover every nonblank line."
            )
        if self.summary.stanza_word_count_statistics.count != len(
            self.stanza_summaries
        ):
            raise ValueError("Stanza word-count statistics must cover every stanza.")
        if self.summary.stanza_line_count_statistics.count != len(
            self.stanza_summaries
        ):
            raise ValueError("Stanza line-count statistics must cover every stanza.")
        if (
            sum(item.token_count for item in self.word_length_distribution)
            != self.summary.word_length_observation_count
        ):
            raise ValueError(
                "The word-length distribution must agree with its denominator."
            )


def _normalized_surface_type(token: TokenRecord) -> str:
    return token.normalized_form.strip()


def _alphabetic_character_count(surface_form: str) -> int | None:
    count = sum(character.isalpha() for character in surface_form)
    return count or None


def _token_audit(tokens: tuple[TokenRecord, ...]) -> tuple[LexicalTokenAudit, ...]:
    rows = []
    for token in tokens:
        included = token.is_lexical
        normalized = _normalized_surface_type(token) if included else ""
        character_count = (
            _alphabetic_character_count(token.surface_form) if included else None
        )
        if included:
            reason = (
                "Included as one shared-preprocessing lexical token."
                if normalized and character_count is not None
                else "Included in word counts; a derived value is unavailable."
            )
        elif token.is_numeric:
            reason = "Excluded from lexical word counts because it is numeric."
        else:
            reason = "Excluded from lexical word counts because it is punctuation."
        rows.append(
            LexicalTokenAudit(
                token_id=token.token_id,
                token_position=token.token_position,
                surface_form=token.surface_form,
                normalized_surface_type=normalized,
                lemma=token.lemma,
                normalized_lemma=token.normalized_lemma,
                part_of_speech=token.part_of_speech,
                line_number=token.line_number,
                stanza_number=token.stanza_number,
                character_start=token.character_start,
                character_end=token.character_end,
                included=included,
                alphabetic_character_count=character_count,
                reason=reason,
            )
        )
    return tuple(rows)


def _structural_summary(
    *,
    scope: str,
    unit: StructuralUnit,
    observations: tuple[LexicalTokenAudit, ...],
    line_count: int,
) -> StructuralWordCountSummary:
    forms = tuple(
        item.normalized_surface_type
        for item in observations
        if item.normalized_surface_type
    )
    lengths = tuple(
        item.alphabetic_character_count
        for item in observations
        if item.alphabetic_character_count is not None
    )
    return StructuralWordCountSummary(
        scope=scope,
        scope_id=unit.unit_id,
        ordinal=unit.ordinal,
        label=f"{scope.title()} {unit.ordinal}",
        source_text=unit.content_text,
        is_blank=unit.is_blank if scope == "line" else False,
        line_count=line_count,
        word_count=len(observations),
        normalized_surface_type_count=len(set(forms)),
        surface_type_token_ratio=(len(set(forms)) / len(forms) if forms else None),
        mean_alphabetic_characters_per_token=(
            statistics.fmean(lengths) if lengths else None
        ),
        median_alphabetic_characters_per_token=(
            statistics.median(lengths) if lengths else None
        ),
    )


def _metrics(
    summary: LexicalStyleSummary,
    line_summaries: tuple[StructuralWordCountSummary, ...],
    stanza_summaries: tuple[StructuralWordCountSummary, ...],
) -> tuple[ModuleMetric, ...]:
    metrics = [
        ModuleMetric(
            "lexical_style.lexical_token_count",
            summary.lexical_token_count,
            ResultLayer.DIRECT_OBSERVATION,
            unit="shared-preprocessing lexical tokens",
            denominator="complete preserved text",
        ),
        ModuleMetric(
            "lexical_style.normalized_surface_type_count",
            summary.normalized_surface_type_count,
            ResultLayer.COMPUTED_SUMMARY,
            unit="normalized observed surface types",
            denominator=f"{summary.lexical_token_count} lexical tokens",
        ),
        ModuleMetric(
            "lexical_style.surface_type_token_ratio",
            summary.surface_type_token_ratio,
            ResultLayer.COMPUTED_SUMMARY,
            unit="proportion",
            denominator=f"{summary.lexical_token_count} lexical tokens",
            note="Descriptive only; plain TTR is sensitive to text length.",
        ),
        ModuleMetric(
            "lexical_style.mattr",
            summary.mattr,
            ResultLayer.COMPUTED_SUMMARY,
            unit="mean overlapping-window type-token ratio",
            denominator=(
                f"{summary.mattr_window_count} overlapping windows of "
                f"{summary.mattr_window_size} lexical tokens"
            ),
        ),
        ModuleMetric(
            "lexical_style.hdd",
            summary.hdd,
            ResultLayer.COMPUTED_SUMMARY,
            unit="expected distinct-type proportion",
            denominator=(
                f"without-replacement samples of {summary.hdd_sample_size} "
                "lexical tokens"
            ),
        ),
        ModuleMetric(
            "lexical_style.mtld",
            summary.mtld,
            ResultLayer.COMPUTED_SUMMARY,
            unit="mean lexical-token factor length",
            denominator=(
                f"forward and reverse factorization at TTR "
                f"{summary.mtld_threshold}"
            ),
        ),
        ModuleMetric(
            "lexical_style.mean_word_length",
            summary.mean_alphabetic_characters_per_token,
            ResultLayer.COMPUTED_SUMMARY,
            unit="alphabetic characters per lexical token",
            denominator=(
                f"{summary.word_length_observation_count} lexical-token "
                "observations with alphabetic characters"
            ),
        ),
        ModuleMetric(
            "lexical_style.median_word_length",
            summary.median_alphabetic_characters_per_token,
            ResultLayer.COMPUTED_SUMMARY,
            unit="alphabetic characters per lexical token",
            denominator=(
                f"{summary.word_length_observation_count} lexical-token "
                "observations with alphabetic characters"
            ),
        ),
        ModuleMetric(
            "lexical_style.mean_words_per_nonblank_line",
            summary.nonblank_line_word_count_statistics.mean,
            ResultLayer.COMPUTED_SUMMARY,
            unit="lexical tokens per nonblank physical line",
            denominator=f"{summary.nonblank_line_count} nonblank physical lines",
        ),
        ModuleMetric(
            "lexical_style.population_sd_words_per_nonblank_line",
            (
                summary.nonblank_line_word_count_statistics
                .population_standard_deviation
            ),
            ResultLayer.COMPUTED_SUMMARY,
            unit="lexical tokens per nonblank physical line",
            denominator=f"{summary.nonblank_line_count} nonblank physical lines",
            note="Population, not sample, standard deviation.",
        ),
        ModuleMetric(
            "lexical_style.mean_words_per_stanza",
            summary.stanza_word_count_statistics.mean,
            ResultLayer.COMPUTED_SUMMARY,
            unit="lexical tokens per stanza",
            denominator=f"{summary.stanza_count} stanzas",
        ),
        ModuleMetric(
            "lexical_style.population_sd_words_per_stanza",
            summary.stanza_word_count_statistics.population_standard_deviation,
            ResultLayer.COMPUTED_SUMMARY,
            unit="lexical tokens per stanza",
            denominator=f"{summary.stanza_count} stanzas",
            note="Population, not sample, standard deviation.",
        ),
        ModuleMetric(
            "lexical_style.mean_nonblank_lines_per_stanza",
            summary.stanza_line_count_statistics.mean,
            ResultLayer.COMPUTED_SUMMARY,
            unit="nonblank physical lines per stanza",
            denominator=f"{summary.stanza_count} stanzas",
        ),
        ModuleMetric(
            "lexical_style.population_sd_nonblank_lines_per_stanza",
            summary.stanza_line_count_statistics.population_standard_deviation,
            ResultLayer.COMPUTED_SUMMARY,
            unit="nonblank physical lines per stanza",
            denominator=f"{summary.stanza_count} stanzas",
            note="Population, not sample, standard deviation.",
        ),
    ]
    metrics.extend(
        ModuleMetric(
            "lexical_style.word_count",
            item.word_count,
            ResultLayer.DIRECT_OBSERVATION,
            scope=item.scope,
            scope_id=item.scope_id,
            unit="shared-preprocessing lexical tokens",
            denominator=item.label,
        )
        for item in (*line_summaries, *stanza_summaries)
    )
    return tuple(metrics)


def _warnings(
    summary: LexicalStyleSummary,
    configuration: LexicalStyleConfiguration,
) -> tuple[ModuleWarning, ...]:
    warnings = []
    if summary.lexical_token_count == 0:
        warnings.append(
            ModuleWarning(
                code="lexical_style.no_lexical_tokens",
                message=(
                    "No lexical tokens were available, so diversity and word-length "
                    "summaries remain missing."
                ),
            )
        )
    elif summary.lexical_token_count < configuration.short_text_warning_threshold:
        warnings.append(
            ModuleWarning(
                code="lexical_style.short_text",
                message=(
                    f"The text contains {summary.lexical_token_count} lexical tokens. "
                    "Lexical-diversity estimates for short poems can be unstable and "
                    "should be compared only with matching configurations and similar "
                    "textual contexts."
                ),
                severity=WarningSeverity.INFORMATION,
            )
        )
    if summary.mattr is None and summary.lexical_token_count:
        warnings.append(
            ModuleWarning(
                code="lexical_style.mattr_unavailable",
                message=(
                    f"MATTR requires at least {configuration.mattr_window_size} "
                    "lexical tokens under the current configuration; the value "
                    "remains missing."
                ),
                severity=WarningSeverity.INFORMATION,
            )
        )
    if summary.hdd is None and summary.lexical_token_count:
        warnings.append(
            ModuleWarning(
                code="lexical_style.hdd_unavailable",
                message=(
                    f"HD-D requires at least {configuration.hdd_sample_size} lexical "
                    "tokens under the current configuration; the value remains missing."
                ),
                severity=WarningSeverity.INFORMATION,
            )
        )
    if summary.mtld is None and summary.lexical_token_count:
        warnings.append(
            ModuleWarning(
                code="lexical_style.mtld_unavailable",
                message=(
                    "MTLD factorization did not produce a finite bidirectional "
                    "estimate; the value remains missing."
                ),
                severity=WarningSeverity.INFORMATION,
            )
        )
    if summary.word_length_observation_count < summary.lexical_token_count:
        warnings.append(
            ModuleWarning(
                code="lexical_style.word_length_incomplete",
                message=(
                    "At least one lexical token contained no alphabetic character. "
                    "It remains in word counts but receives no character-length value."
                ),
            )
        )
    return tuple(warnings)


class LexicalStyleModule:
    """Resource-free module over the shared poetry-preserving document."""

    name = "lexical_style"
    version = "1.1.0"

    def validate_resources(self) -> tuple[ResourceStatus, ...]:
        return ()

    def analyze(self, module_input: ModuleInput) -> ModuleResult:
        return self.analyze_detailed(module_input).module_result

    def analyze_detailed(
        self,
        module_input: ModuleInput,
        configuration: LexicalStyleConfiguration | None = None,
    ) -> LexicalStyleAnalysisResult:
        configuration = configuration or LexicalStyleConfiguration()
        poem = module_input.poem_document
        if poem is None:
            raise LexicalStyleModuleError(
                "Lexical-style analysis requires the shared poetry-preserving "
                "processing record."
            )

        audit = _token_audit(module_input.tokens)
        included = tuple(item for item in audit if item.included)
        forms = tuple(
            item.normalized_surface_type
            for item in included
            if item.normalized_surface_type
        )
        lengths = tuple(
            item.alphabetic_character_count
            for item in included
            if item.alphabetic_character_count is not None
        )
        lengths_stats = descriptive_statistics(lengths)
        mattr = calculate_mattr(forms, window_size=configuration.mattr_window_size)
        hdd = calculate_hdd(forms, sample_size=configuration.hdd_sample_size)
        mtld_forward = _mtld_direction(forms, threshold=configuration.mtld_threshold)
        mtld_reverse = _mtld_direction(
            tuple(reversed(forms)),
            threshold=configuration.mtld_threshold,
        )
        mtld = (
            statistics.fmean((mtld_forward, mtld_reverse))
            if mtld_forward is not None and mtld_reverse is not None
            else None
        )

        observations_by_line: dict[int, list[LexicalTokenAudit]] = defaultdict(list)
        observations_by_stanza: dict[int, list[LexicalTokenAudit]] = defaultdict(list)
        for item in included:
            observations_by_line[item.line_number].append(item)
            if item.stanza_number:
                observations_by_stanza[item.stanza_number].append(item)

        line_summaries = tuple(
            _structural_summary(
                scope="line",
                unit=line,
                observations=tuple(observations_by_line[line.ordinal]),
                line_count=0 if line.is_blank else 1,
            )
            for line in poem.lines
        )
        stanza_summaries = tuple(
            _structural_summary(
                scope="stanza",
                unit=stanza,
                observations=tuple(observations_by_stanza[stanza.ordinal]),
                line_count=sum(
                    line.parent_id == stanza.unit_id and not line.is_blank
                    for line in poem.lines
                ),
            )
            for stanza in poem.stanzas
        )
        nonblank_line_counts = tuple(
            item.word_count for item in line_summaries if not item.is_blank
        )
        stanza_counts = tuple(item.word_count for item in stanza_summaries)
        stanza_line_counts = tuple(item.line_count for item in stanza_summaries)
        summary = LexicalStyleSummary(
            lexical_token_count=len(included),
            normalized_surface_type_count=len(set(forms)),
            surface_type_token_ratio=(len(set(forms)) / len(forms) if forms else None),
            mattr=mattr,
            mattr_window_size=configuration.mattr_window_size,
            mattr_window_count=(
                len(forms) - configuration.mattr_window_size + 1
                if len(forms) >= configuration.mattr_window_size
                else 0
            ),
            hdd=hdd,
            hdd_sample_size=configuration.hdd_sample_size,
            mtld=mtld,
            mtld_forward=mtld_forward,
            mtld_reverse=mtld_reverse,
            mtld_threshold=configuration.mtld_threshold,
            word_length_observation_count=len(lengths),
            mean_alphabetic_characters_per_token=lengths_stats.mean,
            median_alphabetic_characters_per_token=lengths_stats.median,
            population_standard_deviation_alphabetic_characters=(
                lengths_stats.population_standard_deviation
            ),
            minimum_alphabetic_characters=lengths_stats.minimum,
            first_quartile_alphabetic_characters=lengths_stats.first_quartile,
            third_quartile_alphabetic_characters=lengths_stats.third_quartile,
            maximum_alphabetic_characters=lengths_stats.maximum,
            physical_line_count=len(line_summaries),
            nonblank_line_count=sum(not item.is_blank for item in line_summaries),
            stanza_count=len(stanza_summaries),
            nonblank_line_word_count_statistics=descriptive_statistics(
                nonblank_line_counts
            ),
            stanza_word_count_statistics=descriptive_statistics(stanza_counts),
            stanza_line_count_statistics=descriptive_statistics(
                stanza_line_counts
            ),
        )
        distribution_counter = Counter(lengths)
        word_length_distribution = tuple(
            WordLengthDistributionRow(
                alphabetic_character_count=length,
                token_count=count,
                token_proportion=count / len(lengths),
            )
            for length, count in sorted(distribution_counter.items())
        )
        normalized_coverage = ModuleCoverage.from_counts(
            coverage_id="lexical_style.normalized_surface_forms",
            eligible_count=len(included),
            matched_count=len(forms),
            unit="shared-preprocessing lexical tokens",
            unmatched_items=tuple(
                item.surface_form
                for item in included
                if not item.normalized_surface_type
            ),
            note=(
                "Lexical diversity uses normalized observed surface forms only; "
                "no lemma is substituted."
            ),
        )
        length_coverage = ModuleCoverage.from_counts(
            coverage_id="lexical_style.alphabetic_word_lengths",
            eligible_count=len(included),
            matched_count=len(lengths),
            unit="shared-preprocessing lexical tokens",
            unmatched_items=tuple(
                item.surface_form
                for item in included
                if item.alphabetic_character_count is None
            ),
            note=(
                "Word length counts Unicode alphabetic characters in each observed "
                "lexical-token surface. Missing lengths are not entered as zero."
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
                "No external lookup. Diversity types use the normalized observed "
                "surface form already recorded by the shared preprocessing pass; "
                "lemmas remain separate audit evidence."
            ),
            inclusion_policy=(
                "Counts include shared-preprocessing lexical tokens and exclude "
                "punctuation and numeric tokens. Word length counts Unicode "
                "alphabetic characters. Physical blank lines remain visible with "
                "word count zero; stanza totals include their member lexical tokens."
            ),
            resources=(),
        )
        identity_payload = json.dumps(
            {
                "text_sha256": module_input.document.text_sha256,
                "configuration_id": configuration.configuration_id,
                "forms": forms,
                "line_counts": [item.word_count for item in line_summaries],
                "stanza_counts": [item.word_count for item in stanza_summaries],
                "stanza_line_counts": [
                    item.line_count for item in stanza_summaries
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        result_id = "lexical-style-result-v2:" + hashlib.sha256(
            identity_payload.encode("utf-8")
        ).hexdigest()[:20]
        module_result = ModuleResult(
            result_id=result_id,
            module_name=self.name,
            module_version=self.version,
            text_id=module_input.document.text_id,
            text_version_id=module_input.document.text_version_id,
            metrics=_metrics(summary, line_summaries, stanza_summaries),
            coverage=(normalized_coverage, length_coverage),
            warnings=_warnings(summary, configuration),
            provenance=provenance,
        )
        return LexicalStyleAnalysisResult(
            module_result=module_result,
            configuration=configuration,
            summary=summary,
            word_length_distribution=word_length_distribution,
            line_summaries=line_summaries,
            stanza_summaries=stanza_summaries,
            token_audit=audit,
        )
