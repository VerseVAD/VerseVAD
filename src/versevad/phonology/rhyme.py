"""Auditable rhyme and recurring phonological-pattern analysis.

The module consumes the exact local CMUdict evidence retained by Stage 5. It
does not predict pronunciations, alter the pronunciation audit, or turn graded
similarity into a claim that two words definitively rhyme in performance.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from itertools import combinations, product
from typing import Callable, Iterable, TypeVar

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


_STRESSED_PHONE = re.compile(r"^(?P<base>[A-Z]+)(?P<stress>[012])$")
_ORTHOGRAPHIC_VOWELS = frozenset("aeiouy")
_VOWEL_FAMILIES = {
    "AA": "low_back",
    "AO": "low_back",
    "AH": "central",
    "AX": "central",
    "ER": "rhotic",
    "AE": "low_front",
    "EH": "mid_front",
    "EY": "mid_front",
    "IH": "high_front",
    "IY": "high_front",
    "UH": "high_back",
    "UW": "high_back",
    "OW": "mid_back",
    "AY": "diphthong",
    "AW": "diphthong",
    "OY": "diphthong",
}

_T = TypeVar("_T")


class PhonologicalModuleError(RuntimeError):
    """Plain-language failure raised before a partial result is published."""


class RhymeEndingStatus(StrEnum):
    ANALYZED = "analyzed"
    AMBIGUOUS_PRONUNCIATION = "ambiguous_pronunciation"
    UNMATCHED_PRONUNCIATION = "unmatched_pronunciation"
    SOURCE_WITHOUT_MARKED_VOWEL = "source_without_marked_vowel"
    NO_LEXICAL_TOKENS = "no_lexical_tokens"


@dataclass(frozen=True)
class PhonologicalConfiguration:
    """Transparent thresholds and weights for Stage 7."""

    slant_rhyme_threshold: float = 0.68
    stressed_vowel_weight: float = 0.35
    final_consonant_weight: float = 0.25
    phoneme_edit_weight: float = 0.25
    stress_alignment_weight: float = 0.10
    syllable_count_weight: float = 0.05
    related_vowel_family_score: float = 0.60
    minimum_sound_repetitions: int = 2
    minimum_eye_rime_characters: int = 2
    minimum_analyzable_endings: int = 2
    low_ending_coverage_warning_threshold: float = 0.70
    maximum_pair_evaluations: int = 10_000
    scenario_id: str = "rhyme-phonology-cmudict-v1"

    def __post_init__(self) -> None:
        proportions = {
            "slant rhyme threshold": self.slant_rhyme_threshold,
            "related vowel-family score": self.related_vowel_family_score,
            "low ending coverage threshold": (
                self.low_ending_coverage_warning_threshold
            ),
        }
        outside = [
            label for label, value in proportions.items() if not 0 <= value <= 1
        ]
        if outside:
            raise ValueError(
                "Phonological thresholds must be between 0 and 1: "
                + ", ".join(outside)
                + "."
            )
        weights = (
            self.stressed_vowel_weight,
            self.final_consonant_weight,
            self.phoneme_edit_weight,
            self.stress_alignment_weight,
            self.syllable_count_weight,
        )
        if any(value < 0 for value in weights):
            raise ValueError("Phonological similarity weights cannot be negative.")
        if not abs(sum(weights) - 1.0) < 1e-9:
            raise ValueError("Phonological similarity weights must sum to 1.")
        if self.minimum_sound_repetitions < 2:
            raise ValueError("A repeated sound must occur at least twice.")
        if self.minimum_eye_rime_characters < 2:
            raise ValueError("Eye-rhyme evidence requires at least two characters.")
        if self.minimum_analyzable_endings < 1:
            raise ValueError("At least one analyzable line ending must be required.")
        if self.maximum_pair_evaluations < 1:
            raise ValueError("At least one end-rhyme pair must be allowed.")
        if not self.scenario_id.strip():
            raise ValueError("A phonological scenario requires a stable ID.")

    @property
    def configuration_id(self) -> str:
        payload = json.dumps(
            asdict(self),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"phonology-config-v1:{digest}"


@dataclass(frozen=True)
class RhymeEndingVariant:
    phones: tuple[str, ...]
    phones_text: str
    rhyme_part: tuple[str, ...]
    rhyme_part_text: str
    stressed_vowel: str
    stress_suffix: str
    rhyme_syllable_count: int
    ending_shape: str
    final_consonants: tuple[str, ...]


@dataclass(frozen=True)
class InternalRhymeMatch:
    first_token_id: str
    first_word: str
    second_token_id: str
    second_word: str
    rhyme_part: str
    relationship: str


@dataclass(frozen=True)
class PhonologicalLineResult:
    line_id: str
    line_number: int
    stanza_number: int
    source_text: str
    status: RhymeEndingStatus
    eligible_token_count: int
    phonologically_supported_token_count: int
    ending_token_id: str
    ending_surface_form: str
    ending_lookup_form: str
    ending_pronunciation_status: str
    ending_candidate_phones: tuple[str, ...]
    ending_rhyme_parts: tuple[str, ...]
    resolved_rhyme_part: str
    stressed_vowel: str
    ending_shape: str
    poem_scheme_label: str
    stanza_scheme_label: str
    rhyme_group_id: str
    is_refrain: bool
    refrain_group_id: str
    internal_rhyme_matches: tuple[InternalRhymeMatch, ...]
    initial_consonant_sequence: tuple[str, ...]
    repeated_initial_consonants: tuple[str, ...]
    stressed_vowel_sequence: tuple[str, ...]
    repeated_stressed_vowels: tuple[str, ...]
    consonant_sequence: tuple[str, ...]
    repeated_consonants: tuple[str, ...]
    alliteration_density: float | None
    assonance_density: float | None
    consonance_density: float | None
    reason: str


@dataclass(frozen=True)
class RhymePairResult:
    pair_id: str
    stanza_number: int
    first_line_id: str
    first_line_number: int
    first_word: str
    second_line_id: str
    second_line_number: int
    second_word: str
    relationship: str
    rhyme_types: tuple[str, ...]
    similarity_score: float | None
    maximum_similarity_score: float | None
    stressed_vowel_similarity: float | None
    final_consonant_similarity: float | None
    phoneme_edit_similarity: float | None
    stress_alignment_similarity: float | None
    syllable_count_similarity: float | None
    is_eye_rhyme: bool
    orthographic_rime: str
    confidence_label: str
    note: str


@dataclass(frozen=True)
class RhymeStanzaSummary:
    stanza_number: int
    eligible_line_count: int
    analyzable_ending_count: int
    ending_coverage: float | None
    rhyme_scheme: str
    perfect_or_identical_pair_count: int
    slant_pair_count: int
    rhymed_line_count: int
    rhyme_density: float | None


@dataclass(frozen=True)
class SoundFamilySummary:
    category: str
    sound: str
    occurrence_count: int
    line_count: int
    share_of_category_occurrences: float | None


@dataclass(frozen=True)
class PhonologicalSummary:
    eligible_line_count: int
    analyzable_ending_count: int
    ambiguous_ending_count: int
    unmatched_ending_count: int
    ending_coverage: float | None
    whole_poem_rhyme_scheme: str
    stanza_scheme_sequence: str
    rhymed_line_count: int
    rhyme_density: float | None
    perfect_rhyme_pair_count: int
    identical_rhyme_pair_count: int
    slant_rhyme_pair_count: int
    eye_rhyme_pair_count: int
    internal_rhyme_pair_count: int
    refrain_line_count: int
    alliteration_density: float | None
    assonance_density: float | None
    consonance_density: float | None
    dominant_initial_consonants: tuple[str, ...]
    dominant_stressed_vowels: tuple[str, ...]
    dominant_consonants: tuple[str, ...]
    is_sparse: bool


@dataclass(frozen=True)
class PhonologicalAnalysisResult:
    module_result: ModuleResult
    configuration: PhonologicalConfiguration
    pronunciation_configuration_id: str
    summary: PhonologicalSummary
    stanza_summaries: tuple[RhymeStanzaSummary, ...]
    line_results: tuple[PhonologicalLineResult, ...]
    pair_results: tuple[RhymePairResult, ...]
    sound_families: tuple[SoundFamilySummary, ...]

    def __post_init__(self) -> None:
        analyzed = sum(
            item.status is RhymeEndingStatus.ANALYZED
            for item in self.line_results
        )
        if analyzed != self.summary.analyzable_ending_count:
            raise ValueError(
                "Phonological summary counts must agree with the line audit."
            )


def _phone_base(phone: str) -> str:
    match = _STRESSED_PHONE.fullmatch(phone)
    return match.group("base") if match else phone


def _phone_stress(phone: str) -> str:
    match = _STRESSED_PHONE.fullmatch(phone)
    return match.group("stress") if match else ""


def _is_vowel(phone: str) -> bool:
    return _STRESSED_PHONE.fullmatch(phone) is not None


def _candidate_phone_sequences(
    token: PronunciationTokenResult,
) -> tuple[tuple[str, ...], ...]:
    if (
        token.status is PronunciationStatus.SCHOLAR_OVERRIDE
        and token.resolved_phones
    ):
        return (tuple(token.resolved_phones.split()),)
    candidates = tuple(
        tuple(item.split())
        for item in token.dictionary_candidate_phones
        if item.strip()
    )
    if candidates:
        return tuple(dict.fromkeys(candidates))
    if token.resolved_phones:
        return (tuple(token.resolved_phones.split()),)
    return ()


def _last_rhyme_vowel_index(phones: tuple[str, ...]) -> int | None:
    primary = [
        index for index, phone in enumerate(phones) if _phone_stress(phone) == "1"
    ]
    if primary:
        return primary[-1]
    secondary = [
        index for index, phone in enumerate(phones) if _phone_stress(phone) == "2"
    ]
    if secondary:
        return secondary[-1]
    vowels = [index for index, phone in enumerate(phones) if _is_vowel(phone)]
    return vowels[-1] if vowels else None


def _ending_variant(phones: tuple[str, ...]) -> RhymeEndingVariant | None:
    start = _last_rhyme_vowel_index(phones)
    if start is None:
        return None
    suffix = phones[start:]
    rhyme_part = tuple(_phone_base(phone) for phone in suffix)
    vowel_phones = tuple(phone for phone in suffix if _is_vowel(phone))
    stress_suffix = "".join(_phone_stress(phone) for phone in vowel_phones)
    final_vowel_index = max(
        index for index, phone in enumerate(suffix) if _is_vowel(phone)
    )
    final_consonants = tuple(
        _phone_base(phone)
        for phone in suffix[final_vowel_index + 1 :]
        if not _is_vowel(phone)
    )
    if len(vowel_phones) == 1:
        ending_shape = "masculine"
    elif _phone_stress(vowel_phones[-1]) == "0":
        ending_shape = "feminine"
    else:
        ending_shape = "multisyllabic"
    return RhymeEndingVariant(
        phones=phones,
        phones_text=" ".join(phones),
        rhyme_part=rhyme_part,
        rhyme_part_text=" ".join(rhyme_part),
        stressed_vowel=_phone_base(phones[start]),
        stress_suffix=stress_suffix,
        rhyme_syllable_count=len(vowel_phones),
        ending_shape=ending_shape,
        final_consonants=final_consonants,
    )


def _variants_for_token(
    token: PronunciationTokenResult,
) -> tuple[RhymeEndingVariant, ...]:
    return tuple(
        variant
        for phones in _candidate_phone_sequences(token)
        if (variant := _ending_variant(phones)) is not None
    )


def _consensus(
    variants: tuple[RhymeEndingVariant, ...],
    selector: Callable[[RhymeEndingVariant], _T],
) -> _T | None:
    values = tuple(dict.fromkeys(selector(item) for item in variants))
    return values[0] if len(values) == 1 else None


def _feature_consensus(
    token: PronunciationTokenResult,
    selector: Callable[[tuple[str, ...]], _T],
) -> _T | None:
    sequences = _candidate_phone_sequences(token)
    values = tuple(dict.fromkeys(selector(item) for item in sequences))
    return values[0] if len(values) == 1 else None


def _initial_consonant(phones: tuple[str, ...]) -> str:
    for phone in phones:
        if _is_vowel(phone):
            return ""
        return _phone_base(phone)
    return ""


def _stressed_vowels(phones: tuple[str, ...]) -> tuple[str, ...]:
    stressed = tuple(
        _phone_base(phone)
        for phone in phones
        if _phone_stress(phone) in {"1", "2"}
    )
    if stressed:
        return stressed
    return tuple(
        _phone_base(phone) for phone in phones if _is_vowel(phone)
    )


def _consonants(phones: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(_phone_base(phone) for phone in phones if not _is_vowel(phone))


def _repeated(sequence: Iterable[str], minimum: int) -> tuple[str, ...]:
    counts = Counter(sequence)
    return tuple(sorted(sound for sound, count in counts.items() if count >= minimum))


def _repeated_occurrence_density(
    sequence: tuple[str, ...],
    repeated: tuple[str, ...],
) -> float | None:
    if not sequence:
        return None
    repeated_set = set(repeated)
    return sum(item in repeated_set for item in sequence) / len(sequence)


def _orthographic_rime(word: str) -> str:
    value = "".join(character for character in word.casefold() if character.isalpha())
    vowel_positions = [
        index for index, character in enumerate(value) if character in _ORTHOGRAPHIC_VOWELS
    ]
    if not vowel_positions:
        return ""
    start = vowel_positions[-1]
    if (
        value.endswith("e")
        and start == len(value) - 1
        and len(vowel_positions) > 1
    ):
        start = vowel_positions[-2]
    return value[start:]


def _normalized_edit_similarity(
    first: tuple[str, ...],
    second: tuple[str, ...],
) -> float:
    if first == second:
        return 1.0
    if not first or not second:
        return 0.0
    previous = list(range(len(second) + 1))
    for first_index, first_item in enumerate(first, start=1):
        current = [first_index]
        for second_index, second_item in enumerate(second, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[second_index] + 1,
                    previous[second_index - 1]
                    + (first_item != second_item),
                )
            )
        previous = current
    distance = previous[-1]
    return max(0.0, 1.0 - distance / max(len(first), len(second)))


def _vowel_similarity(
    first: str,
    second: str,
    configuration: PhonologicalConfiguration,
) -> float:
    if first == second:
        return 1.0
    first_family = _VOWEL_FAMILIES.get(first)
    second_family = _VOWEL_FAMILIES.get(second)
    if first_family and first_family == second_family:
        return configuration.related_vowel_family_score
    return 0.0


def _variant_similarity(
    first: RhymeEndingVariant,
    second: RhymeEndingVariant,
    configuration: PhonologicalConfiguration,
) -> tuple[float, float, float, float, float, float]:
    vowel = _vowel_similarity(
        first.stressed_vowel,
        second.stressed_vowel,
        configuration,
    )
    consonants = _normalized_edit_similarity(
        first.final_consonants,
        second.final_consonants,
    )
    edit = _normalized_edit_similarity(first.rhyme_part, second.rhyme_part)
    stress = _normalized_edit_similarity(
        tuple(first.stress_suffix),
        tuple(second.stress_suffix),
    )
    syllables = (
        1.0
        if first.rhyme_syllable_count == second.rhyme_syllable_count
        else max(
            0.0,
            1.0
            - abs(first.rhyme_syllable_count - second.rhyme_syllable_count)
            / max(first.rhyme_syllable_count, second.rhyme_syllable_count),
        )
    )
    total = (
        vowel * configuration.stressed_vowel_weight
        + consonants * configuration.final_consonant_weight
        + edit * configuration.phoneme_edit_weight
        + stress * configuration.stress_alignment_weight
        + syllables * configuration.syllable_count_weight
    )
    return total, vowel, consonants, edit, stress, syllables


def _scheme_label(index: int) -> str:
    label = ""
    value = index
    while True:
        value, remainder = divmod(value, 26)
        label = chr(ord("A") + remainder) + label
        if value == 0:
            return label
        value -= 1


def _normalize_refrain(text: str) -> str:
    return " ".join(text.casefold().split())


def _line_sound_evidence(
    tokens: tuple[PronunciationTokenResult, ...],
    configuration: PhonologicalConfiguration,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    float | None,
    float | None,
    float | None,
]:
    initials: list[str] = []
    vowels: list[str] = []
    consonants: list[str] = []
    for token in tokens:
        initial = _feature_consensus(token, _initial_consonant)
        if initial:
            initials.append(initial)
        stressed = _feature_consensus(token, _stressed_vowels)
        if stressed:
            vowels.extend(stressed)
        token_consonants = _feature_consensus(token, _consonants)
        if token_consonants:
            consonants.extend(token_consonants)
    initial_sequence = tuple(initials)
    vowel_sequence = tuple(vowels)
    consonant_sequence = tuple(consonants)
    repeated_initials = _repeated(
        initial_sequence,
        configuration.minimum_sound_repetitions,
    )
    repeated_vowels = _repeated(
        vowel_sequence,
        configuration.minimum_sound_repetitions,
    )
    repeated_consonants = _repeated(
        consonant_sequence,
        configuration.minimum_sound_repetitions,
    )
    return (
        initial_sequence,
        repeated_initials,
        vowel_sequence,
        repeated_vowels,
        consonant_sequence,
        repeated_consonants,
        _repeated_occurrence_density(initial_sequence, repeated_initials),
        _repeated_occurrence_density(vowel_sequence, repeated_vowels),
        _repeated_occurrence_density(consonant_sequence, repeated_consonants),
    )


def _internal_rhymes(
    tokens: tuple[PronunciationTokenResult, ...],
) -> tuple[InternalRhymeMatch, ...]:
    evidence: list[
        tuple[PronunciationTokenResult, str, tuple[str, ...]]
    ] = []
    for token in tokens:
        variants = _variants_for_token(token)
        rhyme_part = _consensus(variants, lambda item: item.rhyme_part_text)
        full_phones = _consensus(variants, lambda item: item.phones)
        if rhyme_part:
            evidence.append((token, rhyme_part, full_phones or ()))
    matches: list[InternalRhymeMatch] = []
    ending_token_id = tokens[-1].token_id if tokens else ""
    for first, second in combinations(evidence, 2):
        first_token, first_part, first_phones = first
        second_token, second_part, second_phones = second
        if first_part != second_part:
            continue
        if (
            first_token.token_id == ending_token_id
            and second_token.token_id == ending_token_id
        ):
            continue
        relationship = (
            "identical"
            if first_token.lookup_form == second_token.lookup_form
            or (first_phones and first_phones == second_phones)
            else "perfect"
        )
        matches.append(
            InternalRhymeMatch(
                first_token_id=first_token.token_id,
                first_word=first_token.surface_form,
                second_token_id=second_token.token_id,
                second_word=second_token.surface_form,
                rhyme_part=first_part,
                relationship=relationship,
            )
        )
    return tuple(matches)


def _initial_line_results(
    pronunciation: PronunciationAnalysisResult,
    configuration: PhonologicalConfiguration,
) -> tuple[PhonologicalLineResult, ...]:
    tokens_by_line: dict[int, list[PronunciationTokenResult]] = defaultdict(list)
    for token in pronunciation.token_audit:
        if token.eligible:
            tokens_by_line[token.line_number].append(token)
    results: list[PhonologicalLineResult] = []
    for source_line in pronunciation.line_summaries:
        tokens = tuple(
            sorted(
                tokens_by_line.get(source_line.line_number, ()),
                key=lambda item: item.token_position,
            )
        )
        supported = sum(bool(_candidate_phone_sequences(token)) for token in tokens)
        sound = _line_sound_evidence(tokens, configuration)
        internal = _internal_rhymes(tokens)
        if not tokens:
            results.append(
                PhonologicalLineResult(
                    line_id=source_line.line_id,
                    line_number=source_line.line_number,
                    stanza_number=source_line.stanza_number,
                    source_text=source_line.source_text,
                    status=RhymeEndingStatus.NO_LEXICAL_TOKENS,
                    eligible_token_count=0,
                    phonologically_supported_token_count=0,
                    ending_token_id="",
                    ending_surface_form="",
                    ending_lookup_form="",
                    ending_pronunciation_status="",
                    ending_candidate_phones=(),
                    ending_rhyme_parts=(),
                    resolved_rhyme_part="",
                    stressed_vowel="",
                    ending_shape="",
                    poem_scheme_label="",
                    stanza_scheme_label="",
                    rhyme_group_id="",
                    is_refrain=False,
                    refrain_group_id="",
                    internal_rhyme_matches=internal,
                    initial_consonant_sequence=sound[0],
                    repeated_initial_consonants=sound[1],
                    stressed_vowel_sequence=sound[2],
                    repeated_stressed_vowels=sound[3],
                    consonant_sequence=sound[4],
                    repeated_consonants=sound[5],
                    alliteration_density=sound[6],
                    assonance_density=sound[7],
                    consonance_density=sound[8],
                    reason="The physical line contains no eligible lexical token.",
                )
            )
            continue
        ending = tokens[-1]
        variants = _variants_for_token(ending)
        rhyme_parts = tuple(
            dict.fromkeys(item.rhyme_part_text for item in variants)
        )
        resolved_part = rhyme_parts[0] if len(rhyme_parts) == 1 else ""
        stressed_vowel = (
            _consensus(variants, lambda item: item.stressed_vowel) or ""
        )
        ending_shape = (
            _consensus(variants, lambda item: item.ending_shape) or "ambiguous"
        )
        if resolved_part:
            status = RhymeEndingStatus.ANALYZED
            reason = (
                "All retained pronunciations support one line-ending rhyme part."
                if len(variants) > 1
                else "The line ending supplies one analyzable rhyme part."
            )
        elif variants:
            status = RhymeEndingStatus.AMBIGUOUS_PRONUNCIATION
            reason = (
                "Retained pronunciation alternatives produce materially "
                "different rhyme parts; no scheme group was assigned."
            )
        elif (
            ending.status is PronunciationStatus.SOURCE_WITHOUT_MARKED_VOWEL
        ):
            status = RhymeEndingStatus.SOURCE_WITHOUT_MARKED_VOWEL
            reason = "The source pronunciation has no marked vowel."
        else:
            status = RhymeEndingStatus.UNMATCHED_PRONUNCIATION
            reason = "The line-ending word has no usable pronunciation evidence."
        results.append(
            PhonologicalLineResult(
                line_id=source_line.line_id,
                line_number=source_line.line_number,
                stanza_number=source_line.stanza_number,
                source_text=source_line.source_text,
                status=status,
                eligible_token_count=len(tokens),
                phonologically_supported_token_count=supported,
                ending_token_id=ending.token_id,
                ending_surface_form=ending.surface_form,
                ending_lookup_form=ending.lookup_form,
                ending_pronunciation_status=ending.status.value,
                ending_candidate_phones=tuple(
                    " ".join(item) for item in _candidate_phone_sequences(ending)
                ),
                ending_rhyme_parts=rhyme_parts,
                resolved_rhyme_part=resolved_part,
                stressed_vowel=stressed_vowel,
                ending_shape=ending_shape,
                poem_scheme_label="",
                stanza_scheme_label="",
                rhyme_group_id="",
                is_refrain=False,
                refrain_group_id="",
                internal_rhyme_matches=internal,
                initial_consonant_sequence=sound[0],
                repeated_initial_consonants=sound[1],
                stressed_vowel_sequence=sound[2],
                repeated_stressed_vowels=sound[3],
                consonant_sequence=sound[4],
                repeated_consonants=sound[5],
                alliteration_density=sound[6],
                assonance_density=sound[7],
                consonance_density=sound[8],
                reason=reason,
            )
        )
    return tuple(results)


def _assign_scheme_and_refrains(
    lines: tuple[PhonologicalLineResult, ...],
) -> tuple[PhonologicalLineResult, ...]:
    analyzed = tuple(
        item for item in lines if item.status is RhymeEndingStatus.ANALYZED
    )
    global_counts = Counter(item.resolved_rhyme_part for item in analyzed)
    global_labels: dict[str, str] = {}
    for line in analyzed:
        part = line.resolved_rhyme_part
        if global_counts[part] >= 2 and part not in global_labels:
            global_labels[part] = _scheme_label(len(global_labels))
    local_labels: dict[tuple[int, str], str] = {}
    for stanza_number in sorted({item.stanza_number for item in analyzed}):
        stanza_lines = tuple(
            item for item in analyzed if item.stanza_number == stanza_number
        )
        counts = Counter(item.resolved_rhyme_part for item in stanza_lines)
        for line in stanza_lines:
            key = (stanza_number, line.resolved_rhyme_part)
            if counts[line.resolved_rhyme_part] >= 2 and key not in local_labels:
                existing = sum(
                    stored_stanza == stanza_number
                    for stored_stanza, _ in local_labels
                )
                local_labels[key] = _scheme_label(existing)
    refrain_counts = Counter(
        _normalize_refrain(item.source_text)
        for item in lines
        if item.source_text.strip()
    )
    refrain_ids: dict[str, str] = {}
    updated: list[PhonologicalLineResult] = []
    for line in lines:
        refrain_key = _normalize_refrain(line.source_text)
        is_refrain = bool(refrain_key and refrain_counts[refrain_key] >= 2)
        if is_refrain and refrain_key not in refrain_ids:
            refrain_ids[refrain_key] = f"refrain-{len(refrain_ids) + 1}"
        if line.status is RhymeEndingStatus.ANALYZED:
            poem_label = global_labels.get(line.resolved_rhyme_part, "x")
            stanza_label = local_labels.get(
                (line.stanza_number, line.resolved_rhyme_part),
                "x",
            )
        elif line.status is RhymeEndingStatus.NO_LEXICAL_TOKENS:
            poem_label = ""
            stanza_label = ""
        else:
            poem_label = "?"
            stanza_label = "?"
        updated.append(
            replace(
                line,
                poem_scheme_label=poem_label,
                stanza_scheme_label=stanza_label,
                rhyme_group_id=(
                    f"rhyme-{poem_label}"
                    if poem_label not in {"", "x", "?"}
                    else ""
                ),
                is_refrain=is_refrain,
                refrain_group_id=refrain_ids.get(refrain_key, ""),
            )
        )
    return tuple(updated)


def _pair_result(
    first: PhonologicalLineResult,
    second: PhonologicalLineResult,
    first_token: PronunciationTokenResult,
    second_token: PronunciationTokenResult,
    configuration: PhonologicalConfiguration,
) -> RhymePairResult:
    first_variants = _variants_for_token(first_token)
    second_variants = _variants_for_token(second_token)
    scores = tuple(
        _variant_similarity(left, right, configuration)
        for left, right in product(first_variants, second_variants)
    )
    exact_part = (
        bool(first.resolved_rhyme_part)
        and first.resolved_rhyme_part == second.resolved_rhyme_part
    )
    identical = (
        exact_part
        and (
            first.ending_lookup_form == second.ending_lookup_form
            or (
                len(first_variants) == 1
                and len(second_variants) == 1
                and first_variants[0].phones == second_variants[0].phones
            )
        )
    )
    orthographic_first = _orthographic_rime(first.ending_lookup_form)
    orthographic_second = _orthographic_rime(second.ending_lookup_form)
    eye = (
        bool(orthographic_first)
        and orthographic_first == orthographic_second
        and len(orthographic_first) >= configuration.minimum_eye_rime_characters
        and not exact_part
    )
    minimum = min((item[0] for item in scores), default=None)
    maximum = max((item[0] for item in scores), default=None)
    if identical:
        relationship = "identical"
        confidence = "Exact"
        note = "The complete ending pronunciation or ending word is identical."
    elif exact_part:
        relationship = "perfect"
        confidence = "Exact"
        note = (
            "All retained pronunciations share the same segment from the last "
            "stressed vowel to the end, with a distinct preceding onset."
        )
    elif minimum is not None and minimum >= configuration.slant_rhyme_threshold:
        relationship = "slant"
        confidence = (
            "Moderate"
            if minimum >= configuration.slant_rhyme_threshold + 0.10
            else "Low"
        )
        note = (
            "Every retained pronunciation pairing meets the configured graded "
            "phonological-similarity threshold."
        )
    elif (
        maximum is not None
        and maximum >= configuration.slant_rhyme_threshold
        and minimum is not None
        and minimum < configuration.slant_rhyme_threshold
    ):
        relationship = "ambiguous_pronunciation"
        confidence = "Unresolved"
        note = (
            "Some retained pronunciation pairings meet the slant threshold and "
            "others do not; no slant count was assigned."
        )
    else:
        relationship = "none"
        confidence = "Below threshold"
        note = "The pair does not meet the exact or configured slant criteria."
    shapes = {
        item.ending_shape for item in first_variants + second_variants
    }
    rhyme_types: list[str] = [relationship]
    if exact_part or relationship == "slant":
        if shapes == {"masculine"}:
            rhyme_types.append("masculine")
        if shapes == {"feminine"}:
            rhyme_types.append("feminine")
        if any(
            item.rhyme_syllable_count > 1
            for item in first_variants + second_variants
        ):
            rhyme_types.append("multisyllabic")
    if eye:
        rhyme_types.append("eye")
    components = (
        min((item[index] for item in scores), default=None)
        for index in range(1, 6)
    )
    vowel, consonants, edit, stress, syllables = components
    identity = hashlib.sha256(
        f"{first.line_id}|{second.line_id}".encode("utf-8")
    ).hexdigest()[:12]
    return RhymePairResult(
        pair_id=f"rhyme-pair-{identity}",
        stanza_number=first.stanza_number,
        first_line_id=first.line_id,
        first_line_number=first.line_number,
        first_word=first.ending_surface_form,
        second_line_id=second.line_id,
        second_line_number=second.line_number,
        second_word=second.ending_surface_form,
        relationship=relationship,
        rhyme_types=tuple(dict.fromkeys(rhyme_types)),
        similarity_score=1.0 if exact_part else minimum,
        maximum_similarity_score=1.0 if exact_part else maximum,
        stressed_vowel_similarity=1.0 if exact_part else vowel,
        final_consonant_similarity=1.0 if exact_part else consonants,
        phoneme_edit_similarity=1.0 if exact_part else edit,
        stress_alignment_similarity=1.0 if exact_part else stress,
        syllable_count_similarity=1.0 if exact_part else syllables,
        is_eye_rhyme=eye,
        orthographic_rime=orthographic_first if eye else "",
        confidence_label=confidence,
        note=note,
    )


def _pair_results(
    lines: tuple[PhonologicalLineResult, ...],
    pronunciation: PronunciationAnalysisResult,
    configuration: PhonologicalConfiguration,
) -> tuple[RhymePairResult, ...]:
    token_map = {item.token_id: item for item in pronunciation.token_audit}
    pairs: list[tuple[PhonologicalLineResult, PhonologicalLineResult]] = []
    for stanza_number in sorted({item.stanza_number for item in lines}):
        analyzable = tuple(
            item
            for item in lines
            if item.stanza_number == stanza_number
            and item.status is RhymeEndingStatus.ANALYZED
        )
        pairs.extend(combinations(analyzable, 2))
    if len(pairs) > configuration.maximum_pair_evaluations:
        raise PhonologicalModuleError(
            "Rhyme analysis would exceed the configured end-pair limit. "
            "Increase the limit deliberately or analyze a smaller text."
        )
    return tuple(
        _pair_result(
            first,
            second,
            token_map[first.ending_token_id],
            token_map[second.ending_token_id],
            configuration,
        )
        for first, second in pairs
    )


def _stanza_summaries(
    lines: tuple[PhonologicalLineResult, ...],
    pairs: tuple[RhymePairResult, ...],
) -> tuple[RhymeStanzaSummary, ...]:
    summaries: list[RhymeStanzaSummary] = []
    stanza_numbers = sorted(
        {
            item.stanza_number
            for item in lines
            if item.status is not RhymeEndingStatus.NO_LEXICAL_TOKENS
        }
    )
    for stanza_number in stanza_numbers:
        stanza_lines = tuple(
            item
            for item in lines
            if item.stanza_number == stanza_number
            and item.status is not RhymeEndingStatus.NO_LEXICAL_TOKENS
        )
        stanza_pairs = tuple(
            item for item in pairs if item.stanza_number == stanza_number
        )
        analyzed = tuple(
            item
            for item in stanza_lines
            if item.status is RhymeEndingStatus.ANALYZED
        )
        rhymed_ids = {
            line_id
            for pair in stanza_pairs
            if pair.relationship in {"perfect", "identical"}
            for line_id in (pair.first_line_id, pair.second_line_id)
        }
        scheme = "".join(item.stanza_scheme_label for item in stanza_lines)
        summaries.append(
            RhymeStanzaSummary(
                stanza_number=stanza_number,
                eligible_line_count=len(stanza_lines),
                analyzable_ending_count=len(analyzed),
                ending_coverage=(
                    len(analyzed) / len(stanza_lines) if stanza_lines else None
                ),
                rhyme_scheme=scheme,
                perfect_or_identical_pair_count=sum(
                    item.relationship in {"perfect", "identical"}
                    for item in stanza_pairs
                ),
                slant_pair_count=sum(
                    item.relationship == "slant" for item in stanza_pairs
                ),
                rhymed_line_count=len(rhymed_ids),
                rhyme_density=(
                    len(rhymed_ids) / len(analyzed) if analyzed else None
                ),
            )
        )
    return tuple(summaries)


def _sound_family_summaries(
    lines: tuple[PhonologicalLineResult, ...],
) -> tuple[SoundFamilySummary, ...]:
    categories = {
        "initial_consonant": lambda item: item.initial_consonant_sequence,
        "stressed_vowel": lambda item: item.stressed_vowel_sequence,
        "consonant": lambda item: item.consonant_sequence,
    }
    rows: list[SoundFamilySummary] = []
    for category, selector in categories.items():
        occurrences: Counter[str] = Counter()
        line_counts: Counter[str] = Counter()
        for line in lines:
            sequence = selector(line)
            occurrences.update(sequence)
            line_counts.update(set(sequence))
        denominator = sum(occurrences.values())
        for sound, count in sorted(
            occurrences.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            rows.append(
                SoundFamilySummary(
                    category=category,
                    sound=sound,
                    occurrence_count=count,
                    line_count=line_counts[sound],
                    share_of_category_occurrences=(
                        count / denominator if denominator else None
                    ),
                )
            )
    return tuple(rows)


def _aggregate_density(
    lines: tuple[PhonologicalLineResult, ...],
    sequence_selector: Callable[[PhonologicalLineResult], tuple[str, ...]],
    repeated_selector: Callable[[PhonologicalLineResult], tuple[str, ...]],
) -> float | None:
    denominator = 0
    numerator = 0
    for line in lines:
        sequence = sequence_selector(line)
        repeated = set(repeated_selector(line))
        denominator += len(sequence)
        numerator += sum(item in repeated for item in sequence)
    return numerator / denominator if denominator else None


def _summary(
    lines: tuple[PhonologicalLineResult, ...],
    pairs: tuple[RhymePairResult, ...],
    stanzas: tuple[RhymeStanzaSummary, ...],
    sounds: tuple[SoundFamilySummary, ...],
    configuration: PhonologicalConfiguration,
) -> PhonologicalSummary:
    eligible = tuple(
        item
        for item in lines
        if item.status is not RhymeEndingStatus.NO_LEXICAL_TOKENS
    )
    analyzed = tuple(
        item for item in lines if item.status is RhymeEndingStatus.ANALYZED
    )
    rhymed_ids = {
        line_id
        for pair in pairs
        if pair.relationship in {"perfect", "identical"}
        for line_id in (pair.first_line_id, pair.second_line_id)
    }
    stanza_scheme_sequence = " ".join(
        item.rhyme_scheme for item in stanzas
    )
    whole_scheme = " ".join(
        "".join(
            line.poem_scheme_label
            for line in lines
            if line.stanza_number == stanza.stanza_number
            and line.status is not RhymeEndingStatus.NO_LEXICAL_TOKENS
        )
        for stanza in stanzas
    )

    def dominant(category: str) -> tuple[str, ...]:
        return tuple(
            item.sound
            for item in sounds
            if item.category == category
        )[:5]

    return PhonologicalSummary(
        eligible_line_count=len(eligible),
        analyzable_ending_count=len(analyzed),
        ambiguous_ending_count=sum(
            item.status is RhymeEndingStatus.AMBIGUOUS_PRONUNCIATION
            for item in lines
        ),
        unmatched_ending_count=sum(
            item.status
            in {
                RhymeEndingStatus.UNMATCHED_PRONUNCIATION,
                RhymeEndingStatus.SOURCE_WITHOUT_MARKED_VOWEL,
            }
            for item in lines
        ),
        ending_coverage=len(analyzed) / len(eligible) if eligible else None,
        whole_poem_rhyme_scheme=whole_scheme,
        stanza_scheme_sequence=stanza_scheme_sequence,
        rhymed_line_count=len(rhymed_ids),
        rhyme_density=len(rhymed_ids) / len(analyzed) if analyzed else None,
        perfect_rhyme_pair_count=sum(
            item.relationship == "perfect" for item in pairs
        ),
        identical_rhyme_pair_count=sum(
            item.relationship == "identical" for item in pairs
        ),
        slant_rhyme_pair_count=sum(
            item.relationship == "slant" for item in pairs
        ),
        eye_rhyme_pair_count=sum(item.is_eye_rhyme for item in pairs),
        internal_rhyme_pair_count=sum(
            len(item.internal_rhyme_matches) for item in lines
        ),
        refrain_line_count=sum(item.is_refrain for item in lines),
        alliteration_density=_aggregate_density(
            lines,
            lambda item: item.initial_consonant_sequence,
            lambda item: item.repeated_initial_consonants,
        ),
        assonance_density=_aggregate_density(
            lines,
            lambda item: item.stressed_vowel_sequence,
            lambda item: item.repeated_stressed_vowels,
        ),
        consonance_density=_aggregate_density(
            lines,
            lambda item: item.consonant_sequence,
            lambda item: item.repeated_consonants,
        ),
        dominant_initial_consonants=dominant("initial_consonant"),
        dominant_stressed_vowels=dominant("stressed_vowel"),
        dominant_consonants=dominant("consonant"),
        is_sparse=len(analyzed) < configuration.minimum_analyzable_endings,
    )


def _warnings(
    summary: PhonologicalSummary,
    configuration: PhonologicalConfiguration,
) -> tuple[ModuleWarning, ...]:
    warnings = [
        ModuleWarning(
            code="phonological_evidence_not_performance",
            message=(
                "Stage 7 reports dictionary-based rhyme and recurring sound "
                "evidence. It does not establish performed pronunciation, "
                "authorial intention, or the only valid hearing of the poem."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
        ModuleWarning(
            code="slant_similarity_not_probability",
            message=(
                "Slant-rhyme similarity is a transparent configured heuristic "
                "over CMUdict phonemes. Its score and confidence label are not "
                "probabilities or human validation."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
        ModuleWarning(
            code="scheme_uses_exact_rhyme_parts",
            message=(
                "Rhyme-scheme letters use only robust perfect or identical "
                "rhyme parts. Slant and eye evidence remain separate."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
    ]
    if summary.ending_coverage is None:
        warnings.append(
            ModuleWarning(
                code="no_eligible_line_endings",
                message="No physical line contained an eligible ending word.",
            )
        )
    elif (
        summary.ending_coverage
        < configuration.low_ending_coverage_warning_threshold
    ):
        warnings.append(
            ModuleWarning(
                code="low_rhyme_ending_coverage",
                message=(
                    "Fewer than the configured share of eligible line endings "
                    "had one robust rhyme part."
                ),
                technical_detail=(
                    f"{summary.analyzable_ending_count} of "
                    f"{summary.eligible_line_count} endings analyzed."
                ),
            )
        )
    if summary.ambiguous_ending_count:
        warnings.append(
            ModuleWarning(
                code="ambiguous_line_endings",
                message=(
                    "Some line-ending words have retained pronunciations with "
                    "different rhyme parts; they remain ungrouped."
                ),
                technical_detail=f"{summary.ambiguous_ending_count} line(s).",
            )
        )
    if summary.unmatched_ending_count:
        warnings.append(
            ModuleWarning(
                code="unmatched_line_endings",
                message=(
                    "Some line endings have no usable dictionary or override "
                    "pronunciation and receive no rhyme label."
                ),
                technical_detail=f"{summary.unmatched_ending_count} line(s).",
            )
        )
    if summary.is_sparse:
        warnings.append(
            ModuleWarning(
                code="sparse_rhyme_evidence",
                message=(
                    "There are fewer than the configured number of analyzable "
                    "line endings; poem-level rhyme summaries are sparse."
                ),
            )
        )
    return tuple(warnings)


def _metrics(
    summary: PhonologicalSummary,
    lines: tuple[PhonologicalLineResult, ...],
) -> tuple[ModuleMetric, ...]:
    metrics: list[ModuleMetric] = [
        ModuleMetric(
            metric_id="phonology.rhyme_scheme",
            value=summary.whole_poem_rhyme_scheme or None,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="perfect/identical end-rhyme labels; x unrhymed; ? unresolved",
            denominator=f"{summary.eligible_line_count} eligible line endings",
        ),
        ModuleMetric(
            metric_id="phonology.rhyme_density",
            value=summary.rhyme_density,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="proportion",
            denominator=f"{summary.analyzable_ending_count} analyzable endings",
            note="Share of analyzable lines participating in an exact rhyme pair.",
        ),
        ModuleMetric(
            metric_id="phonology.slant_rhyme_pair_count",
            value=summary.slant_rhyme_pair_count,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="within-stanza line-ending pairs",
        ),
        ModuleMetric(
            metric_id="phonology.internal_rhyme_pair_count",
            value=summary.internal_rhyme_pair_count,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="within-line exact rhyme pairs",
        ),
        ModuleMetric(
            metric_id="phonology.alliteration_density",
            value=summary.alliteration_density,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="repeated initial-consonant occurrences / supported initials",
        ),
        ModuleMetric(
            metric_id="phonology.assonance_density",
            value=summary.assonance_density,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="repeated stressed-vowel occurrences / supported stressed vowels",
        ),
        ModuleMetric(
            metric_id="phonology.consonance_density",
            value=summary.consonance_density,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="repeated consonant occurrences / supported consonants",
        ),
    ]
    for line in lines:
        metrics.append(
            ModuleMetric(
                metric_id="phonology.line_scheme_label",
                value=line.poem_scheme_label or None,
                layer=ResultLayer.COMPUTED_SUMMARY,
                scope="line",
                scope_id=line.line_id,
                unit="perfect/identical end-rhyme label",
                denominator=f"{line.eligible_token_count} eligible tokens",
            )
        )
    return tuple(metrics)


def analyze_phonological_evidence(
    pronunciation: PronunciationAnalysisResult,
    configuration: PhonologicalConfiguration | None = None,
) -> tuple[
    PhonologicalSummary,
    tuple[RhymeStanzaSummary, ...],
    tuple[PhonologicalLineResult, ...],
    tuple[RhymePairResult, ...],
    tuple[SoundFamilySummary, ...],
]:
    """Pure Stage 7 calculation over an immutable Stage 5 result."""

    configuration = configuration or PhonologicalConfiguration()
    lines = _assign_scheme_and_refrains(
        _initial_line_results(pronunciation, configuration)
    )
    pairs = _pair_results(lines, pronunciation, configuration)
    stanzas = _stanza_summaries(lines, pairs)
    sounds = _sound_family_summaries(lines)
    return (
        _summary(lines, pairs, stanzas, sounds, configuration),
        stanzas,
        lines,
        pairs,
        sounds,
    )


class PhonologicalModule:
    """Stage 7 rhyme and recurring sound module over pinned local CMUdict."""

    name = "rhyme_and_phonological_patterns"
    version = "1.0.0"

    def validate_resources(self) -> tuple[ResourceStatus, ...]:
        return ()

    def analyze_detailed(
        self,
        module_input: ModuleInput,
        pronunciation: PronunciationAnalysisResult,
        configuration: PhonologicalConfiguration | None = None,
    ) -> PhonologicalAnalysisResult:
        configuration = configuration or PhonologicalConfiguration()
        if (
            pronunciation.module_result.text_id != module_input.document.text_id
            or pronunciation.module_result.text_version_id
            != module_input.document.text_version_id
        ):
            raise PhonologicalModuleError(
                "Stage 7 and Stage 5 must describe the same preserved text version."
            )
        summary, stanzas, lines, pairs, sounds = analyze_phonological_evidence(
            pronunciation,
            configuration,
        )
        coverage = ModuleCoverage.from_counts(
            coverage_id="phonology.analyzable_line_endings",
            eligible_count=summary.eligible_line_count,
            matched_count=summary.analyzable_ending_count,
            unit="physical lines containing an eligible ending word",
            unmatched_items=tuple(
                f"line {item.line_number}: {item.ending_surface_form or item.reason}"
                for item in lines
                if item.status
                not in {
                    RhymeEndingStatus.ANALYZED,
                    RhymeEndingStatus.NO_LEXICAL_TOKENS,
                }
            ),
            note=(
                "A line ending is analyzable only when all retained pronunciation "
                "evidence supports one rhyme part."
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
                "Consumes retained Stage 5 exact observed-form CMUdict or "
                "scholar-override phones. Every material dictionary alternative "
                "is retained; no unapproved provisional pronunciation is "
                "consumed or silently selected."
            ),
            inclusion_policy=(
                "Scheme groups use robust perfect/identical rhyme parts from the "
                "last stressed vowel to line end. Slant, eye, internal rhyme, "
                "alliteration, assonance, and consonance remain separately labeled."
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
                "scheme": summary.whole_poem_rhyme_scheme,
                "line_statuses": [
                    (item.line_id, item.status.value, item.poem_scheme_label)
                    for item in lines
                ],
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        result_id = "phonology-result-v1:" + hashlib.sha256(
            identity_payload.encode("utf-8")
        ).hexdigest()[:20]
        module_result = ModuleResult(
            result_id=result_id,
            module_name=self.name,
            module_version=self.version,
            text_id=module_input.document.text_id,
            text_version_id=module_input.document.text_version_id,
            metrics=_metrics(summary, lines),
            coverage=(coverage,),
            warnings=_warnings(summary, configuration),
            provenance=provenance,
        )
        return PhonologicalAnalysisResult(
            module_result=module_result,
            configuration=configuration,
            pronunciation_configuration_id=(
                pronunciation.configuration.configuration_id
            ),
            summary=summary,
            stanza_summaries=stanzas,
            line_results=lines,
            pair_results=pairs,
            sound_families=sounds,
        )
