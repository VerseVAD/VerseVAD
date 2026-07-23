"""Framework-independent services for the beginner one-text workspace."""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable

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
    TextDocument,
)
from versevad.preprocessing import SpacyEnglishPreprocessor, TextPreprocessor, create_text_document


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
        "Normative valence, arousal, and dominance on the original 1-9 scale.",
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


@dataclass(frozen=True)
class VadView:
    lexicon_id: str
    lexicon: str
    matched_observations: int
    lexical_coverage: float | None
    normalized_valence: float | None
    normalized_arousal: float | None
    normalized_dominance: float | None
    type_valence: float | None
    type_arousal: float | None
    type_dominance: float | None
    original_scale: str
    normalization_formula: str


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
    lexicon: str
    surface: str
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


@dataclass(frozen=True)
class UnmatchedView:
    lexicon: str
    surface: str
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
        text_id=f"workspace-{identity}",
        title=request.title.strip(),
        original_text=request.original_text,
    )
    processor = preprocessor or SpacyEnglishPreprocessor()
    results = tuple(
        analyze_lexicon(
            document,
            load_lexicon(lexicon_id, str(source_root.resolve())),
            processor,
            phrase_policy=request.phrase_policy,
            minimum_match_requirement=request.minimum_match_requirement,
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
        token = summary.token_weighted_normalized
        kind = summary.type_weighted_normalized
        metadata = result.lexicon_metadata
        rows.append(
            VadView(
                lexicon_id=metadata.lexicon_id,
                lexicon=metadata.display_name,
                matched_observations=token.valence.count,
                lexical_coverage=result.coverage.lexical_token_coverage,
                normalized_valence=token.valence.mean,
                normalized_arousal=token.arousal.mean,
                normalized_dominance=token.dominance.mean,
                type_valence=kind.valence.mean,
                type_arousal=kind.arousal.mean,
                type_dominance=kind.dominance.mean,
                original_scale=f"{metadata.source_scale_min:g} to {metadata.source_scale_max:g}",
                normalization_formula=metadata.normalization_formula,
            )
        )
    return tuple(rows)


def emotion_association_views(
    workspace: WorkspaceAnalysis,
) -> tuple[EmotionAssociationView, ...]:
    rows = []
    for result in workspace.results:
        for stats in result.category_statistics:
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
                    lexicon=result.lexicon_metadata.display_name,
                    surface=" ".join(token.surface_form for token in tokens),
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
                )
            )
    return tuple(rows)


def unmatched_views(workspace: WorkspaceAnalysis) -> tuple[UnmatchedView, ...]:
    grouped: dict[tuple[str, str, str, str], list[tuple[int, str]]] = {}
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
                token.part_of_speech,
                token.lemma,
            )
            grouped.setdefault(key, []).append((token.line_number, token.context))
    rows = []
    for (lexicon_id, surface, pos, lemma), examples in grouped.items():
        rows.append(
            UnmatchedView(
                lexicon=display_names[lexicon_id],
                surface=surface,
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
            "Emotion associations are multi-label categories, so their percentages are not expected to sum to 100%."
        )
    if emotion_intensity_views(workspace):
        notes.append(
            "Emotion intensity means use only supplied word-emotion pairs; missing pairs are not treated as zero."
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
        "metric",
        "value",
        "unit_or_scale",
        "denominator",
        "plain_language_note",
    ]
    rows: list[dict[str, object]] = []
    for coverage in coverage_views(workspace):
        rows.append(
            {
                "section": "Coverage",
                "lexicon": coverage.lexicon,
                "metric": "Lexical-token coverage",
                "value": coverage.coverage if coverage.coverage is not None else "",
                "unit_or_scale": "proportion",
                "denominator": f"{coverage.lexical_tokens} lexical tokens",
                "plain_language_note": coverage.note,
            }
        )
    for row in vad_views(workspace):
        for label, value in (
            ("Mean normative valence", row.normalized_valence),
            ("Mean normative arousal", row.normalized_arousal),
            ("Mean normative dominance", row.normalized_dominance),
        ):
            rows.append(
                {
                    "section": "Normalized VAD",
                    "lexicon": row.lexicon,
                    "metric": label,
                    "value": value if value is not None else "",
                    "unit_or_scale": "derived 0-1",
                    "denominator": f"{row.matched_observations} included matched observations",
                    "plain_language_note": "Original values and formula remain in the detailed audit.",
                }
            )
    for row in emotion_association_views(workspace):
        rows.append(
            {
                "section": "Emotion association",
                "lexicon": "NRC Emotion",
                "metric": f"{row.category} association rate",
                "value": row.rate_per_lexical_token if row.rate_per_lexical_token is not None else "",
                "unit_or_scale": "proportion",
                "denominator": "all lexical tokens",
                "plain_language_note": f"Contributors: {row.top_terms or 'none'}",
            }
        )
    for row in emotion_intensity_views(workspace):
        rows.append(
            {
                "section": "Emotion intensity",
                "lexicon": "NRC Emotion Intensity",
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
            "start_with": "Coverage, normalized VAD means, association rates, and matched intensity means.",
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
            "start_with": "text/source hashes, versions, model, scenario, and phrase policy.",
            "important_caution": "This is provenance rather than a results table.",
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
