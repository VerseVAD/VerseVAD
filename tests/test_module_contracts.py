from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from versevad.core.modules import (
    AnalysisModule,
    ModuleCoverage,
    ModuleInput,
    ModuleMetric,
    ModuleProvenance,
    ModuleResult,
    ResultLayer,
)
from versevad.models import PreprocessingMetadata
from versevad.preprocessing import create_text_document


class _SyntheticModule:
    name = "synthetic"
    version = "1.0"

    def validate_resources(self):
        return ()

    def analyze(self, module_input: ModuleInput) -> ModuleResult:
        return ModuleResult(
            result_id="result-synthetic",
            module_name=self.name,
            module_version=self.version,
            text_id=module_input.document.text_id,
            text_version_id=module_input.document.text_version_id,
            metrics=(
                ModuleMetric(
                    metric_id="synthetic.mean",
                    value=2.5,
                    layer=ResultLayer.COMPUTED_SUMMARY,
                    unit="synthetic units",
                    denominator="two matched tokens",
                ),
            ),
            coverage=(
                ModuleCoverage.from_counts(
                    coverage_id="synthetic.token_coverage",
                    eligible_count=3,
                    matched_count=2,
                    unit="tokens",
                    unmatched_items=("unrated",),
                ),
            ),
            warnings=(),
            provenance=ModuleProvenance(
                software_version="test",
                source_text_sha256=module_input.document.text_sha256,
                preprocessing_recipe=module_input.preprocessing.recipe_id,
                pipeline_name=module_input.preprocessing.pipeline_name,
                pipeline_version=module_input.preprocessing.pipeline_version,
                configuration_id="synthetic-default-v1",
                scenario_id="baseline",
                lookup_policy="synthetic exact lookup",
                inclusion_policy="all matched synthetic tokens",
                resources=(),
            ),
        )


def _module_input() -> ModuleInput:
    document = create_text_document("synthetic", "Synthetic", "Stone moves.")
    return ModuleInput(
        document=document,
        tokens=(),
        preprocessing=PreprocessingMetadata(
            recipe_id="test-recipe",
            pipeline_name="synthetic-pipeline",
            pipeline_version="1",
            disabled_components=(),
        ),
    )


def test_analysis_module_protocol_and_result_are_framework_independent() -> None:
    module: AnalysisModule = _SyntheticModule()

    result = module.analyze(_module_input())

    assert isinstance(module, AnalysisModule)
    assert result.module_name == "synthetic"
    assert result.metrics[0].value == 2.5
    assert result.coverage[0].coverage_rate == pytest.approx(2 / 3)
    assert result.provenance.preprocessing_recipe == "test-recipe"


def test_coverage_computes_unmatched_items_without_neutral_scores() -> None:
    coverage = ModuleCoverage.from_counts(
        coverage_id="concreteness.token_coverage",
        eligible_count=4,
        matched_count=1,
        unit="tokens",
        unmatched_items=("unknown", "unrated"),
    )

    assert coverage.unmatched_count == 3
    assert coverage.coverage_rate == 0.25
    assert coverage.unmatched_items == ("unknown", "unrated")


def test_empty_coverage_remains_missing() -> None:
    coverage = ModuleCoverage.from_counts(
        coverage_id="empty",
        eligible_count=0,
        matched_count=0,
        unit="tokens",
    )

    assert coverage.unmatched_count == 0
    assert coverage.coverage_rate is None


def test_invalid_coverage_counts_are_rejected() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        ModuleCoverage.from_counts(
            coverage_id="invalid",
            eligible_count=1,
            matched_count=2,
            unit="tokens",
        )


def test_result_records_are_immutable() -> None:
    result = _SyntheticModule().analyze(_module_input())

    with pytest.raises(FrozenInstanceError):
        result.module_version = "changed"  # type: ignore[misc]


def test_same_metric_can_be_reported_for_distinct_lines() -> None:
    base = _SyntheticModule().analyze(_module_input())

    result = ModuleResult(
        result_id="line-results",
        module_name="synthetic",
        module_version="1.0",
        text_id=base.text_id,
        text_version_id=base.text_version_id,
        metrics=(
            ModuleMetric(
                metric_id="synthetic.mean",
                value=1.0,
                layer=ResultLayer.COMPUTED_SUMMARY,
                scope="line",
                scope_id="line:1",
            ),
            ModuleMetric(
                metric_id="synthetic.mean",
                value=2.0,
                layer=ResultLayer.COMPUTED_SUMMARY,
                scope="line",
                scope_id="line:2",
            ),
        ),
        coverage=(),
        warnings=(),
        provenance=base.provenance,
    )

    assert [metric.scope_id for metric in result.metrics] == ["line:1", "line:2"]


def test_duplicate_metric_identity_within_one_scope_is_rejected() -> None:
    base = _SyntheticModule().analyze(_module_input())
    repeated = ModuleMetric(
        metric_id="synthetic.mean",
        value=1.0,
        layer=ResultLayer.COMPUTED_SUMMARY,
        scope="line",
        scope_id="line:1",
    )

    with pytest.raises(ValueError, match="identities"):
        ModuleResult(
            result_id="duplicate",
            module_name="synthetic",
            module_version="1.0",
            text_id=base.text_id,
            text_version_id=base.text_version_id,
            metrics=(repeated, repeated),
            coverage=(),
            warnings=(),
            provenance=base.provenance,
        )


def test_source_text_provenance_requires_a_sha256() -> None:
    with pytest.raises(ValueError, match="64 hexadecimal"):
        ModuleProvenance(
            software_version="test",
            source_text_sha256="not-a-checksum",
            preprocessing_recipe="test",
            pipeline_name="test",
            pipeline_version="1",
            configuration_id="test",
            scenario_id="test",
            lookup_policy="not applicable",
            inclusion_policy="all eligible items",
            resources=(),
        )
