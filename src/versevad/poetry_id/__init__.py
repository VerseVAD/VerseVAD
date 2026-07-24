"""PoetryID: transparent VAD-neighborhood classification."""

from versevad.poetry_id.archetypes import (
    ARCHETYPES,
    ARCHETYPE_BY_ID,
    ARCHETYPE_BY_LEVELS,
    PoetryArchetype,
    VadLevel,
    resolve_archetype,
)
from versevad.poetry_id.engine import (
    DEFAULT_THRESHOLD_PROFILE,
    LexicalCharacterResult,
    LexicalEvidence,
    POETRY_ID_MODULE_NAME,
    POETRY_ID_MODULE_VERSION,
    PoetryIDAnalysisResult,
    PoetryIDAssignment,
    PoetryIDConfiguration,
    PoetryIDEngine,
    PoetryIDUnavailable,
    SUPPORTED_VAD_LEXICON_IDS,
    ThresholdBand,
    ThresholdProfile,
    VadEvidence,
    classify_level,
)
from versevad.poetry_id.integration import (
    lexical_evidence_from_results,
    vad_evidence_from_results,
)

__all__ = [
    "ARCHETYPES",
    "ARCHETYPE_BY_ID",
    "ARCHETYPE_BY_LEVELS",
    "DEFAULT_THRESHOLD_PROFILE",
    "LexicalCharacterResult",
    "LexicalEvidence",
    "POETRY_ID_MODULE_NAME",
    "POETRY_ID_MODULE_VERSION",
    "PoetryArchetype",
    "PoetryIDAnalysisResult",
    "PoetryIDAssignment",
    "PoetryIDConfiguration",
    "PoetryIDEngine",
    "PoetryIDUnavailable",
    "SUPPORTED_VAD_LEXICON_IDS",
    "ThresholdBand",
    "ThresholdProfile",
    "VadEvidence",
    "VadLevel",
    "classify_level",
    "lexical_evidence_from_results",
    "resolve_archetype",
    "vad_evidence_from_results",
]
