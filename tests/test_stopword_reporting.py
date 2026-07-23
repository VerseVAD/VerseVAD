from __future__ import annotations

import hashlib

import pytest

from versevad.analysis.phase2 import analyze_lexicon, compare_lexicons
from versevad.application import AnalysisRequest, WorkspaceAnalysis, vad_contributor_views
from versevad.models import (
    LexiconMetadata,
    LexiconValidation,
    StopwordMode,
    VadEntry,
    VadLexicon,
    VadScores,
)
from versevad.normalization import normalize_lookup
from versevad.preprocessing import create_text_document
from versevad.stopwords import build_stopword_policy


def _stopword_lexicon() -> VadLexicon:
    values = {
        "be": (0.55, 0.30, 0.45),
        "radiant": (0.90, 0.70, 0.75),
        "sorrowful": (0.10, 0.60, 0.25),
        "calm": (0.40, 0.20, 0.55),
        "not": (0.20, 0.50, 0.35),
        "never": (0.15, 0.55, 0.30),
        "happy": (0.80, 0.65, 0.70),
        "return": (0.50, 0.40, 0.50),
        "raven": (0.30, 0.60, 0.45),
        "out of control": (0.25, 0.80, 0.20),
    }
    metadata = LexiconMetadata(
        lexicon_id="stopword_acceptance_vad",
        display_name="Stopword acceptance VAD",
        family="VerseVAD validation fixtures",
        version="1",
        language="English",
        unit_of_analysis="invented words and phrase",
        source_scale_min=0.0,
        source_scale_max=1.0,
        normalization_formula="normalized = original (identity)",
        adapter_version="synthetic-stopword-1",
        citation="Invented VerseVAD validation data.",
        license_notice="Invented public-domain validation data.",
        phrase_support=True,
    )
    entries = {}
    lines = []
    for source_row, (term, scores) in enumerate(values.items(), start=1):
        key = normalize_lookup(term)
        rating = VadScores(*scores)
        entries[key] = VadEntry(
            lexicon_id=metadata.lexicon_id,
            source_term=term,
            lookup_form=key,
            source_row=source_row,
            original=rating,
            normalized=rating,
        )
        lines.append(f"{term}\t{scores}")
    digest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    validation = LexiconValidation(
        source_path=None,
        source_sha256=digest,
        total_rows=len(entries),
        usable_entries=len(entries),
        phrase_entries=1,
        blank_terms=0,
        malformed_rows=0,
        duplicate_keys=0,
        conflicting_normalized_keys=0,
        out_of_range_scores=0,
    )
    return VadLexicon.create(metadata, entries, validation)


def _analyze(text: str, preprocessor, *, policy=None):
    document = create_text_document("stopword-test", "Stopword test", text)
    return analyze_lexicon(
        document,
        _stopword_lexicon(),
        preprocessor,
        minimum_match_requirement=1,
        stopword_policy=policy or build_stopword_policy(),
    )


def _single_token_matches(result):
    token_map = {token.token_id: token for token in result.tokens}
    return {
        token_map[match.token_ids[0]].surface_form: match
        for match in result.matches
        if len(match.token_ids) == 1 and match.included
    }


def test_forms_of_be_remain_in_full_and_leave_filtered_view(preprocessor) -> None:
    result = _analyze(
        "She is radiant. They were sorrowful. He was calm.",
        preprocessor,
    )
    matches = _single_token_matches(result)

    for form in ("is", "were", "was"):
        assert matches[form].matched_term == "be"
        assert matches[form].included
        assert not matches[form].included_in_stopword_view
        token = next(
            token for token in result.tokens if token.token_id == matches[form].token_ids[0]
        )
        assert token.normalized_lemma == "be"

    for form in ("radiant", "sorrowful", "calm"):
        assert matches[form].included_in_stopword_view
    assert result.vad_summary is not None
    assert result.vad_summary.token_weighted_normalized.valence.count == 6
    assert (
        result.vad_summary.stopword_excluded_token_weighted_normalized.valence.count
        == 3
    )


def test_protected_negation_remains_in_filtered_view(preprocessor) -> None:
    result = _analyze("She was not happy. He never returned.", preprocessor)
    matches = _single_token_matches(result)

    assert not matches["was"].included_in_stopword_view
    for form in ("not", "never"):
        assert matches[form].included_in_stopword_view
        assert matches[form].stopword_status == "protected term"


def test_custom_stopword_is_audited_and_excluded(preprocessor) -> None:
    policy = build_stopword_policy(
        mode=StopwordMode.CUSTOM,
        custom_additions=("raven",),
    )
    result = _analyze("Raven raven.", preprocessor, policy=policy)
    matches = _single_token_matches(result)

    assert matches["Raven"].included
    assert not matches["Raven"].included_in_stopword_view
    assert matches["Raven"].stopword_status == "custom stopword"
    assert "custom stopword list" in matches["Raven"].stopword_exclusion_reason
    assert result.stopword_policy is not None
    assert result.stopword_policy.custom_additions == ("raven",)


def test_published_phrase_is_never_broken_by_stopword_filter(preprocessor) -> None:
    result = _analyze("Out of control.", preprocessor)
    phrase = next(
        match for match in result.matches if match.matched_term == "out of control"
    )

    assert phrase.included
    assert phrase.included_in_stopword_view
    assert phrase.stopword_status == "published phrase retained intact"
    assert phrase.normalized_scores is not None
    assert result.vad_summary is not None
    assert (
        result.vad_summary.stopword_excluded_token_weighted_normalized.valence.count
        == 1
    )


def test_midpoint_centered_contribution_uses_frequency(preprocessor) -> None:
    text = " ".join(["be"] * 40 + ["radiant"] * 4)
    result = _analyze(text, preprocessor)
    request = AnalysisRequest(
        project_name="Synthetic",
        title="Contribution",
        original_text=text,
        lexicon_ids=(result.lexicon_metadata.lexicon_id,),
    )
    workspace = WorkspaceAnalysis(
        request=request,
        document=result.document,
        results=(result,),
        comparison=compare_lexicons((result,)),
    )

    rows = [
        row
        for row in vad_contributor_views(workspace)
        if row.analysis_view == "All matched tokens" and row.dimension == "valence"
    ]
    be = next(row for row in rows if row.term == "be")
    radiant = next(row for row in rows if row.term == "radiant")

    assert be.signed_contribution == pytest.approx(2.0)
    assert radiant.signed_contribution == pytest.approx(1.6)
    assert be.midpoint_deviation_per_occurrence == pytest.approx(0.05)

