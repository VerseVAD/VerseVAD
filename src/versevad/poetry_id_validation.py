"""Hand-calculated synthetic validation for PoetryID."""

from __future__ import annotations

import math

from versevad.core.modules import ModuleInput
from versevad.exports.poetry_id import export_poetry_id_bundle
from versevad.models import PreprocessingMetadata, VadScores
from versevad.poetry_id import (
    ARCHETYPES,
    PoetryIDConfiguration,
    PoetryIDEngine,
    VadEvidence,
)
from versevad.preprocessing import create_text_document


def main() -> int:
    document = create_text_document(
        "poetry-id-validation",
        "PoetryID validation",
        "Invented validation text.",
    )
    module_input = ModuleInput(
        document=document,
        tokens=(),
        preprocessing=PreprocessingMetadata(
            "poetry-id-validation-recipe",
            "synthetic",
            "1.0.0",
            (),
        ),
    )
    evidence = VadEvidence(
        source_analysis_id="synthetic-vad-result",
        source_lexicon_id="synthetic-vad",
        source_lexicon_name="Synthetic VAD",
        source_lexicon_version="v1",
        source_adapter_version="1.0.0",
        source_sha256="a" * 64,
        analysis_view="all_matched",
        weighting_mode="token",
        scores=VadScores(0.2, 0.5, 0.8),
        dispersion=VadScores(0.1, 0.1, 0.1),
        matched_token_count=9,
        eligible_token_count=10,
        token_coverage=0.9,
        matched_type_count=8,
        eligible_type_count=10,
        type_coverage=0.8,
        token_vad_observation_count=9,
        type_vad_observation_count=8,
    )
    result = PoetryIDEngine().analyze(
        module_input,
        (evidence,),
        PoetryIDConfiguration(weighting_modes=("token",)),
    )
    assignment = result.assignments[0]
    assert len(ARCHETYPES) == 27
    assert assignment.categorical_archetype.archetype_id == "survivor"
    assert assignment.nearest_centroid_archetype.archetype_id == "survivor"
    assert math.isclose(assignment.centroid_distance, 0)
    assert math.isclose(
        sum(row.affinity for row in assignment.neighbors),
        1,
    )
    assert assignment.confidence.label == "high_confidence"
    bundle = export_poetry_id_bundle(result)
    assert len(bundle) == 7
    assert not any(name.endswith(".json") for name in bundle)

    print("VerseVAD PoetryID validation passed.")
    print("Input VAD: valence 0.2, arousal 0.5, dominance 0.8.")
    print("Categorical profile: The Survivor (low, moderate, high).")
    print("Nearest-centroid distance: 0.000000.")
    print("All 27 distances retained; relative affinities sum to 1.")
    print("Export bundle: seven CSV/TXT files and no PoetryID JSON.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
