"""Auditable exact, lemma, phrase, and comparison lookup across loaded lexicons."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
from typing import Iterable

from versevad.application import LEXICON_SPECS, load_lexicon
from versevad.models import (
    EmotionAssociationEntry,
    EmotionIntensityEntry,
    VadEntry,
    VadLexicon,
    VadScores,
)
from versevad.normalization import normalize_lookup
from versevad.preprocessing import TextPreprocessor, create_text_document


@dataclass(frozen=True)
class LexiconExplorerEntry:
    lexicon_id: str
    lexicon: str
    value_kind: str
    matched_term: str
    match_method: str
    source_rows: tuple[int, ...]
    original_scale: str
    original_scores: VadScores | None
    normalized_scores: VadScores | None
    standard_deviation: VadScores | None
    rater_count: VadScores | None
    associations: tuple[str, ...]
    intensities: tuple[tuple[str, float], ...]
    source_file: str
    source_sha256: str
    version: str
    adapter_version: str
    citation: str
    normalization_formula: str


@dataclass(frozen=True)
class ComponentAverage:
    lexicon_id: str
    lexicon: str
    components: tuple[str, ...]
    original_scores: VadScores
    normalized_scores: VadScores
    original_scale: str


@dataclass(frozen=True)
class CrossLexiconSpread:
    dimension: str
    entry_count: int
    minimum: float
    maximum: float
    spread: float
    descriptive_agreement: str


@dataclass(frozen=True)
class LexiconExplorerResult:
    query: str
    normalized_query: str
    processing_lemma: str
    processing_pos: str
    entries: tuple[LexiconExplorerEntry, ...]
    component_averages: tuple[ComponentAverage, ...]
    comparisons: tuple[CrossLexiconSpread, ...]
    suggestions: tuple[str, ...]
    notices: tuple[str, ...]


def _mean_scores(values: Iterable[VadScores]) -> VadScores:
    rows = tuple(values)
    return VadScores(
        valence=sum(row.valence for row in rows) / len(rows),
        arousal=sum(row.arousal for row in rows) / len(rows),
        dominance=sum(row.dominance for row in rows) / len(rows),
    )


def _entry_view(lexicon, entry, method: str) -> LexiconExplorerEntry:
    metadata = lexicon.metadata
    validation = lexicon.validation
    source_path = validation.source_path
    common = dict(
        lexicon_id=metadata.lexicon_id,
        lexicon=metadata.display_name,
        value_kind=metadata.value_kind.value,
        matched_term=entry.source_term,
        match_method=method,
        original_scale=f"{metadata.source_scale_min:g} to {metadata.source_scale_max:g}",
        source_file=str(source_path) if source_path is not None else "not recorded",
        source_sha256=validation.source_sha256,
        version=metadata.version,
        adapter_version=metadata.adapter_version,
        citation=metadata.citation,
        normalization_formula=metadata.normalization_formula,
    )
    if isinstance(entry, VadEntry):
        return LexiconExplorerEntry(
            **common,
            source_rows=(entry.source_row,),
            original_scores=entry.original,
            normalized_scores=entry.normalized,
            # Streamlit can retain entries created before these optional
            # uncertainty fields were added to VadEntry. Treat their absence
            # as unavailable source data rather than failing the lookup.
            standard_deviation=getattr(entry, "standard_deviation", None),
            rater_count=getattr(entry, "rater_count", None),
            associations=(),
            intensities=(),
        )
    if isinstance(entry, EmotionAssociationEntry):
        return LexiconExplorerEntry(
            **common,
            source_rows=entry.source_rows,
            original_scores=None,
            normalized_scores=None,
            standard_deviation=None,
            rater_count=None,
            associations=entry.associations,
            intensities=(),
        )
    if isinstance(entry, EmotionIntensityEntry):
        return LexiconExplorerEntry(
            **common,
            source_rows=entry.source_rows,
            original_scores=None,
            normalized_scores=None,
            standard_deviation=None,
            rater_count=None,
            associations=(),
            intensities=entry.intensities,
        )
    raise TypeError(f"Unsupported lexicon entry: {type(entry)!r}")


def explore_loaded_lexicons(
    query: str,
    lexicons: Iterable[object],
    preprocessor: TextPreprocessor,
    *,
    mapped_query: str = "",
) -> LexiconExplorerResult:
    """Search loaded source entries without silently substituting a lemma."""

    raw_query = query.strip()
    if not raw_query:
        raise ValueError("Enter a word or phrase to look up.")
    if len(raw_query) > 200 or "\n" in raw_query or "\r" in raw_query:
        raise ValueError("Look up one word or phrase of at most 200 characters.")
    normalized = normalize_lookup(raw_query)
    document = create_text_document("lexicon-explorer", "Lexicon Explorer", raw_query)
    tokens = tuple(token for token in preprocessor.process(document) if token.is_lexical)
    lemma = ""
    pos = ""
    if len(tokens) == 1:
        lemma = tokens[0].normalized_lemma
        pos = tokens[0].part_of_speech

    loaded = tuple(lexicons)
    views: list[LexiconExplorerEntry] = []
    notices: list[str] = []
    matched_lexicons: set[str] = set()
    for lexicon in loaded:
        entry, conflict = lexicon.resolve(normalized, raw_query)
        if conflict:
            notices.append(
                f"{lexicon.metadata.display_name} has a capitalization collision for "
                "this lookup; no source entry was guessed."
            )
        method = "exact phrase" if len(tokens) > 1 else "exact entry"
        if entry is None and lemma and lemma != normalized:
            entry, lemma_conflict = lexicon.resolve(lemma, tokens[0].lemma)
            if lemma_conflict:
                notices.append(
                    f"{lexicon.metadata.display_name} has an unresolved collision for the proposed lemma."
                )
            if entry is not None:
                method = "lemma-derived entry"
        if entry is not None:
            views.append(_entry_view(lexicon, entry, method))
            matched_lexicons.add(lexicon.metadata.lexicon_id)

    mapped = mapped_query.strip()
    if mapped and normalize_lookup(mapped) != normalized:
        mapped_normalized = normalize_lookup(mapped)
        for lexicon in loaded:
            if lexicon.metadata.lexicon_id in matched_lexicons:
                continue
            entry, conflict = lexicon.resolve(mapped_normalized, mapped)
            if conflict:
                notices.append(
                    f"{lexicon.metadata.display_name} has a capitalization collision for the user-supplied mapping."
                )
            if entry is not None:
                views.append(_entry_view(lexicon, entry, "user-supplied mapped lookup"))
                matched_lexicons.add(lexicon.metadata.lexicon_id)
        notices.append(
            f"User-supplied mapping shown for lookup only: {raw_query} → {mapped}. "
            "It does not alter corpus or poem analyses."
        )

    component_averages: list[ComponentAverage] = []
    if len(tokens) > 1:
        for lexicon in loaded:
            if not isinstance(lexicon, VadLexicon):
                continue
            if lexicon.metadata.lexicon_id in matched_lexicons:
                continue
            component_entries = []
            for token in tokens:
                entry, conflict = lexicon.resolve(token.normalized_form, token.surface_form)
                if conflict or entry is None:
                    component_entries = []
                    break
                component_entries.append(entry)
            if component_entries:
                component_averages.append(
                    ComponentAverage(
                        lexicon_id=lexicon.metadata.lexicon_id,
                        lexicon=lexicon.metadata.display_name,
                        components=tuple(entry.source_term for entry in component_entries),
                        original_scores=_mean_scores(entry.original for entry in component_entries),
                        normalized_scores=_mean_scores(
                            entry.normalized for entry in component_entries
                        ),
                        original_scale=(
                            f"{lexicon.metadata.source_scale_min:g} to "
                            f"{lexicon.metadata.source_scale_max:g}"
                        ),
                    )
                )

    comparisons = []
    vad_views = [row for row in views if row.normalized_scores is not None]
    if len(vad_views) >= 2:
        methods = {row.match_method for row in vad_views}
        if len(methods) > 1:
            notices.append(
                "The normalized spread includes more than one lookup method. "
                "Inspect the exact, lemma-derived, or mapped labels before treating the entries as equivalent."
            )
        for dimension in ("valence", "arousal", "dominance"):
            values = [
                float(getattr(row.normalized_scores, dimension))
                for row in vad_views
                if row.normalized_scores is not None
            ]
            spread = max(values) - min(values)
            agreement = "high" if spread <= 0.10 else "moderate" if spread <= 0.25 else "low"
            comparisons.append(
                CrossLexiconSpread(
                    dimension=dimension,
                    entry_count=len(values),
                    minimum=min(values),
                    maximum=max(values),
                    spread=spread,
                    descriptive_agreement=agreement,
                )
            )

    suggestions: tuple[str, ...] = ()
    if not views:
        source_terms: dict[str, str] = {}
        for lexicon in loaded:
            for key, entry in lexicon.entries.items():
                source_terms.setdefault(key, entry.source_term)
        close = get_close_matches(normalized, source_terms.keys(), n=8, cutoff=0.72)
        suggestions = tuple(source_terms[key] for key in close)
    return LexiconExplorerResult(
        query=raw_query,
        normalized_query=normalized,
        processing_lemma=lemma,
        processing_pos=pos,
        entries=tuple(views),
        component_averages=tuple(component_averages),
        comparisons=tuple(comparisons),
        suggestions=suggestions,
        notices=tuple(notices),
    )


def explore_lexicons(
    query: str,
    preprocessor: TextPreprocessor,
    *,
    mapped_query: str = "",
) -> LexiconExplorerResult:
    """Load and search every installed source, using the known source hashes."""

    return explore_loaded_lexicons(
        query,
        (load_lexicon(spec.lexicon_id) for spec in LEXICON_SPECS),
        preprocessor,
        mapped_query=mapped_query,
    )
