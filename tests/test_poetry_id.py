from __future__ import annotations

import math

import pytest

from versevad.core.modules import ModuleInput
from versevad.models import (
    DescriptiveStatistics,
    PreprocessingMetadata,
    VadScores,
)
from versevad.poetry_id import (
    ARCHETYPES,
    DEFAULT_THRESHOLD_PROFILE,
    LexicalEvidence,
    PoetryIDConfiguration,
    PoetryIDEngine,
    ThresholdBand,
    ThresholdProfile,
    VadEvidence,
    classify_level,
    resolve_archetype,
)
from versevad.preprocessing import create_text_document


def _statistics(value: float, count: int = 10) -> DescriptiveStatistics:
    return DescriptiveStatistics(
        count=count,
        mean=value,
        median=value,
        population_standard_deviation=0.1,
        minimum=value,
        first_quartile=value,
        third_quartile=value,
        maximum=value,
    )


def _module_input() -> ModuleInput:
    document = create_text_document(
        "poetry-id-test",
        "Synthetic PoetryID",
        "Invented text.",
    )
    return ModuleInput(
        document=document,
        tokens=(),
        preprocessing=PreprocessingMetadata(
            recipe_id="synthetic-recipe",
            pipeline_name="synthetic-pipeline",
            pipeline_version="1.0.0",
            disabled_components=(),
        ),
    )


def _vad(
    *,
    weighting: str = "token",
    valence: float = 0.2,
    arousal: float = 0.5,
    dominance: float = 0.8,
    matched_tokens: int = 9,
    token_coverage: float = 0.9,
    matched_types: int = 8,
    type_coverage: float = 0.8,
) -> VadEvidence:
    return VadEvidence(
        source_analysis_id=f"analysis-{weighting}",
        source_lexicon_id="synthetic-vad",
        source_lexicon_name="Synthetic VAD",
        source_lexicon_version="v1",
        source_adapter_version="1.0.0",
        source_sha256="a" * 64,
        analysis_view="all_matched",
        weighting_mode=weighting,
        scores=VadScores(valence, arousal, dominance),
        dispersion=VadScores(0.1, 0.1, 0.1),
        matched_token_count=matched_tokens,
        eligible_token_count=10,
        token_coverage=token_coverage,
        matched_type_count=matched_types,
        eligible_type_count=10,
        type_coverage=type_coverage,
        exclusions=("no neutral replacement for unmatched tokens",),
        unmatched_terms=("nonce",),
    )


def test_all_27_archetype_combinations_are_unique_and_complete() -> None:
    assert len(ARCHETYPES) == 27
    combinations = {
        (
            row.valence_level.value,
            row.arousal_level.value,
            row.dominance_level.value,
        )
        for row in ARCHETYPES
    }
    assert len(combinations) == 27
    assert len({row.archetype_id for row in ARCHETYPES}) == 27
    assert len({row.name for row in ARCHETYPES}) == 27
    assert all(row.summary and row.interpretive_caution for row in ARCHETYPES)


@pytest.mark.parametrize(
    ("scores", "expected"),
    [
        ((0.8, 0.8, 0.8), "conqueror"),
        ((0.2, 0.5, 0.8), "survivor"),
        ((0.5, 0.5, 0.5), "observer"),
        ((0.2, 0.2, 0.2), "void"),
        ((0.8, 0.2, 0.2), "sanctuary"),
    ],
)
def test_canonical_synthetic_assignments(
    scores: tuple[float, float, float],
    expected: str,
) -> None:
    levels = tuple(
        classify_level(score, DEFAULT_THRESHOLD_PROFILE.dimensions[name])
        for score, name in zip(
            scores,
            ("valence", "arousal", "dominance"),
            strict=True,
        )
    )
    assert resolve_archetype(*levels).archetype_id == expected


def test_threshold_boundaries_are_explicit_and_custom_profiles_validate() -> None:
    band = DEFAULT_THRESHOLD_PROFILE.dimensions["valence"]
    assert classify_level(0.4, band).value == "low"
    assert classify_level(0.400001, band).value == "moderate"
    assert classify_level(0.599999, band).value == "moderate"
    assert classify_level(0.6, band).value == "high"
    with pytest.raises(ValueError, match="below"):
        ThresholdBand(low_max=0.6, high_min=0.6)
    with pytest.raises(ValueError, match="0 to 1"):
        ThresholdBand(low_max=-0.1, high_min=0.6)
    with pytest.raises(ValueError, match="valence, arousal, and dominance"):
        ThresholdProfile(
            profile_id="bad",
            name="Bad",
            method="fixed",
            dimensions={"valence": ThresholdBand(0.4, 0.6)},
            configuration_version="1",
            built_in=False,
        )


def test_centroids_neighbors_affinities_and_boundary_confidence() -> None:
    engine = PoetryIDEngine()
    result = engine.analyze(
        _module_input(),
        (_vad(),),
        PoetryIDConfiguration(),
    )
    assignment = result.assignments[0]
    assert assignment.categorical_archetype.archetype_id == "survivor"
    assert assignment.nearest_centroid_archetype.archetype_id == "survivor"
    assert assignment.centroid_distance == pytest.approx(0.0)
    assert [row.rank for row in assignment.neighbors] == list(range(1, 28))
    assert all(
        first.distance <= second.distance
        for first, second in zip(
            assignment.neighbors,
            assignment.neighbors[1:],
        )
    )
    assert sum(row.affinity for row in assignment.neighbors) == pytest.approx(
        1.0
    )
    assert assignment.confidence.label == "high_confidence"
    assert "probability" not in assignment.narrative_summary.casefold()

    sensitive = engine.analyze(
        _module_input(),
        (_vad(arousal=0.400001),),
        PoetryIDConfiguration(),
    ).assignments[0]
    assert sensitive.confidence.label == "boundary_sensitive"
    assert sensitive.confidence.boundary_dimensions == ("arousal",)


def test_insufficient_evidence_stays_unavailable_and_token_type_are_separate() -> None:
    engine = PoetryIDEngine()
    result = engine.analyze(
        _module_input(),
        (
            _vad(weighting="token", matched_tokens=2),
            _vad(
                weighting="type",
                valence=0.8,
                arousal=0.8,
                dominance=0.8,
            ),
        ),
        PoetryIDConfiguration(weighting_modes=("token", "type")),
    )
    assert result.status == "partial"
    assert len(result.assignments) == 1
    assert result.assignments[0].weighting_mode == "type"
    assert result.assignments[0].categorical_archetype.archetype_id == (
        "conqueror"
    )
    assert result.unavailable[0].reason == "insufficient_matched_tokens"
    assert any(
        warning.code == "poetry_id_insufficient_matched_tokens"
        for warning in result.module_result.warnings
    )


def test_lexical_character_directionality_and_missing_dimension() -> None:
    lexical = (
        LexicalEvidence(
            dimension_id="concreteness",
            source_module="concreteness",
            configuration_id="concrete-config",
            unit="source 1-5",
            low_max=2.5,
            high_min=3.5,
            low_label="Predominantly abstract vocabulary",
            moderate_label="Mixed abstract and concrete vocabulary",
            high_label="Highly concrete vocabulary",
            token_statistics=_statistics(4.2),
            type_statistics=_statistics(3.0, 8),
            token_coverage=0.8,
            type_coverage=0.7,
        ),
        LexicalEvidence(
            dimension_id="frequency",
            source_module="lexical_frequency",
            configuration_id="frequency-config",
            unit="SUBTLEX-US Zipf",
            low_max=4.0,
            high_min=5.0,
            low_label="Relatively uncommon vocabulary",
            moderate_label="Moderate-frequency vocabulary",
            high_label="Common vocabulary",
            token_statistics=_statistics(5.2),
            type_statistics=None,
            token_coverage=0.9,
            type_coverage=None,
        ),
    )
    result = PoetryIDEngine().analyze(
        _module_input(),
        (_vad(),),
        PoetryIDConfiguration(
            requested_lexical_dimensions=(
                "concreteness",
                "frequency",
                "age_of_acquisition",
            )
        ),
        lexical_evidence=lexical,
    )
    by_key = {
        (row.dimension_id, row.weighting_mode): row
        for row in result.lexical_character
    }
    assert by_key[("concreteness", "token")].level.value == "high"
    assert by_key[("concreteness", "type")].level.value == "moderate"
    assert by_key[("frequency", "token")].display_label == "Common vocabulary"
    assert ("frequency", "type") not in by_key
    assert result.assignments[0].categorical_archetype.archetype_id == (
        "survivor"
    )
    assert result.status == "partial"


def test_configuration_round_trip_preserves_exact_thresholds() -> None:
    custom = ThresholdProfile(
        profile_id="custom-study",
        name="Custom Study Thresholds",
        method="fixed",
        dimensions={
            name: ThresholdBand(0.3, 0.7)
            for name in ("valence", "arousal", "dominance")
        },
        configuration_version="custom-1",
        built_in=False,
    )
    configuration = PoetryIDConfiguration(
        threshold_profile=custom,
        weighting_modes=("type",),
        minimum_matched_tokens=7,
    )
    restored = PoetryIDConfiguration.from_dict(configuration.to_dict())
    assert restored == configuration
    assert restored.configuration_id == configuration.configuration_id
    assert math.isclose(
        restored.threshold_profile.dimensions["arousal"].low_centroid,
        0.15,
    )
