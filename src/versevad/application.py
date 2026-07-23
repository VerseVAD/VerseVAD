"""Framework-independent services for the beginner one-text workspace."""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from collections import Counter
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, Sequence

from versevad.adapters import (
    NrcEmotionAdapter,
    NrcEmotionIntensityAdapter,
    NrcVadV1Adapter,
    NrcVadV21Adapter,
    WarrinerVadAdapter,
)
from versevad.analysis.phase2 import analyze_lexicon, compare_lexicons
from versevad.exports.phase2_csv import export_phase2_csv
from versevad.models import (
    CrossLexiconComparison,
    MatchSelection,
    Phase2AnalysisResult,
    PhrasePolicy,
    ReviewRule,
    StopwordMode,
    TextDocument,
    TokenRecord,
)
from versevad.preprocessing import SpacyEnglishPreprocessor, TextPreprocessor, create_text_document
from versevad.stopwords import DEFAULT_PROTECTED_WORDS, build_stopword_policy


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "source_lexicons"
MAX_TEXT_BYTES = 5 * 1024 * 1024


class TextImportError(ValueError):
    """A plain-language error for an input that was not changed or analyzed."""


class WorkspaceAnalysisError(RuntimeError):
    """A plain-language failure raised before a result is presented as complete."""


@dataclass(frozen=True)
class LexiconSpec:
    lexicon_id: str
    display_name: str
    relative_path: Path
    expected_sha256: str
    short_description: str


LEXICON_SPECS = (
    LexiconSpec(
        "warriner_vad_2013",
        "Warriner VAD",
        Path("XANEW-master/XANEW-master/Ratings_Warriner_et_al.csv"),
        "78ac8107c78e116bb96538fae4faa47281a155f5f8fe39f30bbc6ea3db05b446",
        "Normative valence, arousal, and dominance on the original 1-9 scale, including exact multiword entries.",
    ),
    LexiconSpec(
        "nrc_vad_v1",
        "NRC VAD v1",
        Path("NRC-VAD-Lexicon/NRC-VAD-Lexicon/NRC-VAD-Lexicon.txt"),
        "fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7",
        "Earlier NRC VAD ratings on the original 0-1 scale.",
    ),
    LexiconSpec(
        "nrc_vad_v2_1",
        "NRC VAD v2.1",
        Path("NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt"),
        "42c718817fc91d5c133581b24b0bb31d2b14a0b16edb19bc6ce6ab70343e5a45",
        "Larger NRC VAD source with unigrams and multiword expressions on -1 to 1.",
    ),
    LexiconSpec(
        "nrc_emotion_v0_92",
        "NRC Emotion",
        Path(
            "NRC-Emotion-Lexicon/NRC-Emotion-Lexicon/"
            "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt"
        ),
        "02c661544f4f12ae0c14f9576a10959e8d39a151bb091e455a71a08dcaa2535a",
        "Binary word associations for eight emotions and positive/negative sentiment.",
    ),
    LexiconSpec(
        "nrc_emotion_intensity_v1",
        "NRC Emotion Intensity",
        Path(
            "NRC-Emotion-Intensity-Lexicon/NRC-Emotion-Intensity-Lexicon/"
            "NRC-Emotion-Intensity-Lexicon-v1.txt"
        ),
        "2bed5450b43134e4f849b013424eb76a76e2bdc0ec35df7ec0a0a477031239cb",
        "Category-specific 0-1 intensity ratings for supplied word-emotion pairs.",
    ),
)
LEXICON_SPEC_BY_ID = {spec.lexicon_id: spec for spec in LEXICON_SPECS}
ADAPTER_BY_ID = {
    "warriner_vad_2013": WarrinerVadAdapter,
    "nrc_vad_v1": NrcVadV1Adapter,
    "nrc_vad_v2_1": NrcVadV21Adapter,
    "nrc_emotion_v0_92": NrcEmotionAdapter,
    "nrc_emotion_intensity_v1": NrcEmotionIntensityAdapter,
}


@dataclass(frozen=True)
class AnalysisRequest:
    project_name: str
    title: str
    original_text: str
    lexicon_ids: tuple[str, ...]
    phrase_policy: PhrasePolicy = PhrasePolicy.PHRASE_PREFERRED
    minimum_match_requirement: int = 3
    text_id: str | None = None
    text_version_id: str | None = None
    stopword_mode: StopwordMode = StopwordMode.STANDARD
    protected_stopwords: tuple[str, ...] = DEFAULT_PROTECTED_WORDS
    custom_stopword_additions: tuple[str, ...] = ()
    custom_stopword_removals: tuple[str, ...] = ()
    scenario_id: str = "phase2-multi-lexicon-v1"
    scenario_version_id: str = ""
    review_rules: tuple[ReviewRule, ...] = ()


@dataclass(frozen=True)
class WorkspaceAnalysis:
    request: AnalysisRequest
    document: TextDocument
    results: tuple[Phase2AnalysisResult, ...]
    comparison: CrossLexiconComparison


@dataclass(frozen=True)
class CoverageView:
    lexicon_id: str
    lexicon: str
    value_kind: str
    matched_tokens: int
    lexical_tokens: int
    coverage: float | None
    matched_types: int
    total_types: int
    exact_matches: int
    lemma_matches: int
    phrase_matches: int
    note: str


PART_OF_SPEECH_LABELS = {
    "ADJ": "Adjective",
    "ADP": "Preposition",
    "ADV": "Adverb",
    "CCONJ": "Coordinating Conjunction",
    "DET": "Determiner",
    "INTJ": "Interjection",
    "NOUN": "Common Noun",
    "NOUN + PROPN": "Noun",
    "NUM": "Numeral",
    "PART": "Particle",
    "PRON": "Pronoun",
    "PROPN": "Proper Noun",
    "SCONJ": "Subordinating Conjunction",
    "SYM": "Symbol",
    "VERB": "Main Verb",
    "AUX": "Auxiliary or Copular Verb",
    "VERB + AUX": "Verb",
    "X": "Other or Uncertain",
}


@dataclass(frozen=True)
class PartOfSpeechView:
    tag: str
    category: str
    token_count: int
    share_of_lexical_tokens: float
    unique_type_count: int
    example_forms: str
    lexical_token_denominator: int


@dataclass(frozen=True)
class VadView:
    lexicon_id: str
    lexicon: str
    analysis_view: str
    matched_observations: int
    matched_types: int
    eligible_tokens: int
    lexical_coverage: float | None
    normalized_valence: float | None
    normalized_arousal: float | None
    normalized_dominance: float | None
    type_valence: float | None
    type_arousal: float | None
    type_dominance: float | None
    original_scale: str
    normalization_formula: str


VAD_DEFINITIONS = {
    "valence": (
        "Normative pleasantness: lower ratings are associated with more unpleasant "
        "vocabulary and higher ratings with more pleasant vocabulary."
    ),
    "arousal": (
        "Normative activation or energy—not specifically sexual arousal. Lower "
        "ratings are calmer or more subdued; higher ratings are more activated, "
        "alert, excited, or agitated."
    ),
    "dominance": (
        "Normative power, control, or agency. Lower ratings are associated with "
        "constraint or vulnerability; higher ratings with greater control or power."
    ),
}


def part_of_speech_views_for_tokens(
    tokens: Sequence[TokenRecord],
) -> tuple[PartOfSpeechView, ...]:
    """Summarize broad, reader-facing POS families over lexical tokens."""

    return _part_of_speech_views_for_tokens(tokens, merge_broad_categories=True)


def detailed_part_of_speech_views_for_tokens(
    tokens: Sequence[TokenRecord],
) -> tuple[PartOfSpeechView, ...]:
    """Preserve the model's universal POS tags as a separate audit view."""

    return _part_of_speech_views_for_tokens(tokens, merge_broad_categories=False)


def _part_of_speech_views_for_tokens(
    tokens: Sequence[TokenRecord],
    *,
    merge_broad_categories: bool,
) -> tuple[PartOfSpeechView, ...]:
    lexical_tokens = tuple(token for token in tokens if token.is_lexical)
    denominator = len(lexical_tokens)
    if not denominator:
        return ()
    by_tag: dict[str, list[TokenRecord]] = {}
    for token in lexical_tokens:
        source_tag = token.part_of_speech or "X"
        if merge_broad_categories and source_tag in {"NOUN", "PROPN"}:
            tag = "NOUN + PROPN"
        elif merge_broad_categories and source_tag in {"VERB", "AUX"}:
            tag = "VERB + AUX"
        else:
            tag = source_tag
        by_tag.setdefault(tag, []).append(token)
    rows = []
    for tag, tagged_tokens in by_tag.items():
        forms = Counter(
            token.normalized_form or token.surface_form.casefold()
            for token in tagged_tokens
        )
        examples = ", ".join(
            form
            for form, _frequency in sorted(
                forms.items(),
                key=lambda item: (-item[1], item[0]),
            )[:6]
        )
        rows.append(
            PartOfSpeechView(
                tag=tag,
                category=PART_OF_SPEECH_LABELS.get(tag, tag.title()),
                token_count=len(tagged_tokens),
                share_of_lexical_tokens=len(tagged_tokens) / denominator,
                unique_type_count=len(forms),
                example_forms=examples,
                lexical_token_denominator=denominator,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (-row.token_count, row.category, row.tag),
        )
    )


def part_of_speech_views(
    workspace: WorkspaceAnalysis,
) -> tuple[PartOfSpeechView, ...]:
    """Return a lexicon-independent POS profile for one analyzed text."""

    if not workspace.results:
        return ()
    return part_of_speech_views_for_tokens(workspace.results[0].tokens)


def detailed_part_of_speech_views(
    workspace: WorkspaceAnalysis,
) -> tuple[PartOfSpeechView, ...]:
    """Return the unmerged universal-tag profile for one analyzed text."""

    if not workspace.results:
        return ()
    return detailed_part_of_speech_views_for_tokens(workspace.results[0].tokens)


@dataclass(frozen=True)
class VadInterpretationView:
    lexicon_id: str
    lexicon: str
    analysis_view: str
    dimension: str
    mean: float
    matched_observations: int
    lexical_coverage: float | None
    relation_to_midpoint: str
    explanation: str


@dataclass(frozen=True)
class VadContributorView:
    lexicon_id: str
    lexicon: str
    analysis_view: str
    dimension: str
    term: str
    surface_forms: str
    observations: int
    normalized_rating: float
    original_rating: float
    midpoint_deviation_per_occurrence: float
    signed_contribution: float
    absolute_contribution: float
    effect_on_mean: float | None
    direction: str
    stopword_status: str
    example_surface: str
    example_line: int
    example_context: str
    match_method: str


@dataclass(frozen=True)
class VadCumulativeView:
    """Length-sensitive token totals on the derived 0-1 VAD scale."""

    lexicon_id: str
    lexicon: str
    analysis_view: str
    dimension: str
    matched_observations: int
    lexical_tokens: int
    lexical_coverage: float | None
    rating_total: float
    above_midpoint_deviation: float
    below_midpoint_deviation: float
    net_midpoint_deviation: float
    absolute_midpoint_deviation: float


@dataclass(frozen=True)
class VadSensitivityView:
    lexicon_id: str
    lexicon: str
    weighting: str
    dimension: str
    all_matched_mean: float | None
    stopwords_excluded_mean: float | None
    difference: float | None


@dataclass(frozen=True)
class EmotionAssociationView:
    category: str
    token_count: int
    unique_types: int
    rate_per_lexical_token: float | None
    rate_among_emotion_bearing_tokens: float | None
    top_terms: str


@dataclass(frozen=True)
class EmotionIntensityView:
    category: str
    token_count: int
    distinct_pairs: int
    prevalence_per_lexical_token: float | None
    mean_matched_intensity: float | None
    median_matched_intensity: float | None
    maximum_matched_intensity: float | None
    top_terms: str


@dataclass(frozen=True)
class MatchView:
    lexicon_id: str
    lexicon: str
    surface: str
    normalized: str
    line: int
    stanza: int
    pos: str
    lemma: str
    matched_term: str
    method: str
    status: str
    value: str
    context: str
    explanation: str
    stopword_status: str
    included_in_full: bool
    included_in_filtered: bool
    stopword_exclusion_reason: str


@dataclass(frozen=True)
class UnmatchedView:
    lexicon_id: str
    lexicon: str
    surface: str
    normalized_form: str
    frequency: int
    pos: str
    proposed_lemma: str
    example_line: int
    example_context: str


def decode_uploaded_text(filename: str, content: bytes) -> str:
    """Decode a private UTF-8 plain-text file without rewriting its content."""

    if not filename.lower().endswith(".txt"):
        raise TextImportError(
            "Phase 3 accepts UTF-8 plain-text (.txt) files. Save this poem as a "
            ".txt file or paste it into the text box."
        )
    if len(content) > MAX_TEXT_BYTES:
        raise TextImportError(
            "This file is larger than the 5 MB Phase 3 safety limit. No text was imported."
        )
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise TextImportError(
            "VerseVAD could not read this file as UTF-8. Save a UTF-8 copy or "
            "paste the text directly; the original file was not changed."
        ) from error
    if "\x00" in text:
        raise TextImportError(
            "This does not appear to be an ordinary plain-text file. No text was imported."
        )
    return text


def _adapter(lexicon_id: str):
    try:
        return ADAPTER_BY_ID[lexicon_id]()
    except KeyError as error:
        raise WorkspaceAnalysisError(f"Unknown lexicon selection: {lexicon_id}") from error


@lru_cache(maxsize=10)
def load_lexicon(lexicon_id: str, source_root: str = str(SOURCE_ROOT)):
    spec = LEXICON_SPEC_BY_ID.get(lexicon_id)
    if spec is None:
        raise WorkspaceAnalysisError(f"Unknown lexicon selection: {lexicon_id}")
    lexicon = _adapter(lexicon_id).load(Path(source_root) / spec.relative_path)
    if lexicon.validation.source_sha256 != spec.expected_sha256:
        raise WorkspaceAnalysisError(
            f"{spec.display_name} does not match the source inspected during setup. "
            "No analysis was run. Restore the original source file, then retry."
        )
    return lexicon


def run_workspace_analysis(
    request: AnalysisRequest,
    *,
    preprocessor: TextPreprocessor | None = None,
    source_root: Path = SOURCE_ROOT,
) -> WorkspaceAnalysis:
    if not request.title.strip():
        raise WorkspaceAnalysisError("Enter a title or working label for this text.")
    if not request.original_text.strip():
        raise WorkspaceAnalysisError("Paste a poem or choose a UTF-8 text file before analyzing.")
    if not request.lexicon_ids:
        raise WorkspaceAnalysisError("Select at least one lexicon before analyzing.")
    unknown = set(request.lexicon_ids) - set(LEXICON_SPEC_BY_ID)
    if unknown:
        raise WorkspaceAnalysisError(f"Unknown lexicon selection: {sorted(unknown)}")
    if request.minimum_match_requirement < 1:
        raise WorkspaceAnalysisError("The minimum matched-item setting must be at least 1.")

    identity = hashlib.sha256(
        f"{request.project_name}|{request.title}".encode("utf-8")
    ).hexdigest()[:16]
    document = create_text_document(
        text_id=request.text_id or f"workspace-{identity}",
        title=request.title.strip(),
        original_text=request.original_text,
    )
    if request.text_version_id is not None:
        document = replace(document, text_version_id=request.text_version_id)
    processor = preprocessor or SpacyEnglishPreprocessor()
    try:
        stopword_policy = build_stopword_policy(
            mode=request.stopword_mode,
            protected_words=request.protected_stopwords,
            custom_additions=request.custom_stopword_additions,
            custom_removals=request.custom_stopword_removals,
        )
    except ValueError as error:
        raise WorkspaceAnalysisError(str(error)) from error
    results = tuple(
        analyze_lexicon(
            document,
            load_lexicon(lexicon_id, str(source_root.resolve())),
            processor,
            phrase_policy=request.phrase_policy,
            minimum_match_requirement=request.minimum_match_requirement,
            stopword_policy=stopword_policy,
            scenario_id=request.scenario_id,
            scenario_version_id=request.scenario_version_id,
            review_rules=request.review_rules,
        )
        for lexicon_id in request.lexicon_ids
    )
    return WorkspaceAnalysis(request, document, results, compare_lexicons(results))


def coverage_views(workspace: WorkspaceAnalysis) -> tuple[CoverageView, ...]:
    rows = []
    for result in workspace.results:
        coverage = result.coverage.lexical_token_coverage
        if coverage is None:
            note = "No lexical tokens were available."
        elif coverage >= 0.8:
            note = "At least 80% of lexical tokens matched under this policy."
        elif coverage >= 0.6:
            note = "Between 60% and 80% of lexical tokens matched; inspect unmatched terms."
        else:
            note = "Fewer than 60% matched; interpret aggregates cautiously."
        rows.append(
            CoverageView(
                lexicon_id=result.lexicon_metadata.lexicon_id,
                lexicon=result.lexicon_metadata.display_name,
                value_kind=result.lexicon_metadata.value_kind.value,
                matched_tokens=result.coverage.matched_token_count,
                lexical_tokens=result.coverage.total_lexical_tokens,
                coverage=coverage,
                matched_types=result.coverage.matched_type_count,
                total_types=result.coverage.total_unique_types,
                exact_matches=result.coverage.exact_match_count,
                lemma_matches=result.coverage.lemma_fallback_count,
                phrase_matches=result.coverage.phrase_match_count,
                note=note,
            )
        )
    return tuple(rows)


def vad_views(workspace: WorkspaceAnalysis) -> tuple[VadView, ...]:
    rows = []
    for result in workspace.results:
        summary = result.vad_summary
        if summary is None:
            continue
        metadata = result.lexicon_metadata
        filtered_token = summary.stopword_excluded_token_weighted_normalized
        filtered_type = summary.stopword_excluded_type_weighted_normalized
        view_groups = [
            (
                "All matched tokens",
                summary.token_weighted_normalized,
                summary.type_weighted_normalized,
                result.coverage.matched_type_count,
                result.coverage.total_lexical_tokens,
                result.coverage.lexical_token_coverage,
            )
        ]
        if (
            filtered_token is not None
            and filtered_type is not None
            and result.stopword_coverage is not None
        ):
            view_groups.append(
                (
                    "Stopwords excluded",
                    filtered_token,
                    filtered_type,
                    result.stopword_coverage.matched_type_count,
                    result.stopword_coverage.eligible_token_count,
                    result.stopword_coverage.lexical_token_coverage,
                )
            )
        for (
            analysis_view,
            token,
            kind,
            matched_types,
            eligible_tokens,
            coverage,
        ) in view_groups:
            rows.append(
                VadView(
                    lexicon_id=metadata.lexicon_id,
                    lexicon=metadata.display_name,
                    analysis_view=analysis_view,
                    matched_observations=token.valence.count,
                    matched_types=matched_types,
                    eligible_tokens=eligible_tokens,
                    lexical_coverage=coverage,
                    normalized_valence=token.valence.mean,
                    normalized_arousal=token.arousal.mean,
                    normalized_dominance=token.dominance.mean,
                    type_valence=kind.valence.mean,
                    type_arousal=kind.arousal.mean,
                    type_dominance=kind.dominance.mean,
                    original_scale=(
                        f"{metadata.source_scale_min:g} to "
                        f"{metadata.source_scale_max:g}"
                    ),
                    normalization_formula=metadata.normalization_formula,
                )
            )
    return tuple(rows)


def vad_interpretation_views(
    workspace: WorkspaceAnalysis,
) -> tuple[VadInterpretationView, ...]:
    """Explain normalized VAD means without making contextual emotion claims."""

    rows = []
    for view in vad_views(workspace):
        values = {
            "valence": view.normalized_valence,
            "arousal": view.normalized_arousal,
            "dominance": view.normalized_dominance,
        }
        for dimension, value in values.items():
            if value is None:
                continue
            if value > 0.5:
                relation = "above"
            elif value < 0.5:
                relation = "below"
            else:
                relation = "at"
            coverage_text = (
                "Coverage was unavailable"
                if view.lexical_coverage is None
                else f"Lexical-token coverage was {view.lexical_coverage:.1%}"
            )
            rows.append(
                VadInterpretationView(
                    lexicon_id=view.lexicon_id,
                    lexicon=view.lexicon,
                    analysis_view=view.analysis_view,
                    dimension=dimension,
                    mean=value,
                    matched_observations=view.matched_observations,
                    lexical_coverage=view.lexical_coverage,
                    relation_to_midpoint=relation,
                    explanation=(
                        f"{view.analysis_view}: mean normative {dimension} among "
                        f"{view.matched_observations} "
                        f"included matched observations was {value:.3f}, {relation} "
                        f"the 0.5 midpoint of the derived display scale. {coverage_text}. "
                        "This describes matched lexical ratings, not the poem or speaker."
                    ),
                )
            )
    return tuple(rows)


def vad_sensitivity_views(
    workspace: WorkspaceAnalysis,
) -> tuple[VadSensitivityView, ...]:
    """Compare filtered minus full means without preferring either view."""

    rows: list[VadSensitivityView] = []
    for result in workspace.results:
        summary = result.vad_summary
        if summary is None:
            continue
        groups = (
            (
                "token",
                summary.token_weighted_normalized,
                summary.stopword_excluded_token_weighted_normalized,
            ),
            (
                "type",
                summary.type_weighted_normalized,
                summary.stopword_excluded_type_weighted_normalized,
            ),
        )
        for weighting, all_group, filtered_group in groups:
            if filtered_group is None:
                continue
            for dimension in ("valence", "arousal", "dominance"):
                all_mean = getattr(all_group, dimension).mean
                filtered_mean = getattr(filtered_group, dimension).mean
                difference = (
                    filtered_mean - all_mean
                    if all_mean is not None and filtered_mean is not None
                    else None
                )
                rows.append(
                    VadSensitivityView(
                        lexicon_id=result.lexicon_metadata.lexicon_id,
                        lexicon=result.lexicon_metadata.display_name,
                        weighting=weighting,
                        dimension=dimension,
                        all_matched_mean=all_mean,
                        stopwords_excluded_mean=filtered_mean,
                        difference=difference,
                    )
                )
    return tuple(rows)


def vad_contributor_views(
    workspace: WorkspaceAnalysis,
    *,
    per_direction: int = 5,
) -> tuple[VadContributorView, ...]:
    """Return midpoint-centered term contributions for both VAD views."""

    if per_direction < 1:
        raise ValueError("per_direction must be at least 1")
    rows: list[VadContributorView] = []
    for result in workspace.results:
        summary = result.vad_summary
        if summary is None:
            continue
        all_included = tuple(
            match
            for match in result.matches
            if match.included
            and match.normalized_scores is not None
            and match.original_scores is not None
            and match.matched_term is not None
        )
        if not all_included:
            continue
        token_map = {token.token_id: token for token in result.tokens}
        analysis_groups = (
            (
                "All matched tokens",
                all_included,
                summary.token_weighted_normalized,
            ),
            (
                "Stopwords excluded",
                tuple(
                    match for match in all_included if match.included_in_stopword_view
                ),
                summary.stopword_excluded_token_weighted_normalized,
            ),
        )
        for analysis_view, included, statistics_group in analysis_groups:
            if not included or statistics_group is None:
                continue
            means = {
                dimension: statistics.mean
                for dimension, statistics in statistics_group.by_dimension().items()
            }
            for dimension, mean in means.items():
                if mean is None:
                    continue
                grouped: dict[str, list] = {}
                for match in included:
                    grouped.setdefault(match.matched_term or "", []).append(match)
                dimension_rows = []
                total = len(included)
                for term, matches in grouped.items():
                    first_match = matches[0]
                    normalized_rating = getattr(first_match.normalized_scores, dimension)
                    original_rating = getattr(first_match.original_scores, dimension)
                    count = len(matches)
                    midpoint_deviation = normalized_rating - 0.5
                    signed_contribution = count * midpoint_deviation
                    effect = None
                    if total > count:
                        mean_without = (
                            mean * total - normalized_rating * count
                        ) / (total - count)
                        effect = mean - mean_without
                    if signed_contribution > 0:
                        direction = "above-midpoint weighted deviation"
                    elif signed_contribution < 0:
                        direction = "below-midpoint weighted deviation"
                    else:
                        direction = "at midpoint"
                    first_tokens = tuple(
                        token_map[token_id] for token_id in first_match.token_ids
                    )
                    surface_forms = sorted(
                        {
                            " ".join(
                                token_map[token_id].surface_form
                                for token_id in match.token_ids
                            )
                            for match in matches
                        },
                        key=str.casefold,
                    )
                    dimension_rows.append(
                        VadContributorView(
                            lexicon_id=result.lexicon_metadata.lexicon_id,
                            lexicon=result.lexicon_metadata.display_name,
                            analysis_view=analysis_view,
                            dimension=dimension,
                            term=term,
                            surface_forms=", ".join(surface_forms),
                            observations=count,
                            normalized_rating=normalized_rating,
                            original_rating=original_rating,
                            midpoint_deviation_per_occurrence=midpoint_deviation,
                            signed_contribution=signed_contribution,
                            absolute_contribution=abs(signed_contribution),
                            effect_on_mean=effect,
                            direction=direction,
                            stopword_status=", ".join(
                                sorted(
                                    {match.stopword_status for match in matches},
                                    key=str.casefold,
                                )
                            ),
                            example_surface=" ".join(
                                token.surface_form for token in first_tokens
                            ),
                            example_line=first_match.line_number,
                            example_context=first_tokens[0].context,
                            match_method=first_match.method.value,
                        )
                    )
                positive = sorted(
                    (row for row in dimension_rows if row.signed_contribution > 0),
                    key=lambda row: (
                        -row.signed_contribution,
                        row.term.casefold(),
                    ),
                )[:per_direction]
                negative = sorted(
                    (row for row in dimension_rows if row.signed_contribution < 0),
                    key=lambda row: (
                        row.signed_contribution,
                        row.term.casefold(),
                    ),
                )[:per_direction]
                neutral = [
                    row for row in dimension_rows if row.signed_contribution == 0
                ][:per_direction]
                rows.extend((*positive, *negative, *neutral))
    return tuple(rows)


def vad_cumulative_views(
    workspace: WorkspaceAnalysis,
) -> tuple[VadCumulativeView, ...]:
    """Return length-sensitive token totals without claiming reader response.

    Each included match contributes once. For an activated multiword expression,
    the phrase is one matched observation, consistent with the analysis policy.
    Unmatched tokens remain missing and contribute neither a score nor a zero.
    """

    rows: list[VadCumulativeView] = []
    for result in workspace.results:
        if result.vad_summary is None:
            continue
        all_included = tuple(
            match
            for match in result.matches
            if match.included and match.normalized_scores is not None
        )
        analysis_groups = [
            (
                "All matched tokens",
                all_included,
                result.coverage.total_lexical_tokens,
                result.coverage.lexical_token_coverage,
            )
        ]
        if result.stopword_coverage is not None:
            analysis_groups.append(
                (
                    "Stopwords excluded",
                    tuple(
                        match
                        for match in all_included
                        if match.included_in_stopword_view
                    ),
                    result.stopword_coverage.eligible_token_count,
                    result.stopword_coverage.lexical_token_coverage,
                )
            )
        for analysis_view, included, lexical_tokens, lexical_coverage in analysis_groups:
            for dimension in ("valence", "arousal", "dominance"):
                values = [
                    float(getattr(match.normalized_scores, dimension))
                    for match in included
                    if match.normalized_scores is not None
                ]
                if not values:
                    continue
                above = sum(max(value - 0.5, 0.0) for value in values)
                below = sum(max(0.5 - value, 0.0) for value in values)
                rows.append(
                    VadCumulativeView(
                        lexicon_id=result.lexicon_metadata.lexicon_id,
                        lexicon=result.lexicon_metadata.display_name,
                        analysis_view=analysis_view,
                        dimension=dimension,
                        matched_observations=len(values),
                        lexical_tokens=lexical_tokens,
                        lexical_coverage=lexical_coverage,
                        rating_total=sum(values),
                        above_midpoint_deviation=above,
                        below_midpoint_deviation=below,
                        net_midpoint_deviation=above - below,
                        absolute_midpoint_deviation=above + below,
                    )
                )
    return tuple(rows)


def emotion_association_views(
    workspace: WorkspaceAnalysis,
) -> tuple[EmotionAssociationView, ...]:
    return _association_views(
        workspace,
        {
            "anger",
            "anticipation",
            "disgust",
            "fear",
            "joy",
            "sadness",
            "surprise",
            "trust",
        },
    )


def sentiment_association_views(
    workspace: WorkspaceAnalysis,
) -> tuple[EmotionAssociationView, ...]:
    """Keep positive/negative sentiment distinct from the eight emotions."""

    return _association_views(workspace, {"positive", "negative"})


def _association_views(
    workspace: WorkspaceAnalysis,
    categories: set[str],
) -> tuple[EmotionAssociationView, ...]:
    rows = []
    for result in workspace.results:
        for stats in result.category_statistics:
            if stats.category not in categories:
                continue
            rows.append(
                EmotionAssociationView(
                    category=stats.category,
                    token_count=stats.associated_token_count,
                    unique_types=stats.associated_unique_type_count,
                    rate_per_lexical_token=stats.proportion_of_lexical_tokens,
                    rate_among_emotion_bearing_tokens=(
                        stats.proportion_of_matched_emotion_bearing_tokens
                    ),
                    top_terms=", ".join(item.term for item in stats.top_contributing_terms[:5]),
                )
            )
    return tuple(rows)


def emotion_intensity_views(
    workspace: WorkspaceAnalysis,
) -> tuple[EmotionIntensityView, ...]:
    rows = []
    for result in workspace.results:
        for stats in result.intensity_statistics:
            rows.append(
                EmotionIntensityView(
                    category=stats.category,
                    token_count=stats.matched_token_occurrences,
                    distinct_pairs=stats.matched_word_emotion_pairs,
                    prevalence_per_lexical_token=stats.prevalence_among_lexical_tokens,
                    mean_matched_intensity=stats.token_weighted.mean,
                    median_matched_intensity=stats.token_weighted.median,
                    maximum_matched_intensity=stats.token_weighted.maximum,
                    top_terms=", ".join(item.term for item in stats.top_contributing_terms[:5]),
                )
            )
    return tuple(rows)


def _match_value(match) -> str:
    if match.normalized_scores is not None:
        scores = match.normalized_scores
        return f"V {scores.valence:.3f}; A {scores.arousal:.3f}; D {scores.dominance:.3f} (0-1)"
    if match.associations:
        return ", ".join(match.associations)
    if match.intensities:
        return "; ".join(f"{name} {value:.3f}" for name, value in match.intensities)
    return ""


def match_views(workspace: WorkspaceAnalysis) -> tuple[MatchView, ...]:
    rows = []
    for result in workspace.results:
        token_map = {token.token_id: token for token in result.tokens}
        for match in result.matches:
            tokens = tuple(token_map[token_id] for token_id in match.token_ids)
            first = tokens[0]
            rows.append(
                MatchView(
                    lexicon_id=result.lexicon_metadata.lexicon_id,
                    lexicon=result.lexicon_metadata.display_name,
                    surface=" ".join(token.surface_form for token in tokens),
                    normalized=" ".join(token.normalized_form for token in tokens),
                    line=match.line_number,
                    stanza=match.stanza_number,
                    pos=" + ".join(token.part_of_speech for token in tokens),
                    lemma=" ".join(token.lemma for token in tokens),
                    matched_term=match.matched_term or "",
                    method=match.method.value,
                    status=match.selection.value,
                    value=_match_value(match),
                    context=first.context,
                    explanation=match.reason,
                    stopword_status=match.stopword_status,
                    included_in_full=match.included,
                    included_in_filtered=match.included_in_stopword_view,
                    stopword_exclusion_reason=match.stopword_exclusion_reason,
                )
            )
    return tuple(rows)


def unmatched_views(workspace: WorkspaceAnalysis) -> tuple[UnmatchedView, ...]:
    grouped: dict[tuple[str, str, str, str, str], list[tuple[int, str]]] = {}
    display_names = {
        result.lexicon_metadata.lexicon_id: result.lexicon_metadata.display_name
        for result in workspace.results
    }
    for result in workspace.results:
        token_map = {token.token_id: token for token in result.tokens}
        for match in result.matches:
            if match.selection != MatchSelection.UNMATCHED or len(match.token_ids) != 1:
                continue
            token = token_map[match.token_ids[0]]
            if not token.is_lexical:
                continue
            key = (
                match.lexicon_id,
                token.surface_form,
                token.normalized_form,
                token.part_of_speech,
                token.lemma,
            )
            grouped.setdefault(key, []).append((token.line_number, token.context))
    rows = []
    for (lexicon_id, surface, normalized_form, pos, lemma), examples in grouped.items():
        rows.append(
            UnmatchedView(
                lexicon_id=lexicon_id,
                lexicon=display_names[lexicon_id],
                surface=surface,
                normalized_form=normalized_form,
                frequency=len(examples),
                pos=pos,
                proposed_lemma=lemma,
                example_line=examples[0][0],
                example_context=examples[0][1],
            )
        )
    return tuple(sorted(rows, key=lambda row: (row.lexicon, -row.frequency, row.surface.casefold())))


def overview_notes(workspace: WorkspaceAnalysis) -> tuple[str, ...]:
    notes = [
        "Every number describes lexical evidence under the selected matching policy, not the emotion of the poem or its speaker.",
        "Coverage tells you how much eligible vocabulary contributed. Compare scores only alongside matched counts and coverage.",
    ]
    vad = vad_views(workspace)
    if vad:
        notes.append(
            "The VAD comparison uses separately derived 0-1 values. Original source scales and formulas remain available."
        )
    if emotion_association_views(workspace):
        notes.append(
            "The eight emotion associations are multi-label categories, so their "
            "percentages are not expected to sum to 100%. Positive/negative "
            "sentiment is reported separately."
        )
    if emotion_intensity_views(workspace):
        notes.append(
            "Emotion intensity means use only supplied word-emotion pairs; missing pairs are not treated as zero."
        )
    if workspace.request.scenario_version_id:
        notes.append(
            f"This is a reviewed scenario result pinned to "
            f"{workspace.request.scenario_version_id} with "
            f"{len(workspace.request.review_rules)} active decision revision(s). "
            "The unreviewed baseline remains separate."
        )
    return tuple(notes)


def _csv_bytes(fieldnames: list[str], rows: Iterable[dict[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return b"\xef\xbb\xbf" + output.getvalue().encode("utf-8")


def scholar_summary_csv(workspace: WorkspaceAnalysis) -> bytes:
    fields = [
        "section",
        "lexicon",
        "analysis_view",
        "metric",
        "value",
        "unit_or_scale",
        "denominator",
        "plain_language_note",
    ]
    rows: list[dict[str, object]] = []
    if workspace.request.scenario_version_id:
        rows.extend(
            (
                {
                    "section": "Review methodology",
                    "lexicon": "",
                    "analysis_view": "Reviewed scenario",
                    "metric": "Scenario version ID",
                    "value": workspace.request.scenario_version_id,
                    "unit_or_scale": "stable local identifier",
                    "denominator": "",
                    "plain_language_note": (
                        "This immutable result uses the exact decision revisions "
                        "listed in the detailed manifest."
                    ),
                },
                {
                    "section": "Review methodology",
                    "lexicon": "",
                    "analysis_view": "Reviewed scenario",
                    "metric": "Active review decision revisions",
                    "value": len(workspace.request.review_rules),
                    "unit_or_scale": "count",
                    "denominator": "",
                    "plain_language_note": (
                        "Flags are non-scoring; mappings and exclusions apply only "
                        "within this scenario."
                    ),
                },
            )
        )
    for pos in part_of_speech_views(workspace):
        rows.append(
            {
                "section": "Part of speech",
                "lexicon": "spaCy English linguistic model",
                "analysis_view": "All eligible lexical tokens",
                "metric": f"{pos.category} share",
                "value": pos.share_of_lexical_tokens,
                "unit_or_scale": "proportion",
                "denominator": (
                    f"{pos.token_count} of {pos.lexical_token_denominator} "
                    "lexical token occurrences"
                ),
                "plain_language_note": (
                    f"Source POS tag(s) {pos.tag}; {pos.unique_type_count} unique "
                    f"normalized type(s). Examples: {pos.example_forms or 'none'}. "
                    "Labels are model-generated and may be uncertain in poetic syntax."
                ),
            }
        )
    for coverage in coverage_views(workspace):
        rows.append(
            {
                "section": "Coverage",
                "lexicon": coverage.lexicon,
                "analysis_view": "All matched tokens",
                "metric": "Lexical-token coverage",
                "value": coverage.coverage if coverage.coverage is not None else "",
                "unit_or_scale": "proportion",
                "denominator": f"{coverage.lexical_tokens} lexical tokens",
                "plain_language_note": coverage.note,
            }
        )
    for result in workspace.results:
        if result.stopword_coverage is None:
            continue
        coverage = result.stopword_coverage
        rows.append(
            {
                "section": "Coverage",
                "lexicon": result.lexicon_metadata.display_name,
                "analysis_view": "Stopwords excluded",
                "metric": "Content-focused lexical coverage",
                "value": (
                    coverage.lexical_token_coverage
                    if coverage.lexical_token_coverage is not None
                    else ""
                ),
                "unit_or_scale": "proportion",
                "denominator": (
                    f"{coverage.eligible_token_count} eligible non-stopword, "
                    "non-review-excluded tokens"
                ),
                "plain_language_note": (
                    "Intentionally excluded stopwords and scenario exclusions are "
                    "removed from this secondary denominator."
                ),
            }
        )
    contributors = vad_contributor_views(workspace, per_direction=3)
    for row in vad_views(workspace):
        dimensions = (
            ("valence", row.normalized_valence, row.type_valence),
            ("arousal", row.normalized_arousal, row.type_arousal),
            ("dominance", row.normalized_dominance, row.type_dominance),
        )
        for dimension, token_value, type_value in dimensions:
            terms = [
                item
                for item in contributors
                if item.lexicon_id == row.lexicon_id
                and item.analysis_view == row.analysis_view
                and item.dimension == dimension
            ]
            contributor_note = "; ".join(
                f"{item.term} ({item.signed_contribution:+.3f} weighted deviation)"
                for item in terms
            )
            for weighting, value in (("token", token_value), ("type", type_value)):
                rows.append(
                    {
                        "section": "Normalized VAD",
                        "lexicon": row.lexicon,
                        "analysis_view": row.analysis_view,
                        "metric": f"Mean normative {dimension} ({weighting}-weighted)",
                        "value": value if value is not None else "",
                        "unit_or_scale": "derived 0-1",
                        "denominator": (
                            f"{row.matched_observations} included matched observations"
                            if weighting == "token"
                            else "distinct matched lexicon entries"
                        ),
                        "plain_language_note": (
                            f"Top token-mean contributors: {contributor_note or 'not available'}. "
                            "Original values and formula remain in the detailed audit."
                        ),
                    }
                )
    for row in vad_cumulative_views(workspace):
        for label, value in (
            ("Rating total", row.rating_total),
            ("Above-midpoint load", row.above_midpoint_deviation),
            ("Below-midpoint load", row.below_midpoint_deviation),
            ("Net midpoint load", row.net_midpoint_deviation),
            ("Absolute midpoint load", row.absolute_midpoint_deviation),
        ):
            rows.append(
                {
                    "section": "Cumulative normative lexical load",
                    "lexicon": row.lexicon,
                    "analysis_view": row.analysis_view,
                    "metric": f"{row.dimension.title()} — {label}",
                    "value": value,
                    "unit_or_scale": "length-sensitive token sum on derived 0-1 scale",
                    "denominator": f"{row.matched_observations} included matched observations",
                    "plain_language_note": (
                        "Describes cumulative lexical evidence, not a measured effect on a reader."
                    ),
                }
            )
    for row in vad_sensitivity_views(workspace):
        rows.append(
            {
                "section": "Stopword sensitivity",
                "lexicon": row.lexicon,
                "analysis_view": "Filtered minus full",
                "metric": (
                    f"Mean normative {row.dimension} difference "
                    f"({row.weighting}-weighted)"
                ),
                "value": row.difference if row.difference is not None else "",
                "unit_or_scale": "derived 0-1 difference",
                "denominator": "stopword-excluded mean minus all-matched mean",
                "plain_language_note": (
                    "A larger absolute difference indicates greater sensitivity to "
                    "common grammatical words; neither view is labeled more accurate."
                ),
            }
        )
    for row in emotion_association_views(workspace):
        rows.append(
            {
                "section": "Emotion association",
                "lexicon": "NRC Emotion",
                "analysis_view": "All matched tokens",
                "metric": f"{row.category} association rate",
                "value": row.rate_per_lexical_token if row.rate_per_lexical_token is not None else "",
                "unit_or_scale": "proportion",
                "denominator": "all lexical tokens",
                "plain_language_note": f"Contributors: {row.top_terms or 'none'}",
            }
        )
    for row in sentiment_association_views(workspace):
        rows.append(
            {
                "section": "Sentiment association",
                "lexicon": "NRC Emotion",
                "analysis_view": "All matched tokens",
                "metric": f"{row.category} sentiment-association rate",
                "value": (
                    row.rate_per_lexical_token
                    if row.rate_per_lexical_token is not None
                    else ""
                ),
                "unit_or_scale": "proportion",
                "denominator": "all lexical tokens",
                "plain_language_note": (
                    f"Contributors: {row.top_terms or 'none'}. Sentiment is "
                    "presented separately from the eight emotion categories."
                ),
            }
        )
    for row in emotion_intensity_views(workspace):
        rows.append(
            {
                "section": "Emotion intensity",
                "lexicon": "NRC Emotion Intensity",
                "analysis_view": "All matched tokens",
                "metric": f"Mean matched {row.category} intensity",
                "value": row.mean_matched_intensity if row.mean_matched_intensity is not None else "",
                "unit_or_scale": "source 0-1",
                "denominator": f"{row.token_count} matched {row.category} occurrences",
                "plain_language_note": "Absent word-emotion pairs are missing, not zero.",
            }
        )
    return _csv_bytes(fields, rows)


def csv_reading_guide() -> bytes:
    fields = ["file", "what_it_answers", "start_with", "important_caution"]
    rows = [
        {
            "file": "scholar_summary.csv",
            "what_it_answers": "What are the principal readable results?",
            "start_with": "Coverage, token/type VAD means, cumulative load, contributors, association rates, and matched intensity means.",
            "important_caution": "Read every metric with its denominator and plain-language note.",
        },
        {
            "file": "phase2_coverage.csv",
            "what_it_answers": "How much vocabulary matched each source?",
            "start_with": "lexical_token_coverage and matched_token_count.",
            "important_caution": "Coverage differs by lexicon and matching policy.",
        },
        {
            "file": "phase2_vad_summary.csv",
            "what_it_answers": "What are the VAD distributions?",
            "start_with": "token weighting plus normalized_0_1 scale.",
            "important_caution": "Source and normalized scales are separate; unmatched tokens are absent.",
        },
        {
            "file": "phase2_emotion_associations.csv",
            "what_it_answers": "Which categorical associations occur?",
            "start_with": "proportion_of_lexical_tokens and top_contributing_terms.",
            "important_caution": "A token may have several associations; rates need not sum to 100%.",
        },
        {
            "file": "phase2_emotion_intensity.csv",
            "what_it_answers": "How prevalent and intense are supplied category pairs?",
            "start_with": "prevalence_among_lexical_tokens and token_mean.",
            "important_caution": "Missing category pairs are not zero intensity.",
        },
        {
            "file": "phase2_match_audit.csv",
            "what_it_answers": "Which exact evidence produced each result?",
            "start_with": "surface_span, lexicon_id, selection, matched_term, and reason.",
            "important_caution": "Suppressed rows are audit candidates, not included observations.",
        },
        {
            "file": "phase2_cross_lexicon_comparison.csv",
            "what_it_answers": "How do independent source-specific metrics compare?",
            "start_with": "metric, scale, denominator, and value.",
            "important_caution": "There is deliberately no consensus score.",
        },
        {
            "file": "phase2_manifest.csv",
            "what_it_answers": "Can this analysis be reproduced?",
            "start_with": "text/source hashes, versions, model, scenario, phrase policy, and stopword-list metadata.",
            "important_caution": "This is provenance rather than a results table; reviewed runs also list exact decision revisions.",
        },
        {
            "file": "phase2_results.json",
            "what_it_answers": "Can software read the complete nested result and methodology?",
            "start_with": "results, comparison, review_rules, stopword_policy, stopword_coverage, and vad_summary.",
            "important_caution": "All-matched and stopword-excluded fields are separate views of the same audited matches.",
        },
    ]
    return _csv_bytes(fields, rows)


def detailed_export_zip(workspace: WorkspaceAnalysis) -> bytes:
    """Create the complete audit bundle temporarily and return an in-memory ZIP."""

    with TemporaryDirectory(prefix="versevad-export-") as temporary:
        directory = Path(temporary)
        paths = export_phase2_csv(workspace.results, workspace.comparison, directory)
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, mode="w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for path in paths:
                bundle.write(path, arcname=path.name)
            bundle.writestr("scholar_summary.csv", scholar_summary_csv(workspace))
            bundle.writestr("csv_reading_guide.csv", csv_reading_guide())
            bundle.writestr(
                "START_HERE.txt",
                "Start with scholar_summary.csv and csv_reading_guide.csv.\n"
                "The remaining files preserve the detailed audit trail.\n"
                "Results describe lexical evidence under the selected policy; "
                "they do not determine the emotion of a poem.\n",
            )
        return archive.getvalue()
