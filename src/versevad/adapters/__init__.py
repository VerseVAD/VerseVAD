"""Versioned, source-specific lexicon adapters."""

from versevad.adapters.base import (
    EmotionAssociationAdapter,
    EmotionIntensityAdapter,
    LexiconAdapterError,
    VadLexiconAdapter,
)
from versevad.adapters.nrc_emotion import NrcEmotionAdapter
from versevad.adapters.nrc_intensity import NrcEmotionIntensityAdapter
from versevad.adapters.nrc_vad import NrcVadV1Adapter, NrcVadV21Adapter
from versevad.adapters.warriner import WarrinerVadAdapter

__all__ = [
    "EmotionAssociationAdapter",
    "EmotionIntensityAdapter",
    "LexiconAdapterError",
    "NrcEmotionAdapter",
    "NrcEmotionIntensityAdapter",
    "NrcVadV1Adapter",
    "NrcVadV21Adapter",
    "VadLexiconAdapter",
    "WarrinerVadAdapter",
]
