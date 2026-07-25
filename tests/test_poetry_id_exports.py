from __future__ import annotations

from versevad.core.modules import ModuleInput
from versevad.exports.poetry_id import export_poetry_id_bundle
from versevad.models import PreprocessingMetadata, VadScores
from versevad.poetry_id import (
    PoetryIDConfiguration,
    PoetryIDEngine,
    VadEvidence,
)
from versevad.preprocessing import create_text_document


def test_poetry_id_bundle_is_csv_and_word_only() -> None:
    document = create_text_document("export-test", "Export Test", "Invented.")
    module_input = ModuleInput(
        document=document,
        tokens=(),
        preprocessing=PreprocessingMetadata(
            "recipe",
            "pipeline",
            "1.0",
            (),
        ),
    )
    evidence = VadEvidence(
        source_analysis_id="vad-result",
        source_lexicon_id="vad-source",
        source_lexicon_name="VAD Source",
        source_lexicon_version="v1",
        source_adapter_version="1.0",
        source_sha256="b" * 64,
        analysis_view="all_matched",
        weighting_mode="token",
        scores=VadScores(0.2, 0.5, 0.8),
        dispersion=None,
        matched_token_count=8,
        eligible_token_count=10,
        token_coverage=0.8,
        matched_type_count=7,
        eligible_type_count=9,
        type_coverage=7 / 9,
    )
    result = PoetryIDEngine().analyze(
        module_input,
        (evidence,),
        PoetryIDConfiguration(weighting_modes=("token",)),
    )
    bundle = export_poetry_id_bundle(result)
    assert set(bundle) == {
        "poetry_id_summary.csv",
        "poetry_id_neighbors.csv",
        "poetry_id_lexical_character.csv",
        "poetry_id_methodology.csv",
        "poetry_id_archetype_map.csv",
        "poetry_id_vad_scales.csv",
        "poetry_id_manifest.csv",
        "poetry_id_report.docx",
    }
    assert not any(name.endswith((".json", ".txt", ".xlsx")) for name in bundle)
    assert bundle["poetry_id_report.docx"].startswith(b"PK")
    assert b"The Survivor" in bundle["poetry_id_summary.csv"]
    assert b"not probabilities" in bundle["poetry_id_methodology.csv"]
