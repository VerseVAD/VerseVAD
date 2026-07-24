"""Phonological analysis modules built from local pronunciation evidence."""

from versevad.phonology.rhyme import (
    InternalRhymeMatch,
    PhonologicalAnalysisResult,
    PhonologicalConfiguration,
    PhonologicalLineResult,
    PhonologicalModule,
    PhonologicalModuleError,
    PhonologicalSummary,
    RhymeEndingStatus,
    RhymePairResult,
    RhymeStanzaSummary,
    SoundFamilySummary,
    analyze_phonological_evidence,
)

__all__ = [
    "InternalRhymeMatch",
    "PhonologicalAnalysisResult",
    "PhonologicalConfiguration",
    "PhonologicalLineResult",
    "PhonologicalModule",
    "PhonologicalModuleError",
    "PhonologicalSummary",
    "RhymeEndingStatus",
    "RhymePairResult",
    "RhymeStanzaSummary",
    "SoundFamilySummary",
    "analyze_phonological_evidence",
]
