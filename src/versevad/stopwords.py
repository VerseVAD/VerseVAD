"""Versioned, auditable stopword policy for secondary affective summaries."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

import spacy
from spacy.lang.en.stop_words import STOP_WORDS

from versevad.models import StopwordMode, StopwordPolicy, TokenRecord
from versevad.normalization import normalize_lookup


STOPWORD_SOURCE = "spaCy English STOP_WORDS"
STOPWORD_LIBRARY_VERSION = spacy.__version__
STOPWORD_LIST_VERSION = f"spacy-en-{STOPWORD_LIBRARY_VERSION}+versevad-protected-v1"

# These words remain available to the secondary analysis even when spaCy
# classifies them as stopwords. The first group protects negation; the second
# protects the modal, comparative, and intensifying terms named in the research
# specification so their possible affective function remains visible.
DEFAULT_PROTECTED_WORDS = (
    "against",
    "could",
    "least",
    "less",
    "may",
    "might",
    "more",
    "most",
    "must",
    "neither",
    "never",
    "no",
    "nor",
    "not",
    "should",
    "too",
    "very",
    "without",
)

STANDARD_STOPWORDS = frozenset(normalize_lookup(word) for word in STOP_WORDS)


def _digest(words: Iterable[str]) -> str:
    payload = "\n".join(sorted(set(words)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


STANDARD_STOPWORD_SHA256 = _digest(STANDARD_STOPWORDS)


def normalize_word_list(words: Iterable[str]) -> tuple[str, ...]:
    """Normalize a user list while rejecting phrases and blank entries."""

    normalized: set[str] = set()
    for raw_word in words:
        word = normalize_lookup(str(raw_word).strip())
        if not word:
            continue
        if any(character.isspace() for character in word):
            raise ValueError(
                f"Stopword lists accept one word per entry; {raw_word!r} is a phrase."
            )
        normalized.add(word)
    return tuple(sorted(normalized))


def build_stopword_policy(
    *,
    mode: StopwordMode | str = StopwordMode.STANDARD,
    protected_words: Iterable[str] = DEFAULT_PROTECTED_WORDS,
    custom_additions: Iterable[str] = (),
    custom_removals: Iterable[str] = (),
) -> StopwordPolicy:
    """Create a complete immutable policy recorded with every analysis."""

    selected_mode = mode if isinstance(mode, StopwordMode) else StopwordMode(mode)
    protected = normalize_word_list(protected_words)
    additions = normalize_word_list(custom_additions)
    removals = normalize_word_list(custom_removals)
    if selected_mode == StopwordMode.ALL_MATCHED:
        active: set[str] = set()
    else:
        active = set(STANDARD_STOPWORDS)
        if selected_mode == StopwordMode.CUSTOM:
            active.update(additions)
            active.difference_update(removals)
        active.difference_update(protected)
    active_words = tuple(sorted(active))
    return StopwordPolicy(
        mode=selected_mode,
        source=STOPWORD_SOURCE,
        library_version=STOPWORD_LIBRARY_VERSION,
        list_version=STOPWORD_LIST_VERSION,
        standard_word_count=len(STANDARD_STOPWORDS),
        standard_list_sha256=STANDARD_STOPWORD_SHA256,
        active_words=active_words,
        active_list_sha256=_digest(active_words),
        protected_words=protected,
        custom_additions=additions,
        custom_removals=removals,
    )


def classify_match_stopword(
    tokens: tuple[TokenRecord, ...],
    policy: StopwordPolicy,
    *,
    is_published_phrase: bool,
) -> tuple[str, bool, str]:
    """Return status, exclusion decision, and auditable reason for one match."""

    surface_and_lemma = {
        form
        for token in tokens
        for form in (token.normalized_form, token.normalized_lemma)
        if form
    }
    protected = surface_and_lemma.intersection(policy.protected_words)
    standard = surface_and_lemma.intersection(STANDARD_STOPWORDS)
    custom = surface_and_lemma.intersection(policy.custom_additions)
    removed = surface_and_lemma.intersection(policy.custom_removals)
    active = surface_and_lemma.intersection(policy.active_words)

    if is_published_phrase:
        if standard or custom:
            return (
                "published phrase retained intact",
                False,
                "An accepted published phrase remains one scored entry; stopwords inside it are not removed.",
            )
        return (
            "not a stopword (published phrase)",
            False,
            "The accepted published phrase remains one scored entry.",
        )
    if protected:
        words = ", ".join(sorted(protected))
        return (
            "protected term",
            False,
            f"Protected VerseVAD term retained in both views: {words}.",
        )
    if removed and not active:
        words = ", ".join(sorted(removed))
        return (
            "custom removal",
            False,
            f"Removed from the active stopword list by the analysis configuration: {words}.",
        )
    if standard or custom:
        if custom:
            status = "custom stopword"
            reason = (
                "Excluded from the secondary aggregate by the custom stopword list: "
                f"{', '.join(sorted(custom))}."
            )
        else:
            status = "standard stopword"
            reason = (
                "Excluded from the secondary aggregate by the standard stopword list "
                f"using surface/lemma recognition: {', '.join(sorted(standard))}."
            )
        if policy.mode == StopwordMode.ALL_MATCHED or not active:
            return (
                status,
                False,
                "Identified as a stopword but retained because the secondary policy is "
                "Include all matched words.",
            )
        return status, True, reason
    return "not a stopword", False, "No active stopword entry matched the surface form or lemma."

