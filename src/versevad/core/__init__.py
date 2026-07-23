"""Shared contracts for independently testable VerseVAD analysis modules."""

from versevad.core.modules import (
    AnalysisModule,
    ModuleCoverage,
    ModuleInput,
    ModuleMetric,
    ModuleProvenance,
    ModuleResult,
    ModuleWarning,
    ResultLayer,
    WarningSeverity,
)
from versevad.core.resources import (
    LocalResourceManager,
    ResourceProvenance,
    ResourceSpec,
    ResourceState,
    ResourceStatus,
)

__all__ = [
    "AnalysisModule",
    "LocalResourceManager",
    "ModuleCoverage",
    "ModuleInput",
    "ModuleMetric",
    "ModuleProvenance",
    "ModuleResult",
    "ModuleWarning",
    "ResourceProvenance",
    "ResourceSpec",
    "ResourceState",
    "ResourceStatus",
    "ResultLayer",
    "WarningSeverity",
]
