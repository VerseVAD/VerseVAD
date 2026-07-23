"""Framework-independent contracts for modular Poetic Fingerprint analyses."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, runtime_checkable

from versevad.core.resources import ResourceProvenance, ResourceStatus
from versevad.models import PreprocessingMetadata, TextDocument, TokenRecord


class ResultLayer(StrEnum):
    """Distinguish evidence, calculation, and interpretation in reports."""

    DIRECT_OBSERVATION = "direct_observation"
    COMPUTED_SUMMARY = "computed_summary"
    INTERPRETATION = "interpretation"


class WarningSeverity(StrEnum):
    INFORMATION = "information"
    CAUTION = "caution"
    ERROR = "error"


MetricValue = int | float | str | bool | None


@dataclass(frozen=True)
class ModuleInput:
    """The preserved text and traceable processing representation for one module."""

    document: TextDocument
    tokens: tuple[TokenRecord, ...]
    preprocessing: PreprocessingMetadata

    def __post_init__(self) -> None:
        mismatched = [
            token.token_id
            for token in self.tokens
            if token.text_id != self.document.text_id
            or token.text_version_id != self.document.text_version_id
        ]
        if mismatched:
            raise ValueError(
                "Every module-input token must belong to the supplied text version."
            )


@dataclass(frozen=True)
class ModuleMetric:
    """One explicitly named observation, calculation, or interpretation."""

    metric_id: str
    value: MetricValue
    layer: ResultLayer
    scope: str = "document"
    scope_id: str = ""
    unit: str = ""
    weighting: str = ""
    denominator: str = ""
    note: str = ""

    def __post_init__(self) -> None:
        if not self.metric_id.strip():
            raise ValueError("A module metric must have a non-empty metric ID.")
        if not self.scope.strip():
            raise ValueError("A module metric must identify its structural scope.")
        if isinstance(self.value, float) and not math.isfinite(self.value):
            raise ValueError(
                "Missing or undefined metric values must be None, not NaN or infinity."
            )


@dataclass(frozen=True)
class ModuleCoverage:
    """Coverage that keeps unmatched observations missing rather than neutral."""

    coverage_id: str
    eligible_count: int
    matched_count: int
    unmatched_count: int
    coverage_rate: float | None
    unit: str
    scope: str = "document"
    scope_id: str = ""
    unmatched_items: tuple[str, ...] = ()
    note: str = ""

    @classmethod
    def from_counts(
        cls,
        *,
        coverage_id: str,
        eligible_count: int,
        matched_count: int,
        unit: str,
        scope: str = "document",
        scope_id: str = "",
        unmatched_items: tuple[str, ...] = (),
        note: str = "",
    ) -> ModuleCoverage:
        if eligible_count < 0 or matched_count < 0:
            raise ValueError("Coverage counts cannot be negative.")
        if matched_count > eligible_count:
            raise ValueError("The matched count cannot exceed the eligible count.")
        return cls(
            coverage_id=coverage_id,
            eligible_count=eligible_count,
            matched_count=matched_count,
            unmatched_count=eligible_count - matched_count,
            coverage_rate=(
                matched_count / eligible_count if eligible_count else None
            ),
            unit=unit,
            scope=scope,
            scope_id=scope_id,
            unmatched_items=unmatched_items,
            note=note,
        )

    def __post_init__(self) -> None:
        if not self.coverage_id.strip():
            raise ValueError("A coverage record must have a non-empty coverage ID.")
        if not self.unit.strip():
            raise ValueError("A coverage record must identify its counted unit.")
        if not self.scope.strip():
            raise ValueError("A coverage record must identify its structural scope.")
        if self.eligible_count < 0 or self.matched_count < 0 or self.unmatched_count < 0:
            raise ValueError("Coverage counts cannot be negative.")
        if self.matched_count + self.unmatched_count != self.eligible_count:
            raise ValueError(
                "Matched and unmatched coverage counts must equal the eligible count."
            )
        expected_rate = (
            self.matched_count / self.eligible_count
            if self.eligible_count
            else None
        )
        if expected_rate is None:
            if self.coverage_rate is not None:
                raise ValueError("Coverage for an empty denominator must remain missing.")
        elif self.coverage_rate is None or not math.isclose(
            self.coverage_rate, expected_rate
        ):
            raise ValueError("The coverage rate must agree with its recorded counts.")


@dataclass(frozen=True)
class ModuleWarning:
    code: str
    message: str
    severity: WarningSeverity = WarningSeverity.CAUTION
    technical_detail: str = ""

    def __post_init__(self) -> None:
        if not self.code.strip() or not self.message.strip():
            raise ValueError("A module warning requires both a code and a message.")


@dataclass(frozen=True)
class ModuleProvenance:
    """Inputs required to reproduce a module result."""

    software_version: str
    source_text_sha256: str
    preprocessing_recipe: str
    pipeline_name: str
    pipeline_version: str
    configuration_id: str
    scenario_id: str
    lookup_policy: str
    inclusion_policy: str
    resources: tuple[ResourceProvenance, ...]

    def __post_init__(self) -> None:
        required = {
            "software version": self.software_version,
            "source-text SHA-256": self.source_text_sha256,
            "preprocessing recipe": self.preprocessing_recipe,
            "pipeline name": self.pipeline_name,
            "pipeline version": self.pipeline_version,
            "configuration ID": self.configuration_id,
            "scenario ID": self.scenario_id,
            "lookup policy": self.lookup_policy,
            "inclusion policy": self.inclusion_policy,
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing:
            raise ValueError(
                "Module provenance is missing: " + ", ".join(missing) + "."
            )
        if len(self.source_text_sha256) != 64 or any(
            character not in "0123456789abcdefABCDEF"
            for character in self.source_text_sha256
        ):
            raise ValueError(
                "Module provenance requires a 64 hexadecimal digit source-text "
                "SHA-256 checksum."
            )


@dataclass(frozen=True)
class ModuleResult:
    """Stable result envelope shared by optional analysis modules."""

    result_id: str
    module_name: str
    module_version: str
    text_id: str
    text_version_id: str
    metrics: tuple[ModuleMetric, ...]
    coverage: tuple[ModuleCoverage, ...]
    warnings: tuple[ModuleWarning, ...]
    provenance: ModuleProvenance

    def __post_init__(self) -> None:
        required = {
            "result ID": self.result_id,
            "module name": self.module_name,
            "module version": self.module_version,
            "text ID": self.text_id,
            "text-version ID": self.text_version_id,
        }
        missing = [label for label, value in required.items() if not value.strip()]
        if missing:
            raise ValueError("Module result is missing: " + ", ".join(missing) + ".")
        metric_identities = [
            (
                metric.metric_id,
                metric.scope,
                metric.scope_id,
                metric.weighting,
                metric.unit,
            )
            for metric in self.metrics
        ]
        if len(metric_identities) != len(set(metric_identities)):
            raise ValueError(
                "Metric identities must be unique within each scope and weighting."
            )
        coverage_identities = [
            (item.coverage_id, item.scope, item.scope_id) for item in self.coverage
        ]
        if len(coverage_identities) != len(set(coverage_identities)):
            raise ValueError("Coverage identities must be unique within each scope.")


@runtime_checkable
class AnalysisModule(Protocol):
    """Minimal interface implemented by every optional analysis module."""

    name: str
    version: str

    def analyze(self, module_input: ModuleInput) -> ModuleResult: ...

    def validate_resources(self) -> tuple[ResourceStatus, ...]: ...
