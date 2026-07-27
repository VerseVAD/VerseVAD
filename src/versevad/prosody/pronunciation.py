"""Optional CMUdict pronunciation, syllable, and lexical-stress foundation."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from functools import lru_cache
from importlib.metadata import version as package_version
from pathlib import Path
from statistics import fmean
from typing import Iterable

import pronouncing

from versevad import __version__
from versevad.adapters.cmudict import (
    CMUDICT_DICTIONARY_ROWS,
    CMUDICT_PHONE_ROWS,
    CMUDICT_SYMBOL_ROWS,
    CMUDictAdapter,
    CMUDictAdapterError,
    CMUDictEntry,
    CMUDictLexicon,
    CMUDictValidation,
    normalize_pronunciation_key,
)
from versevad.analysis.statistics import descriptive_statistics
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
from versevad.core.resources import (
    LocalResourceManager,
    ResourceProvenance,
    ResourceSpec,
    ResourceState,
    ResourceStatus,
)
from versevad.models import DescriptiveStatistics, TokenRecord


CMUDICT_COMMIT = "74790861f652b15e4ac49015a90074ad62a27690"
CMUDICT_DICTIONARY_SHA256 = (
    "81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22"
)
CMUDICT_PHONES_SHA256 = (
    "ffb588a5e55684723582c7256e1d2f9fadb130011392d9e59237c76e34c2cfd6"
)
CMUDICT_SYMBOLS_SHA256 = (
    "408ccaae803641c6d7b626b6299949320c2dbca96b2220fd3fb17887b023b027"
)
CMUDICT_CITATION = (
    "Carnegie Mellon University Speech Group. CMU Pronouncing Dictionary, "
    f"official cmusphinx/cmudict commit {CMUDICT_COMMIT}. "
    "https://github.com/cmusphinx/cmudict"
)
CMUDICT_LICENSE_NOTICE = (
    "CMUdict permits unrestricted research and commercial use and requests "
    "acknowledgment of its Carnegie Mellon origin. Exact license retained "
    "locally at resources/pronunciation/CMUDICT_LICENSE.txt."
)

CMUDICT_DICTIONARY_SPEC = ResourceSpec(
    resource_id="cmudict-dictionary",
    display_name="CMU Pronouncing Dictionary",
    relative_path="pronunciation/cmudict.dict",
    version=f"Official repository commit {CMUDICT_COMMIT}",
    accepted_sha256=(CMUDICT_DICTIONARY_SHA256,),
    minimum_bytes=3_500_000,
    citation=CMUDICT_CITATION,
    license_notice=CMUDICT_LICENSE_NOTICE,
)
CMUDICT_PHONES_SPEC = ResourceSpec(
    resource_id="cmudict-phone-inventory",
    display_name="CMUdict phone inventory",
    relative_path="pronunciation/cmudict.phones",
    version=f"Official repository commit {CMUDICT_COMMIT}",
    accepted_sha256=(CMUDICT_PHONES_SHA256,),
    minimum_bytes=350,
    citation=CMUDICT_CITATION,
    license_notice=CMUDICT_LICENSE_NOTICE,
)
CMUDICT_SYMBOLS_SPEC = ResourceSpec(
    resource_id="cmudict-symbol-inventory",
    display_name="CMUdict symbol inventory",
    relative_path="pronunciation/cmudict.symbols",
    version=f"Official repository commit {CMUDICT_COMMIT}",
    accepted_sha256=(CMUDICT_SYMBOLS_SHA256,),
    minimum_bytes=250,
    citation=CMUDICT_CITATION,
    license_notice=CMUDICT_LICENSE_NOTICE,
)


class PronunciationModuleError(RuntimeError):
    """Plain-language failure raised before a partial result is published."""


class PronunciationStatus(StrEnum):
    NOT_ELIGIBLE = "not_eligible"
    DICTIONARY_UNIQUE = "dictionary_unique"
    DICTIONARY_PROSODIC_CONSENSUS = "dictionary_prosodic_consensus"
    DICTIONARY_USER_SELECTION = "dictionary_user_selection"
    SCHOLAR_OVERRIDE = "scholar_override"
    AMBIGUOUS_DICTIONARY = "ambiguous_dictionary"
    SOURCE_WITHOUT_MARKED_VOWEL = "source_without_marked_vowel"
    UNMATCHED = "unmatched"


@dataclass(frozen=True)
class PronunciationOverride:
    """One explicit poem-specific scholar pronunciation selection."""

    term: str
    phones: tuple[str, ...]
    note: str

    def __post_init__(self) -> None:
        if not self.term.strip():
            raise ValueError("A pronunciation override requires a word.")
        if not self.phones:
            raise ValueError("A pronunciation override requires ARPAbet phones.")
        if any(
            not phone.strip()
            or phone != phone.strip()
            or " " in phone
            or phone != phone.upper()
            for phone in self.phones
        ):
            raise ValueError(
                "Pronunciation override phones must be separate uppercase "
                "ARPAbet symbols."
            )
        if not self.note.strip():
            raise ValueError(
                "A pronunciation override requires a short scholarly note."
            )

    @property
    def lookup_form(self) -> str:
        return normalize_pronunciation_key(self.term)

    @property
    def phones_text(self) -> str:
        return " ".join(self.phones)


def parse_pronunciation_overrides(text: str) -> tuple[PronunciationOverride, ...]:
    """Parse beginner-facing `word = PHONES | note` override rows."""

    overrides: list[PronunciationOverride] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        assignment, note_separator, note = line.partition("|")
        term, equals, phone_text = assignment.partition("=")
        if not equals:
            raise ValueError(
                f"Override line {line_number} must use "
                "`word = ARPAbet phones | note`."
            )
        if not note_separator or not note.strip():
            raise ValueError(
                f"Override line {line_number} requires a note after `|`."
            )
        phones = tuple(phone_text.strip().upper().split())
        try:
            overrides.append(
                PronunciationOverride(
                    term=term.strip(),
                    phones=phones,
                    note=note.strip(),
                )
            )
        except ValueError as error:
            raise ValueError(f"Override line {line_number}: {error}") from error
    lookup_forms = [item.lookup_form for item in overrides]
    duplicates = sorted(
        {
            item
            for item in lookup_forms
            if lookup_forms.count(item) > 1
        }
    )
    if duplicates:
        raise ValueError(
            "Each override word may appear once. Duplicate normalized word(s): "
            + ", ".join(duplicates)
        )
    return tuple(overrides)


def serialize_pronunciation_overrides(
    overrides: tuple[PronunciationOverride, ...],
) -> str:
    """Serialize validated session overrides in the editable UI format."""

    return "\n".join(
        f"{override.term} = {override.phones_text} | {override.note}"
        for override in overrides
    )


def upsert_pronunciation_override_text(
    text: str,
    *,
    term: str,
    phones_text: str,
    note: str,
) -> str:
    """Add or replace one normalized observed-form override."""

    replacement = PronunciationOverride(
        term=term.strip(),
        phones=tuple(phones_text.strip().upper().split()),
        note=note.strip(),
    )
    current = list(parse_pronunciation_overrides(text))
    for index, override in enumerate(current):
        if override.lookup_form == replacement.lookup_form:
            current[index] = replacement
            break
    else:
        current.append(replacement)
    return serialize_pronunciation_overrides(tuple(current))


@dataclass(frozen=True)
class PronunciationConfiguration:
    overrides: tuple[PronunciationOverride, ...] = ()
    low_coverage_warning_threshold: float = 0.8
    minimum_complete_lines: int = 2
    minimum_resolved_tokens: int = 3
    scenario_id: str = "cmudict-prosody-foundation-v2"

    def __post_init__(self) -> None:
        if not 0 <= self.low_coverage_warning_threshold <= 1:
            raise ValueError("The pronunciation coverage threshold must be 0-1.")
        if self.minimum_complete_lines < 1:
            raise ValueError("At least one complete line must be required.")
        if self.minimum_resolved_tokens < 1:
            raise ValueError("At least one resolved token must be required.")
        if not self.scenario_id.strip():
            raise ValueError("A pronunciation scenario requires a stable ID.")
        lookup_forms = [item.lookup_form for item in self.overrides]
        if len(lookup_forms) != len(set(lookup_forms)):
            raise ValueError("Pronunciation override words must be unique.")

    @property
    def configuration_id(self) -> str:
        payload = json.dumps(
            asdict(self),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return f"pronunciation-config-v1:{digest}"


@dataclass(frozen=True)
class PronunciationTokenResult:
    token_id: str
    token_position: int
    surface_form: str
    normalized_form: str
    lookup_form: str
    part_of_speech: str
    line_number: int
    stanza_number: int
    context: str
    is_lexical: bool
    is_proper_noun: bool
    eligible: bool
    resolved: bool
    status: PronunciationStatus
    dictionary_source_term: str | None
    dictionary_candidate_count: int
    dictionary_candidate_phones: tuple[str, ...]
    dictionary_candidate_stresses: tuple[str, ...]
    dictionary_candidate_syllable_counts: tuple[int, ...]
    dictionary_source_lines: tuple[int, ...]
    resolved_phones: str | None
    resolved_stress_pattern: str | None
    resolved_syllable_count: int | None
    confidence_label: str
    override_note: str
    reason: str


@dataclass(frozen=True)
class PronunciationLineSummary:
    line_id: str
    line_number: int
    stanza_number: int
    source_text: str
    eligible_token_count: int
    resolved_token_count: int
    ambiguous_token_count: int
    unmatched_token_count: int
    source_without_marked_vowel_count: int
    resolution_coverage: float | None
    is_complete: bool
    syllable_count: int | None
    lexical_stress_sequence: str | None
    compact_stress_sequence: str | None
    primary_stress_count: int | None
    secondary_stress_count: int | None
    unstressed_syllable_count: int | None
    stress_density: float | None


@dataclass(frozen=True)
class PronunciationTypeSummary:
    lookup_form: str
    surface_forms: tuple[str, ...]
    token_occurrences: int
    resolved_occurrences: int
    statuses: tuple[str, ...]
    dictionary_candidate_count: int
    candidate_phones: tuple[str, ...]
    resolved_syllable_count: int | None
    resolved_stress_pattern: str | None


@dataclass(frozen=True)
class PronunciationSummary:
    syllables_per_resolved_word: DescriptiveStatistics
    syllables_per_complete_line: DescriptiveStatistics
    eligible_token_count: int
    resolved_token_count: int
    ambiguous_token_count: int
    unmatched_token_count: int
    source_without_marked_vowel_count: int
    override_token_count: int
    multi_candidate_token_count: int
    token_coverage: float | None
    eligible_unique_type_count: int
    resolved_unique_type_count: int
    unique_type_coverage: float | None
    eligible_line_count: int
    complete_line_count: int
    complete_line_coverage: float | None
    total_resolved_syllables: int
    primary_stress_count: int
    secondary_stress_count: int
    unstressed_syllable_count: int
    stress_density: float | None
    is_sparse: bool


@dataclass(frozen=True)
class PronunciationAnalysisResult:
    module_result: ModuleResult
    configuration: PronunciationConfiguration
    resource_statuses: tuple[ResourceStatus, ...]
    resource_validation: CMUDictValidation
    pronouncing_package_version: str
    cmudict_package_version: str
    summary: PronunciationSummary
    line_summaries: tuple[PronunciationLineSummary, ...]
    type_summaries: tuple[PronunciationTypeSummary, ...]
    token_audit: tuple[PronunciationTokenResult, ...]

    def __post_init__(self) -> None:
        eligible = sum(item.eligible for item in self.token_audit)
        resolved = sum(item.resolved for item in self.token_audit)
        if (
            eligible != self.summary.eligible_token_count
            or resolved != self.summary.resolved_token_count
        ):
            raise ValueError(
                "Pronunciation summary counts must agree with the token audit."
            )
        if any(
            item.resolved_syllable_count is not None and not item.resolved
            for item in self.token_audit
        ):
            raise ValueError(
                "Unresolved pronunciation rows cannot carry syllable values."
            )


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _base_token_values(token: TokenRecord) -> dict[str, object]:
    return {
        "token_id": token.token_id,
        "token_position": token.token_position,
        "surface_form": token.surface_form,
        "normalized_form": token.normalized_form,
        "lookup_form": normalize_pronunciation_key(token.surface_form),
        "part_of_speech": token.part_of_speech,
        "line_number": token.line_number,
        "stanza_number": token.stanza_number,
        "context": token.context,
        "is_lexical": token.is_lexical,
        "is_proper_noun": token.is_proper_noun,
    }


def _dictionary_fields(
    entry: CMUDictEntry | None,
) -> dict[str, object]:
    pronunciations = entry.pronunciations if entry is not None else ()
    return {
        "dictionary_source_term": (
            entry.source_term if entry is not None else None
        ),
        "dictionary_candidate_count": len(pronunciations),
        "dictionary_candidate_phones": tuple(
            item.phones_text for item in pronunciations
        ),
        "dictionary_candidate_stresses": tuple(
            item.stress_pattern for item in pronunciations
        ),
        "dictionary_candidate_syllable_counts": tuple(
            item.syllable_count for item in pronunciations
        ),
        "dictionary_source_lines": tuple(
            item.source_line for item in pronunciations
        ),
    }


def _ineligible_token(token: TokenRecord) -> PronunciationTokenResult:
    kind = "numeric" if token.is_numeric else "punctuation or non-lexical"
    return PronunciationTokenResult(
        **_base_token_values(token),
        eligible=False,
        resolved=False,
        status=PronunciationStatus.NOT_ELIGIBLE,
        **_dictionary_fields(None),
        resolved_phones=None,
        resolved_stress_pattern=None,
        resolved_syllable_count=None,
        confidence_label="Not applicable",
        override_note="",
        reason=f"Excluded from the pronunciation denominator as {kind}.",
    )


def _resolve_override(
    token: TokenRecord,
    entry: CMUDictEntry | None,
    override: PronunciationOverride,
    lexicon: CMUDictLexicon,
) -> PronunciationTokenResult:
    problems = lexicon.validate_phones(override.phones)
    if problems:
        raise PronunciationModuleError(
            f"The pronunciation override for {override.term!r} is invalid: "
            + " ".join(problems)
        )
    phones_text = override.phones_text
    stress_pattern = pronouncing.stresses(phones_text)
    syllable_count = pronouncing.syllable_count(phones_text)
    selected_dictionary_candidate = (
        entry is not None
        and any(
            candidate.phones_text == phones_text
            for candidate in entry.pronunciations
        )
    )
    return PronunciationTokenResult(
        **_base_token_values(token),
        eligible=True,
        resolved=True,
        status=(
            PronunciationStatus.DICTIONARY_USER_SELECTION
            if selected_dictionary_candidate
            else PronunciationStatus.SCHOLAR_OVERRIDE
        ),
        **_dictionary_fields(entry),
        resolved_phones=phones_text,
        resolved_stress_pattern=stress_pattern,
        resolved_syllable_count=syllable_count,
        confidence_label=(
            (
                "Explicit user selection from retained dictionary candidates; "
                "not a calibrated probability"
            )
            if selected_dictionary_candidate
            else "Explicit scholar override; not a calibrated probability"
        ),
        override_note=override.note,
        reason=(
            (
                "The user selected one retained dictionary candidate for this "
                "observed form in the current session."
            )
            if selected_dictionary_candidate
            else (
                "A validated poem-specific scholar override supplied this "
                "pronunciation. Dictionary candidates remain visible separately."
            )
        ),
    )


def _resolve_dictionary(
    token: TokenRecord,
    entry: CMUDictEntry | None,
) -> PronunciationTokenResult:
    if entry is None:
        return PronunciationTokenResult(
            **_base_token_values(token),
            eligible=True,
            resolved=False,
            status=PronunciationStatus.UNMATCHED,
            **_dictionary_fields(None),
            resolved_phones=None,
            resolved_stress_pattern=None,
            resolved_syllable_count=None,
            confidence_label="No dictionary evidence",
            override_note="",
            reason=(
                "No exact normalized observed-form entry was found in the "
                "pinned CMUdict source. No pronunciation was fabricated."
            ),
        )

    candidates = entry.pronunciations
    signatures = {
        (item.syllable_count, item.stress_pattern) for item in candidates
    }
    if any(item.syllable_count == 0 for item in candidates):
        return PronunciationTokenResult(
            **_base_token_values(token),
            eligible=True,
            resolved=False,
            status=PronunciationStatus.SOURCE_WITHOUT_MARKED_VOWEL,
            **_dictionary_fields(entry),
            resolved_phones=None,
            resolved_stress_pattern=None,
            resolved_syllable_count=None,
            confidence_label="Dictionary entry lacks usable stress evidence",
            override_note="",
            reason=(
                "The source entry has a pronunciation variant without a marked "
                "vowel. It remains auditable but cannot supply a syllable/stress "
                "result without a scholar override."
            ),
        )
    if len(candidates) == 1:
        candidate = candidates[0]
        return PronunciationTokenResult(
            **_base_token_values(token),
            eligible=True,
            resolved=True,
            status=PronunciationStatus.DICTIONARY_UNIQUE,
            **_dictionary_fields(entry),
            resolved_phones=candidate.phones_text,
            resolved_stress_pattern=candidate.stress_pattern,
            resolved_syllable_count=candidate.syllable_count,
            confidence_label=(
                "One dictionary pronunciation; not a calibrated probability"
            ),
            override_note="",
            reason="One exact observed-form dictionary pronunciation was available.",
        )
    if len(signatures) == 1:
        syllable_count, stress_pattern = next(iter(signatures))
        return PronunciationTokenResult(
            **_base_token_values(token),
            eligible=True,
            resolved=True,
            status=PronunciationStatus.DICTIONARY_PROSODIC_CONSENSUS,
            **_dictionary_fields(entry),
            resolved_phones=None,
            resolved_stress_pattern=stress_pattern,
            resolved_syllable_count=syllable_count,
            confidence_label=(
                "All dictionary variants agree on syllables and lexical stress; "
                "phoneme alternatives remain unresolved"
            ),
            override_note="",
            reason=(
                "Multiple exact dictionary pronunciations were retained. They "
                "agree on the Stage 5 syllable count and lexical-stress pattern, "
                "so only those shared prosodic fields contribute."
            ),
        )
    return PronunciationTokenResult(
        **_base_token_values(token),
        eligible=True,
        resolved=False,
        status=PronunciationStatus.AMBIGUOUS_DICTIONARY,
        **_dictionary_fields(entry),
        resolved_phones=None,
        resolved_stress_pattern=None,
        resolved_syllable_count=None,
        confidence_label="Unresolved materially different dictionary variants",
        override_note="",
        reason=(
            "Multiple exact dictionary pronunciations differ in syllable count "
            "or lexical stress. VerseVAD did not silently select one."
        ),
    )


def _token_audit(
    module_input: ModuleInput,
    lexicon: CMUDictLexicon,
    configuration: PronunciationConfiguration,
) -> tuple[PronunciationTokenResult, ...]:
    override_by_lookup = {
        item.lookup_form: item for item in configuration.overrides
    }
    rows: list[PronunciationTokenResult] = []
    for token in module_input.tokens:
        if not token.is_lexical:
            rows.append(_ineligible_token(token))
            continue
        lookup_form = normalize_pronunciation_key(token.surface_form)
        entry = lexicon.lookup(lookup_form)
        override = override_by_lookup.get(lookup_form)
        if override is not None:
            rows.append(_resolve_override(token, entry, override, lexicon))
        else:
            rows.append(_resolve_dictionary(token, entry))
    return tuple(rows)


def _line_summary(
    *,
    line_id: str,
    line_number: int,
    stanza_number: int,
    source_text: str,
    rows: Iterable[PronunciationTokenResult],
) -> PronunciationLineSummary:
    row_tuple = tuple(rows)
    eligible = tuple(item for item in row_tuple if item.eligible)
    resolved = tuple(item for item in eligible if item.resolved)
    is_complete = bool(eligible) and len(resolved) == len(eligible)
    stress_patterns = tuple(
        item.resolved_stress_pattern or "" for item in resolved
    )
    compact = "".join(stress_patterns) if is_complete else None
    total_syllables = (
        sum(item.resolved_syllable_count or 0 for item in resolved)
        if is_complete
        else None
    )
    primary = compact.count("1") if compact is not None else None
    secondary = compact.count("2") if compact is not None else None
    unstressed = compact.count("0") if compact is not None else None
    stressed = (
        (primary or 0) + (secondary or 0)
        if compact is not None
        else None
    )
    return PronunciationLineSummary(
        line_id=line_id,
        line_number=line_number,
        stanza_number=stanza_number,
        source_text=source_text,
        eligible_token_count=len(eligible),
        resolved_token_count=len(resolved),
        ambiguous_token_count=sum(
            item.status is PronunciationStatus.AMBIGUOUS_DICTIONARY
            for item in eligible
        ),
        unmatched_token_count=sum(
            item.status is PronunciationStatus.UNMATCHED for item in eligible
        ),
        source_without_marked_vowel_count=sum(
            item.status is PronunciationStatus.SOURCE_WITHOUT_MARKED_VOWEL
            for item in eligible
        ),
        resolution_coverage=_rate(len(resolved), len(eligible)),
        is_complete=is_complete,
        syllable_count=total_syllables,
        lexical_stress_sequence=(
            " | ".join(stress_patterns) if is_complete else None
        ),
        compact_stress_sequence=compact,
        primary_stress_count=primary,
        secondary_stress_count=secondary,
        unstressed_syllable_count=unstressed,
        stress_density=(
            stressed / total_syllables
            if stressed is not None and total_syllables
            else None
        ),
    )


def _line_summaries(
    module_input: ModuleInput,
    audit: tuple[PronunciationTokenResult, ...],
) -> tuple[PronunciationLineSummary, ...]:
    if module_input.poem_document is not None:
        stanza_by_id = {
            stanza.unit_id: stanza.ordinal
            for stanza in module_input.poem_document.stanzas
        }
        stanza_by_line = {
            line.ordinal: stanza_by_id.get(line.parent_id, 0)
            for line in module_input.poem_document.lines
        }
        return tuple(
            _line_summary(
                line_id=line.unit_id,
                line_number=line.ordinal,
                stanza_number=stanza_by_line.get(line.ordinal, 0),
                source_text=line.content_text,
                rows=(item for item in audit if item.line_number == line.ordinal),
            )
            for line in module_input.poem_document.lines
        )
    line_numbers = sorted({item.line_number for item in audit})
    return tuple(
        _line_summary(
            line_id=f"line-{line_number}",
            line_number=line_number,
            stanza_number=next(
                (
                    item.stanza_number
                    for item in audit
                    if item.line_number == line_number
                ),
                0,
            ),
            source_text="",
            rows=(item for item in audit if item.line_number == line_number),
        )
        for line_number in line_numbers
    )


def _type_summaries(
    audit: tuple[PronunciationTokenResult, ...],
) -> tuple[PronunciationTypeSummary, ...]:
    by_lookup: dict[str, list[PronunciationTokenResult]] = defaultdict(list)
    for item in audit:
        if item.eligible:
            by_lookup[item.lookup_form].append(item)
    summaries: list[PronunciationTypeSummary] = []
    for lookup_form, rows in by_lookup.items():
        resolved_syllables = {
            item.resolved_syllable_count for item in rows if item.resolved
        }
        resolved_stresses = {
            item.resolved_stress_pattern for item in rows if item.resolved
        }
        first = rows[0]
        summaries.append(
            PronunciationTypeSummary(
                lookup_form=lookup_form,
                surface_forms=tuple(
                    sorted({item.surface_form for item in rows}, key=str.casefold)
                ),
                token_occurrences=len(rows),
                resolved_occurrences=sum(item.resolved for item in rows),
                statuses=tuple(sorted({item.status.value for item in rows})),
                dictionary_candidate_count=first.dictionary_candidate_count,
                candidate_phones=first.dictionary_candidate_phones,
                resolved_syllable_count=(
                    next(iter(resolved_syllables))
                    if len(resolved_syllables) == 1
                    else None
                ),
                resolved_stress_pattern=(
                    next(iter(resolved_stresses))
                    if len(resolved_stresses) == 1
                    else None
                ),
            )
        )
    return tuple(sorted(summaries, key=lambda item: item.lookup_form))


def _summary(
    audit: tuple[PronunciationTokenResult, ...],
    lines: tuple[PronunciationLineSummary, ...],
    configuration: PronunciationConfiguration,
) -> PronunciationSummary:
    eligible = tuple(item for item in audit if item.eligible)
    resolved = tuple(item for item in eligible if item.resolved)
    eligible_types = {item.lookup_form for item in eligible}
    resolved_types = {item.lookup_form for item in resolved}
    eligible_lines = tuple(line for line in lines if line.eligible_token_count)
    complete_lines = tuple(line for line in eligible_lines if line.is_complete)
    stress_patterns = tuple(
        item.resolved_stress_pattern or "" for item in resolved
    )
    stress_string = "".join(stress_patterns)
    total_syllables = sum(
        item.resolved_syllable_count or 0 for item in resolved
    )
    primary = stress_string.count("1")
    secondary = stress_string.count("2")
    unstressed = stress_string.count("0")
    return PronunciationSummary(
        syllables_per_resolved_word=descriptive_statistics(
            item.resolved_syllable_count
            for item in resolved
            if item.resolved_syllable_count is not None
        ),
        syllables_per_complete_line=descriptive_statistics(
            line.syllable_count
            for line in complete_lines
            if line.syllable_count is not None
        ),
        eligible_token_count=len(eligible),
        resolved_token_count=len(resolved),
        ambiguous_token_count=sum(
            item.status is PronunciationStatus.AMBIGUOUS_DICTIONARY
            for item in eligible
        ),
        unmatched_token_count=sum(
            item.status is PronunciationStatus.UNMATCHED for item in eligible
        ),
        source_without_marked_vowel_count=sum(
            item.status is PronunciationStatus.SOURCE_WITHOUT_MARKED_VOWEL
            for item in eligible
        ),
        override_token_count=sum(
            item.status
            in {
                PronunciationStatus.DICTIONARY_USER_SELECTION,
                PronunciationStatus.SCHOLAR_OVERRIDE,
            }
            for item in eligible
        ),
        multi_candidate_token_count=sum(
            item.dictionary_candidate_count > 1 for item in eligible
        ),
        token_coverage=_rate(len(resolved), len(eligible)),
        eligible_unique_type_count=len(eligible_types),
        resolved_unique_type_count=len(resolved_types),
        unique_type_coverage=_rate(len(resolved_types), len(eligible_types)),
        eligible_line_count=len(eligible_lines),
        complete_line_count=len(complete_lines),
        complete_line_coverage=_rate(len(complete_lines), len(eligible_lines)),
        total_resolved_syllables=total_syllables,
        primary_stress_count=primary,
        secondary_stress_count=secondary,
        unstressed_syllable_count=unstressed,
        stress_density=(
            (primary + secondary) / total_syllables
            if total_syllables
            else None
        ),
        is_sparse=len(resolved) < configuration.minimum_resolved_tokens,
    )


def _warnings(
    summary: PronunciationSummary,
    configuration: PronunciationConfiguration,
) -> tuple[ModuleWarning, ...]:
    warnings = [
        ModuleWarning(
            code="north_american_dictionary",
            message=(
                "CMUdict supplies dictionary pronunciations for North American "
                "English. Dialect, historical pronunciation, performance, and "
                "poetic elision may differ."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
        ModuleWarning(
            code="lexical_stress_not_meter",
            message=(
                "Stage 5 reports dictionary syllables and lexical stress. It "
                "does not classify meter, performed rhythm, rhyme, or scansion."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
        ModuleWarning(
            code="confidence_is_categorical",
            message=(
                "Pronunciation confidence labels describe source resolution "
                "status; they are not calibrated probabilities."
            ),
            severity=WarningSeverity.INFORMATION,
        ),
    ]
    if not summary.eligible_token_count:
        warnings.append(
            ModuleWarning(
                code="no_eligible_tokens",
                message=(
                    "No lexical tokens were eligible. Pronunciation coverage "
                    "and aggregates remain missing."
                ),
            )
        )
    elif not summary.resolved_token_count:
        warnings.append(
            ModuleWarning(
                code="no_resolved_pronunciations",
                message=(
                    "No eligible token had a resolved pronunciation. Syllable "
                    "and stress aggregates remain missing rather than zero."
                ),
            )
        )
    if (
        summary.token_coverage is not None
        and summary.token_coverage < configuration.low_coverage_warning_threshold
    ):
        warnings.append(
            ModuleWarning(
                code="low_pronunciation_coverage",
                message=(
                    "Pronunciation coverage is below the configured caution "
                    f"threshold of {configuration.low_coverage_warning_threshold:.0%}."
                ),
                technical_detail=(
                    f"{summary.resolved_token_count} of "
                    f"{summary.eligible_token_count} eligible tokens resolved."
                ),
            )
        )
    if summary.ambiguous_token_count:
        warnings.append(
            ModuleWarning(
                code="material_pronunciation_ambiguity",
                message=(
                    "Some dictionary alternatives differ in syllable count or "
                    "lexical stress. They remain unresolved until the user "
                    "selects a retained candidate or supplies a validated "
                    "scholar override."
                ),
                technical_detail=(
                    f"{summary.ambiguous_token_count} token occurrence(s)."
                ),
            )
        )
    if summary.unmatched_token_count:
        warnings.append(
            ModuleWarning(
                code="out_of_dictionary_tokens",
                message=(
                    "Some observed forms are absent from the pinned dictionary. "
                    "No grapheme-to-phoneme estimate was substituted."
                ),
                technical_detail=(
                    f"{summary.unmatched_token_count} token occurrence(s)."
                ),
            )
        )
    if summary.source_without_marked_vowel_count:
        warnings.append(
            ModuleWarning(
                code="source_without_marked_vowel",
                message=(
                    "Some source entries contain no marked vowel and cannot "
                    "supply Stage 5 syllable or stress evidence."
                ),
                technical_detail=(
                    f"{summary.source_without_marked_vowel_count} token "
                    "occurrence(s)."
                ),
            )
        )
    if (
        summary.eligible_line_count
        and summary.complete_line_count < configuration.minimum_complete_lines
    ):
        warnings.append(
            ModuleWarning(
                code="few_complete_lines",
                message=(
                    "Fewer than the configured minimum number of lines have "
                    "complete pronunciation coverage. Line aggregates are sparse."
                ),
                technical_detail=(
                    f"{summary.complete_line_count} complete line(s); configured "
                    f"minimum {configuration.minimum_complete_lines}."
                ),
            )
        )
    if summary.complete_line_count < summary.eligible_line_count:
        warnings.append(
            ModuleWarning(
                code="incomplete_lines_excluded",
                message=(
                    "Incomplete lines keep total syllables and stress sequences "
                    "missing so unresolved words do not create deceptively low "
                    "line totals."
                ),
                severity=WarningSeverity.INFORMATION,
            )
        )
    if summary.override_token_count:
        warnings.append(
            ModuleWarning(
                code="scholar_overrides_active",
                message=(
                    "One or more poem-specific pronunciation selections or "
                    "scholar overrides are active and remain distinct from "
                    "automatic dictionary resolution."
                ),
                severity=WarningSeverity.INFORMATION,
                technical_detail=(
                    f"{summary.override_token_count} token occurrence(s)."
                ),
            )
        )
    if summary.is_sparse:
        warnings.append(
            ModuleWarning(
                code="sparse_resolved_sample",
                message=(
                    "Fewer than the configured minimum number of resolved tokens "
                    "contributed to Stage 5 aggregates."
                ),
            )
        )
    return tuple(warnings)


def _metrics(
    summary: PronunciationSummary,
    lines: tuple[PronunciationLineSummary, ...],
) -> tuple[ModuleMetric, ...]:
    word_stats = summary.syllables_per_resolved_word
    line_stats = summary.syllables_per_complete_line
    metrics = [
        ModuleMetric(
            metric_id="pronunciation.mean_syllables_per_resolved_word",
            value=word_stats.mean,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="syllables per resolved lexical token",
            weighting="resolved token occurrences",
            denominator=f"{summary.resolved_token_count} resolved tokens",
        ),
        ModuleMetric(
            metric_id="pronunciation.median_syllables_per_resolved_word",
            value=word_stats.median,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="syllables per resolved lexical token",
            weighting="resolved token occurrences",
            denominator=f"{summary.resolved_token_count} resolved tokens",
        ),
        ModuleMetric(
            metric_id="pronunciation.mean_syllables_per_complete_line",
            value=line_stats.mean,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="syllables per complete line",
            weighting="complete physical lines",
            denominator=f"{summary.complete_line_count} complete lines",
        ),
        ModuleMetric(
            metric_id="pronunciation.median_syllables_per_complete_line",
            value=line_stats.median,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="syllables per complete line",
            weighting="complete physical lines",
            denominator=f"{summary.complete_line_count} complete lines",
        ),
        ModuleMetric(
            metric_id="pronunciation.stress_density",
            value=summary.stress_density,
            layer=ResultLayer.COMPUTED_SUMMARY,
            unit="proportion of resolved syllables carrying primary or secondary stress",
            weighting="resolved syllables",
            denominator=f"{summary.total_resolved_syllables} resolved syllables",
        ),
    ]
    for line in lines:
        metrics.extend(
            (
                ModuleMetric(
                    metric_id="pronunciation.line_syllable_count",
                    value=line.syllable_count,
                    layer=ResultLayer.COMPUTED_SUMMARY,
                    scope="line",
                    scope_id=line.line_id,
                    unit="syllables",
                    weighting="resolved lexical tokens",
                    denominator=(
                        f"{line.resolved_token_count} of "
                        f"{line.eligible_token_count} eligible tokens resolved"
                    ),
                    note=(
                        "Missing unless every eligible lexical token in the line "
                        "is resolved."
                    ),
                ),
                ModuleMetric(
                    metric_id="pronunciation.line_lexical_stress_sequence",
                    value=line.lexical_stress_sequence,
                    layer=ResultLayer.DIRECT_OBSERVATION,
                    scope="line",
                    scope_id=line.line_id,
                    unit="CMUdict stress digits grouped by word",
                    denominator=(
                        f"{line.resolved_token_count} of "
                        f"{line.eligible_token_count} eligible tokens resolved"
                    ),
                ),
            )
        )
    return tuple(metrics)


@lru_cache(maxsize=4)
def _load_cached(
    dictionary_path: str,
    phones_path: str,
    symbols_path: str,
    dictionary_hash: str,
    phones_hash: str,
    symbols_hash: str,
    expected_dictionary_rows: int | None,
    expected_phone_rows: int | None,
    expected_symbol_rows: int | None,
) -> CMUDictLexicon:
    del dictionary_hash, phones_hash, symbols_hash
    return CMUDictAdapter().load(
        dictionary_path,
        phones_path,
        symbols_path,
        expected_dictionary_rows=expected_dictionary_rows,
        expected_phone_rows=expected_phone_rows,
        expected_symbol_rows=expected_symbol_rows,
    )


class PronunciationModule:
    name = "pronunciation_prosody_foundation"
    version = "1.1.0"

    def __init__(
        self,
        resource_root: Path | str,
        *,
        dictionary_spec: ResourceSpec = CMUDICT_DICTIONARY_SPEC,
        phones_spec: ResourceSpec = CMUDICT_PHONES_SPEC,
        symbols_spec: ResourceSpec = CMUDICT_SYMBOLS_SPEC,
        expected_dictionary_rows: int | None = CMUDICT_DICTIONARY_ROWS,
        expected_phone_rows: int | None = CMUDICT_PHONE_ROWS,
        expected_symbol_rows: int | None = CMUDICT_SYMBOL_ROWS,
    ) -> None:
        self.resource_root = Path(resource_root)
        self.dictionary_spec = dictionary_spec
        self.phones_spec = phones_spec
        self.symbols_spec = symbols_spec
        self.expected_dictionary_rows = expected_dictionary_rows
        self.expected_phone_rows = expected_phone_rows
        self.expected_symbol_rows = expected_symbol_rows
        self._manager = LocalResourceManager(self.resource_root)

    @property
    def resource_specs(self) -> tuple[ResourceSpec, ...]:
        return (
            self.dictionary_spec,
            self.phones_spec,
            self.symbols_spec,
        )

    def validate_resources(self) -> tuple[ResourceStatus, ...]:
        statuses = self._manager.validate_many(self.resource_specs)
        if all(status.available for status in statuses):
            try:
                _load_cached(
                    str(statuses[0].configured_path),
                    str(statuses[1].configured_path),
                    str(statuses[2].configured_path),
                    statuses[0].source_sha256,
                    statuses[1].source_sha256,
                    statuses[2].source_sha256,
                    self.expected_dictionary_rows,
                    self.expected_phone_rows,
                    self.expected_symbol_rows,
                )
            except CMUDictAdapterError as error:
                detail = (
                    f" Technical detail: {error.technical_detail}"
                    if error.technical_detail
                    else ""
                )
                statuses = (
                    replace(
                        statuses[0],
                        state=ResourceState.MALFORMED,
                        message=(
                            "The local CMUdict files are readable but do not "
                            f"satisfy the source contract: {error}{detail}"
                        ),
                    ),
                    *statuses[1:],
                )
        return statuses

    def _load(
        self,
    ) -> tuple[CMUDictLexicon, tuple[ResourceStatus, ...]]:
        statuses = self.validate_resources()
        unavailable = [
            status
            for status in statuses
            if status.state is not ResourceState.AVAILABLE
        ]
        if unavailable:
            raise PronunciationModuleError(
                "The pronunciation module is unavailable. "
                + " ".join(status.message for status in unavailable)
            )
        try:
            lexicon = _load_cached(
                str(statuses[0].configured_path),
                str(statuses[1].configured_path),
                str(statuses[2].configured_path),
                statuses[0].source_sha256,
                statuses[1].source_sha256,
                statuses[2].source_sha256,
                self.expected_dictionary_rows,
                self.expected_phone_rows,
                self.expected_symbol_rows,
            )
        except CMUDictAdapterError as error:
            detail = f" Technical detail: {error.technical_detail}" if error.technical_detail else ""
            raise PronunciationModuleError(f"{error}{detail}") from error
        return lexicon, statuses

    def analyze(
        self,
        module_input: ModuleInput,
    ) -> ModuleResult:
        return self.analyze_detailed(module_input).module_result

    def analyze_detailed(
        self,
        module_input: ModuleInput,
        configuration: PronunciationConfiguration = PronunciationConfiguration(),
    ) -> PronunciationAnalysisResult:
        lexicon, statuses = self._load()
        audit = _token_audit(module_input, lexicon, configuration)
        lines = _line_summaries(module_input, audit)
        summary = _summary(audit, lines, configuration)
        type_summaries = _type_summaries(audit)
        pronouncing_version = package_version("pronouncing")
        cmudict_version = package_version("cmudict")
        source_hashes = "|".join(status.source_sha256 for status in statuses)
        result_digest = hashlib.sha256(
            (
                module_input.document.text_sha256
                + configuration.configuration_id
                + source_hashes
            ).encode("utf-8")
        ).hexdigest()[:20]
        resource_provenance = tuple(
            ResourceProvenance.from_available_status(
                status,
                citation=spec.citation,
                license_notice=spec.license_notice,
                adapter_version=CMUDictAdapter.adapter_version,
            )
            for spec, status in zip(
                self.resource_specs,
                statuses,
                strict=True,
            )
        )
        module_result = ModuleResult(
            result_id=f"pronunciation-{result_digest}",
            module_name=self.name,
            module_version=self.version,
            text_id=module_input.document.text_id,
            text_version_id=module_input.document.text_version_id,
            metrics=_metrics(summary, lines),
            coverage=(
                ModuleCoverage.from_counts(
                    coverage_id="pronunciation.resolved_token_coverage",
                    eligible_count=summary.eligible_token_count,
                    matched_count=summary.resolved_token_count,
                    unit="lexical token occurrences",
                    unmatched_items=tuple(
                        item.surface_form
                        for item in audit
                        if item.eligible and not item.resolved
                    ),
                    note=(
                        "Resolved from one dictionary pronunciation, shared "
                        "syllable/stress evidence across alternatives, or an "
                        "explicit scholar override."
                    ),
                ),
                ModuleCoverage.from_counts(
                    coverage_id="pronunciation.resolved_unique_type_coverage",
                    eligible_count=summary.eligible_unique_type_count,
                    matched_count=summary.resolved_unique_type_count,
                    unit="unique normalized observed forms",
                    unmatched_items=tuple(
                        item.lookup_form
                        for item in type_summaries
                        if not item.resolved_occurrences
                    ),
                ),
                ModuleCoverage.from_counts(
                    coverage_id="pronunciation.complete_line_coverage",
                    eligible_count=summary.eligible_line_count,
                    matched_count=summary.complete_line_count,
                    unit="physical lines containing lexical tokens",
                    unmatched_items=tuple(
                        str(line.line_number)
                        for line in lines
                        if line.eligible_token_count and not line.is_complete
                    ),
                ),
            ),
            warnings=_warnings(summary, configuration),
            provenance=ModuleProvenance(
                software_version=__version__,
                source_text_sha256=module_input.document.text_sha256,
                preprocessing_recipe=module_input.preprocessing.recipe_id,
                pipeline_name=module_input.preprocessing.pipeline_name,
                pipeline_version=module_input.preprocessing.pipeline_version,
                configuration_id=configuration.configuration_id,
                scenario_id=configuration.scenario_id,
                lookup_policy=(
                    "Exact normalized observed-form lookup only; retain every "
                    "dictionary variant; resolve multiple variants only when "
                    "syllable count and lexical stress agree; explicit validated "
                    f"scholar overrides; pronouncing {pronouncing_version}; "
                    f"cmudict package {cmudict_version}."
                ),
                inclusion_policy=(
                    "All lexical tokens including proper nouns are eligible. "
                    "Punctuation and numeric/non-lexical tokens are excluded. "
                    "Unmatched, materially ambiguous, and vowelless source "
                    "entries remain missing. Incomplete line totals remain missing."
                ),
                resources=resource_provenance,
            ),
        )
        return PronunciationAnalysisResult(
            module_result=module_result,
            configuration=configuration,
            resource_statuses=statuses,
            resource_validation=lexicon.validation,
            pronouncing_package_version=pronouncing_version,
            cmudict_package_version=cmudict_version,
            summary=summary,
            line_summaries=lines,
            type_summaries=type_summaries,
            token_audit=audit,
        )
