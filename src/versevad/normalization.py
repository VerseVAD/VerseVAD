"""Transparent normalization helpers used by adapters and matching."""

from __future__ import annotations

import unicodedata


APOSTROPHE_TRANSLATION = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u02bc": "'",
        "\uff07": "'",
    }
)


def normalize_lookup(value: str) -> str:
    """Apply NFC and case folding without discarding visible characters."""

    return unicodedata.normalize("NFC", value).casefold().strip()


def canonicalize_apostrophes(value: str) -> str:
    return value.translate(APOSTROPHE_TRANSLATION)


def possessive_base(value: str) -> str | None:
    """Return a conservative English possessive base, if one is present."""

    canonical = canonicalize_apostrophes(normalize_lookup(value))
    if len(canonical) > 2 and canonical.endswith("'s"):
        return canonical[:-2]
    if len(canonical) > 1 and canonical.endswith("s'"):
        return canonical[:-1]
    return None


def possessive_surface_base(value: str) -> str | None:
    """Return a possessive base while retaining source capitalization."""

    canonical = canonicalize_apostrophes(unicodedata.normalize("NFC", value).strip())
    if len(canonical) > 2 and canonical.casefold().endswith("'s"):
        return canonical[:-2]
    if len(canonical) > 1 and canonical.casefold().endswith("s'"):
        return canonical[:-1]
    return None


def strip_edge_punctuation(value: str) -> str:
    """Strip Unicode punctuation at token edges while preserving internal marks."""

    start = 0
    end = len(value)
    while start < end and unicodedata.category(value[start]).startswith("P"):
        start += 1
    while end > start and unicodedata.category(value[end - 1]).startswith("P"):
        end -= 1
    return value[start:end]
