"""Read-only adapter for a pinned official CMU Pronouncing Dictionary."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import pronouncing

from versevad.normalization import canonicalize_apostrophes, normalize_lookup


CMUDICT_DICTIONARY_ROWS = 135_166
CMUDICT_PHONE_ROWS = 39
CMUDICT_SYMBOL_ROWS = 84

_VARIANT_PATTERN = re.compile(
    r"^(?P<term>.+?)(?:\((?P<variant>[2-9][0-9]*)\))?$"
)
_BASE_PHONE_PATTERN = re.compile(r"^[A-Z]+$")
_STRESSED_VOWEL_PATTERN = re.compile(r"^(?P<base>[A-Z]+)(?P<stress>[012])$")


class CMUDictAdapterError(RuntimeError):
    """Plain-language source failure that confirms no file was changed."""

    def __init__(self, message: str, technical_detail: str = "") -> None:
        super().__init__(message)
        self.technical_detail = technical_detail
        self.data_changed = False


def normalize_pronunciation_key(value: str) -> str:
    """Normalize case and apostrophe style without deleting visible characters."""

    return canonicalize_apostrophes(normalize_lookup(value))


@dataclass(frozen=True)
class CMUPronunciation:
    """One source pronunciation variant for one normalized dictionary term."""

    source_term: str
    lookup_form: str
    variant_number: int
    phones: tuple[str, ...]
    stress_pattern: str
    syllable_count: int
    source_line: int
    source_comment: str = ""

    @property
    def phones_text(self) -> str:
        return " ".join(self.phones)


@dataclass(frozen=True)
class CMUDictEntry:
    """All source pronunciation variants for one spelling."""

    source_term: str
    lookup_form: str
    pronunciations: tuple[CMUPronunciation, ...]


@dataclass(frozen=True)
class CMUDictValidation:
    dictionary_path: Path
    phones_path: Path
    symbols_path: Path
    dictionary_sha256: str
    phones_sha256: str
    symbols_sha256: str
    dictionary_rows: int
    unique_terms: int
    multiple_pronunciation_terms: int
    maximum_pronunciations: int
    phone_rows: int
    symbol_rows: int
    malformed_rows: int
    duplicate_variants: int
    duplicate_pronunciations: int
    unknown_symbols: int
    vowelless_pronunciations: int
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass(frozen=True)
class CMUDictLexicon:
    entries: Mapping[str, CMUDictEntry]
    phone_categories: Mapping[str, str]
    symbols: frozenset[str]
    validation: CMUDictValidation

    @classmethod
    def create(
        cls,
        entries: Mapping[str, CMUDictEntry],
        phone_categories: Mapping[str, str],
        symbols: frozenset[str],
        validation: CMUDictValidation,
    ) -> CMUDictLexicon:
        return cls(
            entries=MappingProxyType(dict(entries)),
            phone_categories=MappingProxyType(dict(phone_categories)),
            symbols=symbols,
            validation=validation,
        )

    @property
    def vowel_phones(self) -> frozenset[str]:
        return frozenset(
            phone
            for phone, category in self.phone_categories.items()
            if category == "vowel"
        )

    def lookup(self, value: str) -> CMUDictEntry | None:
        return self.entries.get(normalize_pronunciation_key(value))

    def validate_phones(self, phones: tuple[str, ...]) -> tuple[str, ...]:
        """Return validation messages for a scholar-supplied ARPAbet sequence."""

        problems: list[str] = []
        if not phones:
            return ("A pronunciation must contain at least one ARPAbet symbol.",)
        vowel_count = 0
        for phone in phones:
            if phone not in self.symbols:
                problems.append(f"Unknown CMUdict symbol {phone!r}.")
                continue
            stressed = _STRESSED_VOWEL_PATTERN.fullmatch(phone)
            if stressed:
                base = stressed.group("base")
                if self.phone_categories.get(base) != "vowel":
                    problems.append(
                        f"{phone!r} carries stress but {base!r} is not a vowel."
                    )
                else:
                    vowel_count += 1
            elif self.phone_categories.get(phone) == "vowel":
                problems.append(
                    f"Vowel {phone!r} requires a 0, 1, or 2 stress marker."
                )
        if not vowel_count:
            problems.append(
                "A pronunciation requires at least one stressed or unstressed vowel."
            )
        return tuple(problems)


class CMUDictAdapter:
    """Validate and parse exact local CMUdict files without modifying them."""

    adapter_version = "1.0.0"

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _read_lines(path: Path, label: str) -> tuple[str, ...]:
        if not path.is_file():
            raise CMUDictAdapterError(
                f"The local CMUdict {label} file was not found.",
                f"Expected a readable file at {path}.",
            )
        try:
            return tuple(path.read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeError) as error:
            raise CMUDictAdapterError(
                f"The local CMUdict {label} file could not be read.",
                f"{type(error).__name__}: {error}",
            ) from error

    @staticmethod
    def _parse_phone_inventory(
        lines: tuple[str, ...],
    ) -> tuple[dict[str, str], list[str]]:
        phone_categories: dict[str, str] = {}
        problems: list[str] = []
        for source_line, line in enumerate(lines, start=1):
            parts = line.split("\t")
            if (
                len(parts) != 2
                or not _BASE_PHONE_PATTERN.fullmatch(parts[0])
                or not parts[1].strip()
            ):
                problems.append(
                    f"phone row {source_line}: expected BASE_PHONE<TAB>category"
                )
                continue
            phone, category = parts
            if phone in phone_categories:
                problems.append(
                    f"phone row {source_line}: duplicate phone {phone!r}"
                )
                continue
            phone_categories[phone] = category
        return phone_categories, problems

    @staticmethod
    def _parse_symbols(
        lines: tuple[str, ...],
    ) -> tuple[frozenset[str], list[str]]:
        symbols: set[str] = set()
        problems: list[str] = []
        for source_line, line in enumerate(lines, start=1):
            symbol = line.strip()
            if not symbol or " " in symbol or "\t" in symbol:
                problems.append(
                    f"symbol row {source_line}: expected one nonblank symbol"
                )
                continue
            if symbol in symbols:
                problems.append(
                    f"symbol row {source_line}: duplicate symbol {symbol!r}"
                )
                continue
            symbols.add(symbol)
        return frozenset(symbols), problems

    @staticmethod
    def _inventory_problems(
        phone_categories: Mapping[str, str],
        symbols: frozenset[str],
    ) -> list[str]:
        problems: list[str] = []
        for phone, category in phone_categories.items():
            if phone not in symbols:
                problems.append(f"base phone {phone!r} is missing from symbols")
            if category == "vowel":
                for stress in "012":
                    if f"{phone}{stress}" not in symbols:
                        problems.append(
                            f"vowel {phone!r} is missing stress symbol {phone}{stress}"
                        )
        for symbol in symbols:
            stressed = _STRESSED_VOWEL_PATTERN.fullmatch(symbol)
            base = stressed.group("base") if stressed else symbol
            if base not in phone_categories:
                problems.append(
                    f"symbol {symbol!r} has no base-phone inventory entry"
                )
            elif stressed and phone_categories[base] != "vowel":
                problems.append(
                    f"non-vowel symbol {symbol!r} unexpectedly carries stress"
                )
        return problems

    def load(
        self,
        dictionary_path: Path | str,
        phones_path: Path | str,
        symbols_path: Path | str,
        *,
        expected_dictionary_rows: int | None = CMUDICT_DICTIONARY_ROWS,
        expected_phone_rows: int | None = CMUDICT_PHONE_ROWS,
        expected_symbol_rows: int | None = CMUDICT_SYMBOL_ROWS,
    ) -> CMUDictLexicon:
        dictionary = Path(dictionary_path)
        phones = Path(phones_path)
        symbols_file = Path(symbols_path)
        dictionary_lines = self._read_lines(dictionary, "dictionary")
        phone_lines = self._read_lines(phones, "phone inventory")
        symbol_lines = self._read_lines(symbols_file, "symbol inventory")

        phone_categories, phone_problems = self._parse_phone_inventory(
            phone_lines
        )
        symbols, symbol_problems = self._parse_symbols(symbol_lines)
        problems = [
            *phone_problems,
            *symbol_problems,
            *self._inventory_problems(phone_categories, symbols),
        ]

        by_lookup: dict[str, list[CMUPronunciation]] = {}
        source_terms: dict[str, str] = {}
        variant_numbers: dict[str, set[int]] = {}
        malformed_rows = 0
        duplicate_variants = 0
        duplicate_pronunciations = 0
        unknown_symbols = 0
        vowelless_pronunciations = 0

        for source_line, line in enumerate(dictionary_lines, start=1):
            key, separator, phone_text = line.partition(" ")
            match = _VARIANT_PATTERN.fullmatch(key)
            if (
                not separator
                or not match
                or not phone_text
                or phone_text != phone_text.strip()
            ):
                malformed_rows += 1
                problems.append(
                    f"dictionary row {source_line}: malformed term/phones structure"
                )
                continue
            phone_text, comment_separator, source_comment = phone_text.partition(
                " # "
            )
            if not comment_separator:
                source_comment = ""
            source_term = match.group("term")
            variant_number = int(match.group("variant") or "1")
            lookup_form = normalize_pronunciation_key(source_term)
            phone_tuple = tuple(phone_text.split())
            if (
                not source_term
                or source_term != source_term.strip()
                or not lookup_form
                or source_term.casefold() != source_term
            ):
                malformed_rows += 1
                problems.append(
                    f"dictionary row {source_line}: malformed source term {source_term!r}"
                )
                continue

            phone_errors: list[str] = []
            vowel_count = 0
            for phone in phone_tuple:
                if phone not in symbols:
                    unknown_symbols += 1
                    phone_errors.append(f"unknown symbol {phone!r}")
                    continue
                stressed = _STRESSED_VOWEL_PATTERN.fullmatch(phone)
                if stressed:
                    base = stressed.group("base")
                    if phone_categories.get(base) != "vowel":
                        phone_errors.append(
                            f"stress marker on non-vowel {phone!r}"
                        )
                    else:
                        vowel_count += 1
                elif phone_categories.get(phone) == "vowel":
                    phone_errors.append(
                        f"vowel {phone!r} lacks a 0, 1, or 2 stress marker"
                    )
            stress_pattern = pronouncing.stresses(phone_text)
            syllable_count = pronouncing.syllable_count(phone_text)
            if len(stress_pattern) != vowel_count or syllable_count != vowel_count:
                phone_errors.append(
                    "pronouncing syllable/stress utilities disagree with vowel count"
                )
            if phone_errors:
                malformed_rows += 1
                problems.append(
                    f"dictionary row {source_line}: " + "; ".join(phone_errors)
                )
                continue
            if not vowel_count:
                vowelless_pronunciations += 1

            seen_variants = variant_numbers.setdefault(lookup_form, set())
            if variant_number in seen_variants:
                duplicate_variants += 1
                problems.append(
                    f"dictionary row {source_line}: duplicate variant "
                    f"{variant_number} for {source_term!r}"
                )
                continue
            seen_variants.add(variant_number)
            existing = by_lookup.setdefault(lookup_form, [])
            if any(item.phones == phone_tuple for item in existing):
                duplicate_pronunciations += 1
            source_terms.setdefault(lookup_form, source_term)
            existing.append(
                CMUPronunciation(
                    source_term=source_term,
                    lookup_form=lookup_form,
                    variant_number=variant_number,
                    phones=phone_tuple,
                    stress_pattern=stress_pattern,
                    syllable_count=syllable_count,
                    source_line=source_line,
                    source_comment=source_comment,
                )
            )

        for lookup_form, candidates in by_lookup.items():
            observed = sorted(item.variant_number for item in candidates)
            expected = list(range(1, len(candidates) + 1))
            if observed != expected:
                problems.append(
                    f"term {source_terms[lookup_form]!r}: variant numbers "
                    f"{observed!r} are not contiguous from 1"
                )

        if (
            expected_dictionary_rows is not None
            and len(dictionary_lines) != expected_dictionary_rows
        ):
            problems.append(
                f"expected {expected_dictionary_rows} dictionary rows; "
                f"found {len(dictionary_lines)}"
            )
        if expected_phone_rows is not None and len(phone_lines) != expected_phone_rows:
            problems.append(
                f"expected {expected_phone_rows} phone rows; found {len(phone_lines)}"
            )
        if (
            expected_symbol_rows is not None
            and len(symbol_lines) != expected_symbol_rows
        ):
            problems.append(
                f"expected {expected_symbol_rows} symbol rows; "
                f"found {len(symbol_lines)}"
            )

        entries = {
            lookup_form: CMUDictEntry(
                source_term=source_terms[lookup_form],
                lookup_form=lookup_form,
                pronunciations=tuple(
                    sorted(
                        candidates,
                        key=lambda item: item.variant_number,
                    )
                ),
            )
            for lookup_form, candidates in by_lookup.items()
        }
        maximum_pronunciations = max(
            (len(entry.pronunciations) for entry in entries.values()),
            default=0,
        )
        errors = (
            (
                "The CMUdict files contain structural problems; no partial "
                "pronunciation resource was activated.",
            )
            if problems
            else ()
        )
        validation = CMUDictValidation(
            dictionary_path=dictionary.resolve(),
            phones_path=phones.resolve(),
            symbols_path=symbols_file.resolve(),
            dictionary_sha256=self._sha256(dictionary),
            phones_sha256=self._sha256(phones),
            symbols_sha256=self._sha256(symbols_file),
            dictionary_rows=len(dictionary_lines),
            unique_terms=len(entries),
            multiple_pronunciation_terms=sum(
                len(entry.pronunciations) > 1 for entry in entries.values()
            ),
            maximum_pronunciations=maximum_pronunciations,
            phone_rows=len(phone_categories),
            symbol_rows=len(symbols),
            malformed_rows=malformed_rows,
            duplicate_variants=duplicate_variants,
            duplicate_pronunciations=duplicate_pronunciations,
            unknown_symbols=unknown_symbols,
            vowelless_pronunciations=vowelless_pronunciations,
            errors=errors,
            warnings=(
                (
                    "CMUdict is a North American English dictionary and "
                    "acknowledges possible errors, omissions, and inconsistencies."
                ),
                (
                    f"{vowelless_pronunciations} source pronunciation(s) have no "
                    "marked vowel and cannot supply a syllable/stress result."
                ),
                (
                    f"{duplicate_pronunciations} alternate source row(s) repeat "
                    "an existing phone sequence and remain auditable variants."
                ),
            ),
        )
        if not validation.is_valid:
            detail = " | ".join(problems[:16])
            if len(problems) > 16:
                detail += f" | {len(problems) - 16} additional problem(s)"
            raise CMUDictAdapterError(validation.errors[0], detail)
        return CMUDictLexicon.create(
            entries,
            phone_categories,
            symbols,
            validation,
        )
