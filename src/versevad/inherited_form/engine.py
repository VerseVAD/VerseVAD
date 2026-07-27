"""Transparent candidate ranking for inherited poetic forms."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from statistics import fmean, pstdev
from typing import Iterable, Sequence

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
from versevad.phonology import PhonologicalAnalysisResult
from versevad.prosody import (
    MeterAnalysisResult,
    MeterLineStatus,
    PronunciationAnalysisResult,
)

from .profiles import (
    FORM_PROFILES,
    FORM_PROFILE_BY_ID,
    PROFILE_REGISTRY_VERSION,
    FormProfile,
    FormRule,
    RuleRole,
)


MODULE_NAME = "inherited_form"
MODULE_VERSION = "1.0.0"
_PHONE_VOWEL = re.compile(r"^[A-Z]+[012]$")


@dataclass(frozen=True)
class InheritedFormConfiguration:
    profile_ids: tuple[str, ...] = tuple(profile.profile_id for profile in FORM_PROFILES)
    suggestion_threshold: float = 0.45
    minimum_evidence_coverage: float = 0.35
    minimum_required_evidence_coverage: float = 0.70
    moderate_confidence_threshold: float = 0.58
    high_confidence_threshold: float = 0.75
    moderate_margin: float = 0.03
    high_margin: float = 0.08
    modified_refrain_floor: float = 0.70
    scenario_id: str = "inherited-form-ten-profile-v1"

    def __post_init__(self) -> None:
        if not self.profile_ids or len(set(self.profile_ids)) != len(self.profile_ids):
            raise ValueError("Select one or more unique inherited-form profiles.")
        unknown = set(self.profile_ids) - set(FORM_PROFILE_BY_ID)
        if unknown:
            raise ValueError(f"Unknown inherited-form profiles: {sorted(unknown)}")
        proportions = (
            self.suggestion_threshold,
            self.minimum_evidence_coverage,
            self.minimum_required_evidence_coverage,
            self.moderate_confidence_threshold,
            self.high_confidence_threshold,
            self.moderate_margin,
            self.high_margin,
            self.modified_refrain_floor,
        )
        if any(not 0 <= value <= 1 for value in proportions):
            raise ValueError("Inherited-form thresholds must be between zero and one.")
        if self.moderate_confidence_threshold > self.high_confidence_threshold:
            raise ValueError("Moderate confidence cannot exceed high confidence.")
        if self.moderate_margin > self.high_margin:
            raise ValueError("Moderate candidate margin cannot exceed high margin.")
        if not self.scenario_id:
            raise ValueError("Inherited-form analysis requires a scenario ID.")

    @property
    def configuration_id(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return "inherited-form-config-v1:" + hashlib.sha256(
            payload.encode("utf-8")
        ).hexdigest()[:16]


@dataclass(frozen=True)
class FormFeatureEvidence:
    rule_id: str
    feature_id: str
    label: str
    role: str
    weight: float
    expected: str
    detected: str
    score: float | None
    evidence_coverage: float | None
    explanation: str
    source_modules: tuple[str, ...]

    @property
    def available(self) -> bool:
        return self.score is not None


@dataclass(frozen=True)
class FormCandidateResult:
    rank: int
    profile_id: str
    profile_name: str
    definition: str
    tooltip: str
    consistency: float | None
    evidence_coverage: float
    required_feature_agreement: float | None
    required_evidence_coverage: float
    required_contradiction_count: int
    margin_over_next: float | None
    confidence: str
    classification: str
    suggested: bool
    narrative: str
    feature_evidence: tuple[FormFeatureEvidence, ...]


@dataclass(frozen=True)
class InheritedFormAnalysisResult:
    module_result: ModuleResult
    configuration: InheritedFormConfiguration
    registry_version: str
    status: str
    best_candidate: FormCandidateResult | None
    nearest_alternative: FormCandidateResult | None
    candidates: tuple[FormCandidateResult, ...]


@dataclass(frozen=True)
class _Observations:
    line_numbers: tuple[int, ...]
    line_texts: tuple[str, ...]
    line_words: tuple[tuple[str, ...], ...]
    line_token_ids: tuple[tuple[str, ...], ...]
    stanza_lengths: tuple[int, ...]
    syllable_counts: tuple[int | None, ...]
    rhyme_labels: tuple[str, ...]

    @property
    def line_count(self) -> int:
        return len(self.line_numbers)

    @property
    def ending_words(self) -> tuple[str, ...]:
        return tuple(words[-1] if words else "" for words in self.line_words)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _count_score(observed: int, expected: int) -> float:
    return _clamp(1 - abs(observed - expected) / max(2, expected * 0.25))


def _sequence_similarity(left: Sequence[str], right: Sequence[str]) -> float:
    if not left or not right:
        return 0.0
    if tuple(left) == tuple(right):
        return 1.0
    return SequenceMatcher(None, tuple(left), tuple(right)).ratio()


def _stanza_similarity(observed: tuple[int, ...], expected: tuple[int, ...]) -> float:
    if observed == expected:
        return 1.0
    if not observed or not expected:
        return 0.0
    count_fit = _count_score(len(observed), len(expected))
    padded = max(len(observed), len(expected))
    differences = sum(
        abs((observed[index] if index < len(observed) else 0) -
            (expected[index] if index < len(expected) else 0))
        for index in range(padded)
    )
    length_fit = _clamp(1 - differences / max(sum(expected), 1))
    return (count_fit + length_fit) / 2


def _scheme_pair_score(
    expected: str,
    observed: tuple[str, ...],
    pair_lookup: dict[tuple[int, int], tuple[str, float | None]],
) -> tuple[float | None, float]:
    if len(observed) < len(expected):
        expected = expected[: len(observed)]
    expected_rhyme_relations: list[float] = []
    expected_difference_relations: list[float] = []
    eligible = 0
    possible = 0
    for first in range(len(expected)):
        for second in range(first + 1, len(expected)):
            possible += 1
            left = observed[first] if first < len(observed) else "?"
            right = observed[second] if second < len(observed) else "?"
            if not left or not right or "?" in (left, right):
                continue
            eligible += 1
            should_rhyme = expected[first] == expected[second]
            observed_rhyme = left == right
            target = (
                expected_rhyme_relations
                if should_rhyme
                else expected_difference_relations
            )
            if should_rhyme:
                if observed_rhyme:
                    target.append(1.0)
                    continue
                relationship, similarity = pair_lookup.get(
                    (first + 1, second + 1), ("", None)
                )
                if relationship in {"perfect", "identical"}:
                    target.append(1.0)
                elif relationship == "slant":
                    target.append(0.45 + 0.45 * (similarity or 0.0))
                elif relationship == "eye":
                    target.append(0.25)
                else:
                    target.append(0.0)
            else:
                target.append(0.0 if observed_rhyme else 1.0)
    category_scores = [
        fmean(items)
        for items in (
            expected_rhyme_relations,
            expected_difference_relations,
        )
        if items
    ]
    return (
        fmean(category_scores) if category_scores else None,
        eligible / possible if possible else 0.0,
    )


def _rhyme_pair_lookup(
    result: PhonologicalAnalysisResult | None,
) -> dict[tuple[int, int], tuple[str, float | None]]:
    if result is None:
        return {}
    lookup = {}
    line_number_by_id = {line.line_id: line.line_number for line in result.line_results}
    for pair in result.pair_results:
        first = line_number_by_id.get(pair.first_line_id, pair.first_line_number)
        second = line_number_by_id.get(pair.second_line_id, pair.second_line_number)
        lookup[(min(first, second), max(first, second))] = (
            pair.relationship,
            pair.similarity_score,
        )
    return lookup


def _feature(
    rule: FormRule,
    observations: _Observations,
    pronunciation: PronunciationAnalysisResult | None,
    meter: MeterAnalysisResult | None,
    phonology: PhonologicalAnalysisResult | None,
    configuration: InheritedFormConfiguration,
) -> FormFeatureEvidence:
    parameters = rule.parameter_map
    feature_id = rule.feature_id
    score: float | None = None
    coverage: float | None = 1.0
    detected = ""
    explanation = ""
    sources = ["shared_poem_document"]

    if feature_id == "line_count_exact":
        expected = int(parameters["count"])
        score = _count_score(observations.line_count, expected)
        detected = f"{observations.line_count} nonblank lines"
        explanation = "Exact line count receives full credit; near counts receive graded credit."
    elif feature_id == "stanza_pattern":
        patterns = tuple(parameters["patterns"])
        score = max(_stanza_similarity(observations.stanza_lengths, item) for item in patterns)
        detected = "/".join(map(str, observations.stanza_lengths)) or "no nonblank stanzas"
        explanation = "Physical stanza layout is supporting evidence; logical architecture is scored elsewhere."
    elif feature_id == "rhyme_scheme":
        sources.append("rhyme_and_phonological_patterns")
        if phonology is None:
            coverage = 0.0
        else:
            schemes = tuple(str(item).replace(" ", "") for item in parameters["schemes"])
            pair_lookup = _rhyme_pair_lookup(phonology)
            results = [
                _scheme_pair_score(scheme, observations.rhyme_labels, pair_lookup)
                for scheme in schemes
            ]
            available = [item for item in results if item[0] is not None]
            if available:
                score, coverage = max(available, key=lambda item: item[0] or 0.0)
            else:
                coverage = 0.0
            detected = phonology.summary.whole_poem_rhyme_scheme or "unavailable"
            explanation = "Expected rhyme relations receive full, slant, eye, or no credit from the graded rhyme evidence."
    elif feature_id == "meter_pattern":
        sources.extend(("pronunciation_prosody_foundation", "candidate_meter_and_rhythmic_regularity"))
        pattern = str(parameters["pattern"])
        foot_count = int(parameters["foot_count"])
        scores = []
        eligible = observations.line_count
        if meter is not None and meter.performance_aware is not None:
            for line in meter.performance_aware.line_results:
                realization = line.primary_realization
                if realization is None:
                    continue
                base = realization.scores.overall
                if realization.pattern.value == pattern and realization.foot_count == foot_count:
                    scores.append(base)
                elif realization.pattern.value == pattern:
                    scores.append(base * 0.45)
                else:
                    scores.append(0.0)
        elif meter is not None:
            for line in meter.line_results:
                if line.status is not MeterLineStatus.ANALYZED:
                    continue
                fit = next(
                    (
                        item.fit_score
                        for item in line.candidate_fits
                        if item.pattern.value == pattern and item.foot_count == foot_count
                    ),
                    None,
                )
                if fit is not None:
                    scores.append(fit)
        score = fmean(scores) if scores else None
        coverage = len(scores) / eligible if eligible else 0.0
        detected = (
            meter.performance_aware.poem_summary.primary_meter
            if meter is not None and meter.performance_aware is not None
            else meter.summary.closest_candidate_label
            if meter is not None
            else "unavailable"
        )
        explanation = "This consumes VerseVAD's existing governing-meter analysis; the form module does not rescan independently."
    elif feature_id == "syllable_pattern":
        sources.append("pronunciation_prosody_foundation")
        expected = tuple(int(item) for item in parameters["counts"])
        supported = [
            (observed, target)
            for observed, target in zip(observations.syllable_counts, expected)
            if observed is not None
        ]
        score = (
            fmean(_clamp(1 - abs(observed - target) / 3) for observed, target in supported)
            if supported
            else None
        )
        coverage = len(supported) / len(expected)
        detected = "/".join("?" if item is None else str(item) for item in observations.syllable_counts[: len(expected)])
        explanation = "Only fully pronunciation-supported line totals are scored; unresolved lines remain missing."
    elif feature_id == "maximum_total_syllables":
        sources.append("pronunciation_prosody_foundation")
        counts = [item for item in observations.syllable_counts if item is not None]
        if len(counts) == observations.line_count and counts:
            maximum = int(parameters["maximum"])
            total = sum(counts)
            score = 1.0 if total <= maximum else _clamp(1 - (total - maximum) / maximum)
            detected = f"{total} resolved syllables"
        else:
            coverage = len(counts) / observations.line_count if observations.line_count else 0.0
        explanation = "Brevity is supporting evidence and requires complete line-level syllable totals."
    elif feature_id == "villanelle_refrains":
        positions = ((1, 6, 12, 18), (3, 9, 15, 19))
        comparisons = []
        possible = 0
        for group in positions:
            if group[0] > observations.line_count:
                continue
            anchor = observations.line_words[group[0] - 1]
            for position in group[1:]:
                possible += 1
                if position <= observations.line_count:
                    comparisons.append(_sequence_similarity(anchor, observations.line_words[position - 1]))
        score = fmean(comparisons) if comparisons else None
        coverage = len(comparisons) / possible if possible else 0.0
        detected = f"{len(comparisons)} of {possible} prescribed refrain comparisons available"
        explanation = "Exact repeated lines receive full credit; lexically modified refrains receive graded credit."
    elif feature_id == "sestina_rotation":
        endings = observations.ending_words
        expected_indices = (0, 1, 2, 3, 4, 5, 5, 0, 4, 1, 3, 2, 2, 5, 3, 0, 1, 4, 4, 2, 1, 5, 0, 3, 3, 4, 0, 2, 5, 1, 1, 3, 5, 4, 2, 0)
        if len(endings) >= 6 and all(endings[:6]):
            seed = endings[:6]
            comparisons = [
                1.0 if endings[index] == seed[seed_index] else 0.0
                for index, seed_index in enumerate(expected_indices)
                if index < len(endings) and endings[index]
            ]
            score = fmean(comparisons) if comparisons else None
            coverage = len(comparisons) / len(expected_indices)
            detected = f"{sum(comparisons):.0f} of {len(comparisons)} available rotation positions agree"
        else:
            coverage = 0.0
        explanation = "Normalized lexical line-ending words are compared with the traditional six-word rotation."
    elif feature_id == "sestina_envoi":
        endings = observations.ending_words
        if len(endings) >= 39 and all(endings[:6]):
            seed = endings[:6]
            final = endings[36:39]
            terminal_score = max(
                fmean(1.0 if actual == seed[index] else 0.0 for actual, index in zip(final, variant))
                for variant in ((4, 2, 0), (0, 2, 4))
            )
            envoi_words = {
                word
                for words in observations.line_words[36:39]
                for word in words
            }
            return_score = len(set(seed) & envoi_words) / len(set(seed))
            score = (terminal_score + return_score) / 2
            detected = f"terminal words {'/'.join(final)}; {len(set(seed) & envoi_words)} of 6 seed words present"
        else:
            coverage = min(1.0, max(0, len(endings) - 36) / 3)
        explanation = "The three terminal end-words and the return of all six seed words are scored separately and averaged."
    elif feature_id == "limerick_length_relation":
        counts = observations.syllable_counts[:5]
        if len(counts) == 5 and all(item is not None for item in counts):
            long_mean = fmean(counts[index] for index in (0, 1, 4) if counts[index] is not None)
            short_mean = fmean(counts[index] for index in (2, 3) if counts[index] is not None)
            score = _clamp((long_mean - short_mean + 1) / max(long_mean * 0.35, 1))
            detected = f"long-line mean {long_mean:.1f}; short-line mean {short_mean:.1f} syllables"
        else:
            coverage = sum(item is not None for item in counts) / 5
        explanation = "Resolved syllable totals test the conventional longer 1/2/5 and shorter 3/4 relationship."
    elif feature_id == "limerick_meter":
        sources.extend(("pronunciation_prosody_foundation", "candidate_meter_and_rhythmic_regularity"))
        if meter is not None and len(meter.line_results) >= 5:
            scores = []
            for index, line in enumerate(meter.line_results[:5]):
                target_feet = 3 if index in (0, 1, 4) else 2
                fit = next(
                    (
                        item.fit_score
                        for item in line.candidate_fits
                        if item.pattern.value == "anapestic" and item.foot_count == target_feet
                    ),
                    None,
                )
                if fit is not None:
                    scores.append(fit)
            score = fmean(scores) if scores else None
            coverage = len(scores) / 5
            detected = f"{len(scores)} of 5 lines had comparable anapestic candidates"
        else:
            coverage = 0.0
        explanation = "The conventional anapestic long/short pattern is read from existing line-level meter candidates."
    elif feature_id == "quatrain_sequence":
        minimum = int(parameters["minimum"])
        if observations.stanza_lengths:
            quatrains = sum(length == 4 for length in observations.stanza_lengths)
            score = min(1.0, quatrains / minimum) * (
                quatrains / len(observations.stanza_lengths)
            )
            detected = f"{quatrains} quatrains across {len(observations.stanza_lengths)} printed stanzas"
        explanation = "Printed quatrains are counted directly."
    elif feature_id == "pantoum_repetition":
        stanzas = _line_ranges(observations.stanza_lengths)
        comparisons = []
        for current, following in zip(stanzas, stanzas[1:]):
            if len(current) >= 4 and len(following) >= 3:
                comparisons.extend(
                    (
                        _sequence_similarity(observations.line_words[current[1]], observations.line_words[following[0]]),
                        _sequence_similarity(observations.line_words[current[3]], observations.line_words[following[2]]),
                    )
                )
        score = fmean(comparisons) if comparisons else None
        coverage = len(comparisons) / max(2 * (len(stanzas) - 1), 1)
        detected = f"{len(comparisons)} interstanza repetition comparisons"
        explanation = "Successive 2→1 and 4→3 line repetitions receive exact or graded lexical credit."
    elif feature_id == "pantoum_closure":
        stanzas = _line_ranges(observations.stanza_lengths)
        if len(stanzas) >= 2 and len(stanzas[0]) >= 3 and len(stanzas[-1]) >= 4:
            opening = stanzas[0]
            final = stanzas[-1]
            score = max(
                fmean((
                    _sequence_similarity(observations.line_words[opening[0]], observations.line_words[final[3]]),
                    _sequence_similarity(observations.line_words[opening[2]], observations.line_words[final[1]]),
                )),
                fmean((
                    _sequence_similarity(observations.line_words[opening[0]], observations.line_words[final[1]]),
                    _sequence_similarity(observations.line_words[opening[2]], observations.line_words[final[3]]),
                )),
            )
            detected = "opening and final-stanza lines compared"
        explanation = "Traditional circular closure is supporting, not required, evidence."
    elif feature_id == "terza_stanzas":
        lengths = observations.stanza_lengths
        if lengths:
            core = lengths[:-1] if lengths[-1] in (1, 2) else lengths
            terminal_ok = lengths[-1] in (1, 2, 3)
            score = (sum(item == 3 for item in core) / max(len(core), 1)) * (1.0 if terminal_ok else 0.8)
            detected = "/".join(map(str, lengths))
        explanation = "Physical tercets receive full credit; a terminal line or couplet is allowed."
    elif feature_id == "terza_rhyme":
        sources.append("rhyme_and_phonological_patterns")
        if phonology is not None and observations.line_count >= 6:
            letters = []
            current = ord("A")
            stanzas = observations.line_count // 3
            for index in range(stanzas):
                a = chr(current + index)
                b = chr(current + index + 1)
                letters.extend((a, b, a))
            expected = "".join(letters)
            score, coverage = _scheme_pair_score(
                expected,
                observations.rhyme_labels,
                _rhyme_pair_lookup(phonology),
            )
            detected = phonology.summary.whole_poem_rhyme_scheme
        else:
            coverage = 0.0
        explanation = "The ABA BCB CDC equivalence chain uses VerseVAD's graded rhyme evidence."
    elif feature_id == "line_length_uniformity":
        counts = [item for item in observations.syllable_counts if item is not None]
        if len(counts) >= 3 and fmean(counts) > 0:
            coefficient = pstdev(counts) / fmean(counts)
            score = _clamp(1 - coefficient / 0.35)
            coverage = len(counts) / observations.line_count
            detected = f"syllable-count coefficient of variation {coefficient:.3f}"
        else:
            coverage = len(counts) / observations.line_count if observations.line_count else 0.0
        explanation = "Resolved syllable-count variability supplies supporting line-length evidence."
    elif feature_id == "ghazal_architecture":
        minimum = int(parameters["minimum"])
        maximum = int(parameters["maximum"])
        lengths = observations.stanza_lengths
        if lengths:
            couplets = sum(item == 2 for item in lengths)
            stanza_fit = couplets / len(lengths)
            range_fit = 1.0 if minimum <= couplets <= maximum else _clamp(1 - min(abs(couplets - minimum), abs(couplets - maximum)) / minimum)
            score = (stanza_fit + range_fit) / 2
            detected = f"{couplets} printed couplets across {len(lengths)} stanzas"
        explanation = "The profile tests five to fifteen physically printed couplets."
    elif feature_id == "ghazal_radif_qafia":
        sources.append("pronunciation_prosody_foundation")
        score, coverage, detected = _ghazal_score(observations, pronunciation)
        explanation = "Repeated lexical suffixes identify a radif candidate; the preceding resolved pronunciation supplies qafia-rhyme evidence."
    else:  # pragma: no cover - registry validation should make this unreachable
        raise ValueError(f"Unsupported inherited-form feature: {feature_id}")

    return FormFeatureEvidence(
        rule_id=rule.rule_id,
        feature_id=feature_id,
        label=rule.label,
        role=rule.role.value,
        weight=rule.weight,
        expected=rule.expected,
        detected=detected or "unavailable",
        score=None if score is None else _clamp(score),
        evidence_coverage=None if coverage is None else _clamp(coverage),
        explanation=explanation,
        source_modules=tuple(dict.fromkeys(sources)),
    )


def _line_ranges(lengths: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    start = 0
    rows = []
    for length in lengths:
        rows.append(tuple(range(start, start + length)))
        start += length
    return tuple(rows)


def _pronunciation_rime(phones: str | None) -> tuple[str, ...]:
    sequence = tuple((phones or "").split())
    if not sequence:
        return ()
    primary = [index for index, phone in enumerate(sequence) if phone.endswith("1")]
    vowels = [index for index, phone in enumerate(sequence) if _PHONE_VOWEL.match(phone)]
    start = primary[-1] if primary else vowels[-1] if vowels else -1
    return sequence[start:] if start >= 0 else ()


def _ghazal_score(
    observations: _Observations,
    pronunciation: PronunciationAnalysisResult | None,
) -> tuple[float | None, float, str]:
    targets = [0, 1, *range(3, observations.line_count, 2)]
    targets = [index for index in targets if index < observations.line_count]
    if len(targets) < 4:
        return None, len(targets) / 6, "too few candidate radif positions"
    first_words = observations.line_words[targets[0]]
    candidates = [
        first_words[-length:]
        for length in range(1, min(4, len(first_words)) + 1)
    ]
    best_suffix: tuple[str, ...] = ()
    best_support = 0.0
    for suffix in candidates:
        support = sum(
            tuple(observations.line_words[index][-len(suffix):]) == tuple(suffix)
            for index in targets
            if len(observations.line_words[index]) >= len(suffix)
        ) / len(targets)
        adjusted = support + 0.01 * len(suffix)
        if adjusted > best_support:
            best_support = adjusted
            best_suffix = tuple(suffix)
    radif_support = max(0.0, best_support - 0.01 * len(best_suffix))
    if not best_suffix or radif_support < 0.5:
        return radif_support, 1.0, "no repeated radif candidate on most prescribed lines"
    pronunciation_by_token = (
        {item.token_id: item for item in pronunciation.token_results}
        if pronunciation is not None
        else {}
    )
    qafia_rimes = []
    for line_index in targets:
        words = observations.line_words[line_index]
        token_ids = observations.line_token_ids[line_index]
        if (
            len(words) <= len(best_suffix)
            or tuple(words[-len(best_suffix):]) != best_suffix
        ):
            continue
        token_index = len(token_ids) - len(best_suffix) - 1
        if token_index < 0:
            continue
        token = pronunciation_by_token.get(token_ids[token_index])
        rime = _pronunciation_rime(token.resolved_phones if token is not None else None)
        if rime:
            qafia_rimes.append(rime)
    qafia_score = None
    if len(qafia_rimes) >= 2:
        anchor = qafia_rimes[0]
        qafia_score = fmean(
            1.0 if item == anchor else _sequence_similarity(anchor, item) * 0.6
            for item in qafia_rimes[1:]
        )
    score = radif_support if qafia_score is None else 0.65 * radif_support + 0.35 * qafia_score
    qafia_coverage = len(qafia_rimes) / len(targets)
    coverage = 0.65 + 0.35 * qafia_coverage
    return (
        score,
        coverage,
        f"radif candidate “{' '.join(best_suffix)}” on {radif_support:.0%} of prescribed lines; "
        f"{len(qafia_rimes)} qafia pronunciations resolved",
    )


def _observations(
    module_input: ModuleInput,
    pronunciation: PronunciationAnalysisResult | None,
    phonology: PhonologicalAnalysisResult | None,
) -> _Observations:
    poem = module_input.poem_document
    if poem is None:
        raise ValueError("Inherited-form analysis requires the shared poem document.")
    lines = tuple(line for line in poem.lines if not line.is_blank)
    line_numbers = tuple(line.ordinal for line in lines)
    line_number_set = set(line_numbers)
    tokens_by_line: dict[int, list] = {number: [] for number in line_numbers}
    for token in module_input.tokens:
        if token.line_number in line_number_set and token.is_lexical:
            tokens_by_line[token.line_number].append(token)
    line_words = tuple(
        tuple(token.normalized_form for token in tokens_by_line[number])
        for number in line_numbers
    )
    line_token_ids = tuple(
        tuple(token.token_id for token in tokens_by_line[number])
        for number in line_numbers
    )
    stanza_lengths = []
    for stanza in poem.stanzas:
        count = sum(
            not line.is_blank and line.parent_id == stanza.unit_id
            for line in poem.lines
        )
        if count:
            stanza_lengths.append(count)
    syllables = {}
    if pronunciation is not None:
        syllables = {
            line.line_number: line.syllable_count if line.is_complete else None
            for line in pronunciation.line_summaries
        }
    rhyme = {}
    if phonology is not None:
        rhyme = {
            line.line_number: line.poem_scheme_label or "?"
            for line in phonology.line_results
        }
    return _Observations(
        line_numbers=line_numbers,
        line_texts=tuple(line.content_text for line in lines),
        line_words=line_words,
        line_token_ids=line_token_ids,
        stanza_lengths=tuple(stanza_lengths),
        syllable_counts=tuple(syllables.get(number) for number in line_numbers),
        rhyme_labels=tuple(rhyme.get(number, "?") for number in line_numbers),
    )


def _classification(consistency: float | None, required: float | None) -> str:
    if consistency is None:
        return "No inherited-form match"
    if consistency >= 0.95 and (required is None or required >= 0.95):
        return "Strict"
    if consistency >= 0.82:
        return "Strongly conforming"
    if consistency >= 0.68:
        return "Modified"
    if consistency >= 0.55:
        return "Form-derived"
    if consistency >= 0.45:
        return "Suggestive resemblance"
    return "No inherited-form match"


def _tooltip(profile: FormProfile, evidence: Sequence[FormFeatureEvidence]) -> str:
    available = [item for item in evidence if item.score is not None]
    strongest = sorted(available, key=lambda item: item.weight * (item.score or 0), reverse=True)[:2]
    departures = sorted(available, key=lambda item: item.score if item.score is not None else 1)[:2]
    text = profile.tooltip_definition
    if strongest:
        text += " Agreement: " + "; ".join(f"{item.label} ({item.detected})" for item in strongest) + "."
    if departures and any((item.score or 0) < 0.8 for item in departures):
        text += " Departures: " + "; ".join(
            f"{item.label} ({item.detected})"
            for item in departures
            if (item.score or 0) < 0.8
        ) + "."
    return text


class InheritedFormEngine:
    name = MODULE_NAME
    version = MODULE_VERSION

    @staticmethod
    def validate_resources() -> tuple:
        return ()

    def analyze(
        self,
        module_input: ModuleInput,
        pronunciation: PronunciationAnalysisResult | None,
        meter: MeterAnalysisResult | None,
        phonology: PhonologicalAnalysisResult | None,
        configuration: InheritedFormConfiguration = InheritedFormConfiguration(),
    ) -> InheritedFormAnalysisResult:
        observations = _observations(module_input, pronunciation, phonology)
        raw = []
        for profile_id in configuration.profile_ids:
            profile = FORM_PROFILE_BY_ID[profile_id]
            evidence = tuple(
                _feature(
                    rule,
                    observations,
                    pronunciation,
                    meter,
                    phonology,
                    configuration,
                )
                for rule in profile.rules
            )
            available = [item for item in evidence if item.score is not None]
            effective_weights = {
                item.rule_id: item.weight * (
                    item.evidence_coverage
                    if item.evidence_coverage is not None
                    else 1.0
                )
                for item in available
            }
            available_weight = sum(effective_weights.values())
            total_weight = sum(item.weight for item in evidence)
            consistency = (
                sum(
                    effective_weights[item.rule_id] * float(item.score)
                    for item in available
                )
                / available_weight
                if available_weight
                else None
            )
            required = [
                item
                for item in available
                if item.role == RuleRole.REQUIRED.value
            ]
            required_potential_weight = sum(
                item.weight
                for item in evidence
                if item.role == RuleRole.REQUIRED.value
            )
            required_evidence_coverage = (
                sum(effective_weights[item.rule_id] for item in required)
                / required_potential_weight
                if required_potential_weight
                else 1.0
            )
            required_agreement = (
                sum(
                    effective_weights[item.rule_id] * float(item.score)
                    for item in required
                )
                / sum(effective_weights[item.rule_id] for item in required)
                if required
                else None
            )
            contradictions = sum((item.score or 0) < 0.2 for item in required)
            raw.append(
                (
                    profile,
                    evidence,
                    consistency,
                    available_weight / total_weight,
                    required_agreement,
                    required_evidence_coverage,
                    contradictions,
                )
            )
        raw.sort(
            key=lambda item: (
                -(item[2] if item[2] is not None else -1),
                -item[3],
                item[0].profile_id,
            )
        )
        candidates = []
        for index, (
            profile,
            evidence,
            consistency,
            coverage,
            required,
            required_coverage,
            contradictions,
        ) in enumerate(raw):
            next_score = raw[index + 1][2] if index + 1 < len(raw) else None
            margin = (
                consistency - next_score
                if consistency is not None and next_score is not None
                else None
            )
            suggested = (
                consistency is not None
                and consistency >= configuration.suggestion_threshold
                and coverage >= configuration.minimum_evidence_coverage
                and required_coverage
                >= configuration.minimum_required_evidence_coverage
                and contradictions == 0
            )
            if (
                suggested
                and consistency >= configuration.high_confidence_threshold
                and coverage >= 0.75
                and (margin or 0) >= configuration.high_margin
            ):
                confidence = "high"
            elif (
                suggested
                and consistency >= configuration.moderate_confidence_threshold
                and coverage >= 0.50
                and (margin or 0) >= configuration.moderate_margin
            ):
                confidence = "moderate"
            else:
                confidence = "low"
            classification = _classification(consistency, required)
            if not suggested:
                classification = "No inherited-form match"
            narrative = (
                f"{classification} {profile.name} candidate. "
                f"Observed consistency is {consistency:.1%} across {coverage:.1%} "
                "of the profile's weighted evidence."
                if consistency is not None
                else f"{profile.name} could not be scored from the available evidence."
            )
            candidates.append(
                FormCandidateResult(
                    rank=index + 1,
                    profile_id=profile.profile_id,
                    profile_name=profile.name,
                    definition=profile.definition,
                    tooltip=_tooltip(profile, evidence),
                    consistency=consistency,
                    evidence_coverage=coverage,
                    required_feature_agreement=required,
                    required_evidence_coverage=required_coverage,
                    required_contradiction_count=contradictions,
                    margin_over_next=margin,
                    confidence=confidence,
                    classification=classification,
                    suggested=suggested,
                    narrative=narrative,
                    feature_evidence=evidence,
                )
            )
        best = candidates[0] if candidates and candidates[0].suggested else None
        alternative = candidates[1] if best is not None and len(candidates) > 1 else None
        warnings = []
        if best is None:
            warnings.append(
                ModuleWarning(
                    code="inherited_form_no_suggestion",
                    message=(
                        "No candidate met the configured suggestion and evidence "
                        "thresholds. The ranked evidence remains available for inspection."
                    ),
                    severity=WarningSeverity.INFORMATION,
                )
            )
        elif best.confidence == "low":
            warnings.append(
                ModuleWarning(
                    code="inherited_form_low_confidence",
                    message=(
                        f"{best.profile_name} is a low-confidence potential match; "
                        "inspect coverage, required features, and the nearest alternative."
                    ),
                )
            )
        module_result = self._module_result(
            module_input,
            configuration,
            tuple(candidates),
            best,
            alternative,
            tuple(warnings),
        )
        return InheritedFormAnalysisResult(
            module_result=module_result,
            configuration=configuration,
            registry_version=PROFILE_REGISTRY_VERSION,
            status="suggested" if best is not None else "no_match",
            best_candidate=best,
            nearest_alternative=alternative,
            candidates=tuple(candidates),
        )

    @staticmethod
    def _module_result(
        module_input: ModuleInput,
        configuration: InheritedFormConfiguration,
        candidates: tuple[FormCandidateResult, ...],
        best: FormCandidateResult | None,
        alternative: FormCandidateResult | None,
        warnings: tuple[ModuleWarning, ...],
    ) -> ModuleResult:
        metrics = [
            ModuleMetric(
                "inherited_form.result_status",
                "suggested" if best is not None else "no_match",
                ResultLayer.INTERPRETATION,
                unit="status label",
                denominator="ten enabled inherited-form profiles",
                note="A suggestion is a rule-based potential match, not a declaration of genre identity.",
            ),
            ModuleMetric(
                "inherited_form.best_candidate_id",
                best.profile_id if best else None,
                ResultLayer.INTERPRETATION,
                unit="profile ID",
                denominator="ranked enabled profiles",
            ),
            ModuleMetric(
                "inherited_form.best_candidate_name",
                best.profile_name if best else None,
                ResultLayer.INTERPRETATION,
                unit="display label",
                denominator="ranked enabled profiles",
            ),
            ModuleMetric(
                "inherited_form.best_consistency",
                best.consistency if best else None,
                ResultLayer.COMPUTED_SUMMARY,
                unit="proportion",
                denominator="available weighted profile evidence",
            ),
            ModuleMetric(
                "inherited_form.best_evidence_coverage",
                best.evidence_coverage if best else candidates[0].evidence_coverage,
                ResultLayer.COMPUTED_SUMMARY,
                unit="proportion",
                denominator="potential profile weight",
            ),
            ModuleMetric(
                "inherited_form.confidence_label",
                best.confidence if best else "none",
                ResultLayer.INTERPRETATION,
                unit="rule-based evidence label",
                denominator="consistency, coverage, required-feature contradictions, and candidate margin",
                note="Confidence is not a probability.",
            ),
            ModuleMetric(
                "inherited_form.classification",
                best.classification if best else "No inherited-form match",
                ResultLayer.INTERPRETATION,
                unit="conformity label",
                denominator="documented consistency thresholds",
            ),
            ModuleMetric(
                "inherited_form.nearest_alternative_id",
                alternative.profile_id if alternative else None,
                ResultLayer.COMPUTED_SUMMARY,
                unit="profile ID",
                denominator="second-ranked enabled profile",
            ),
            ModuleMetric(
                "inherited_form.nearest_alternative_name",
                alternative.profile_name if alternative else None,
                ResultLayer.COMPUTED_SUMMARY,
                unit="display label",
                denominator="second-ranked enabled profile",
            ),
            ModuleMetric(
                "inherited_form.candidate_margin",
                best.margin_over_next if best else None,
                ResultLayer.COMPUTED_SUMMARY,
                unit="consistency-index difference",
                denominator="best minus second-ranked candidate",
            ),
        ]
        for candidate in candidates:
            scope_id = candidate.profile_id
            metrics.extend(
                (
                    ModuleMetric(
                        "inherited_form.candidate_name",
                        candidate.profile_name,
                        ResultLayer.INTERPRETATION,
                        scope="candidate",
                        scope_id=scope_id,
                        unit="display label",
                        denominator="one versioned form profile",
                    ),
                    ModuleMetric(
                        "inherited_form.candidate_rank",
                        candidate.rank,
                        ResultLayer.COMPUTED_SUMMARY,
                        scope="candidate",
                        scope_id=scope_id,
                        unit="rank",
                        denominator=f"{len(candidates)} enabled profiles",
                    ),
                    ModuleMetric(
                        "inherited_form.candidate_consistency",
                        candidate.consistency,
                        ResultLayer.COMPUTED_SUMMARY,
                        scope="candidate",
                        scope_id=scope_id,
                        unit="proportion",
                        denominator="available weighted profile evidence",
                    ),
                    ModuleMetric(
                        "inherited_form.candidate_evidence_coverage",
                        candidate.evidence_coverage,
                        ResultLayer.COMPUTED_SUMMARY,
                        scope="candidate",
                        scope_id=scope_id,
                        unit="proportion",
                        denominator="potential profile weight",
                    ),
                    ModuleMetric(
                        "inherited_form.candidate_classification",
                        candidate.classification,
                        ResultLayer.INTERPRETATION,
                        scope="candidate",
                        scope_id=scope_id,
                        unit="conformity label",
                        denominator="documented consistency thresholds",
                    ),
                )
            )
        available_rules = sum(
            evidence.score is not None
            for candidate in candidates
            for evidence in candidate.feature_evidence
        )
        total_rules = sum(len(candidate.feature_evidence) for candidate in candidates)
        coverage = (
            ModuleCoverage.from_counts(
                coverage_id="inherited_form.rule_evidence",
                eligible_count=total_rules,
                matched_count=available_rules,
                unit="profile rules",
                note="Unavailable dependent evidence remains missing rather than receiving a zero score.",
            ),
        )
        provenance = ModuleProvenance(
            software_version=__version__,
            source_text_sha256=module_input.document.text_sha256,
            preprocessing_recipe=module_input.preprocessing.recipe_id,
            pipeline_name="VerseVAD inherited-form candidate ranking",
            pipeline_version=MODULE_VERSION,
            configuration_id=configuration.configuration_id,
            scenario_id=configuration.scenario_id,
            lookup_policy="Versioned rule profiles with graded structural evidence.",
            inclusion_policy=(
                "Nonblank physical lines; missing pronunciation, meter, or rhyme "
                "evidence lowers coverage and is never converted to mismatch."
            ),
            resources=(),
        )
        signature = "|".join(
            (
                module_input.document.text_version_id,
                configuration.configuration_id,
                *(candidate.profile_id + ":" + str(candidate.consistency) for candidate in candidates),
            )
        )
        return ModuleResult(
            result_id="inherited-form:" + hashlib.sha256(signature.encode("utf-8")).hexdigest(),
            module_name=MODULE_NAME,
            module_version=MODULE_VERSION,
            text_id=module_input.document.text_id,
            text_version_id=module_input.document.text_version_id,
            metrics=tuple(metrics),
            coverage=coverage,
            warnings=warnings,
            provenance=provenance,
        )


__all__ = [
    "InheritedFormAnalysisResult",
    "InheritedFormConfiguration",
    "InheritedFormEngine",
    "FormCandidateResult",
    "FormFeatureEvidence",
    "MODULE_NAME",
    "MODULE_VERSION",
]
