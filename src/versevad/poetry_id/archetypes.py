"""Canonical 27-profile PoetryID archetype registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class VadLevel(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


@dataclass(frozen=True)
class PoetryArchetype:
    archetype_id: str
    name: str
    valence_level: VadLevel
    arousal_level: VadLevel
    dominance_level: VadLevel
    short_descriptor: str
    summary: str
    interpretive_caution: str


_LEVEL_LANGUAGE = {
    "valence": {
        VadLevel.LOW: "low normative valence",
        VadLevel.MODERATE: "moderate normative valence",
        VadLevel.HIGH: "high normative valence",
    },
    "arousal": {
        VadLevel.LOW: "low normative arousal",
        VadLevel.MODERATE: "moderate normative arousal",
        VadLevel.HIGH: "high normative arousal",
    },
    "dominance": {
        VadLevel.LOW: "low normative dominance",
        VadLevel.MODERATE: "moderate normative dominance",
        VadLevel.HIGH: "high normative dominance",
    },
}


def _entry(
    archetype_id: str,
    name: str,
    valence: VadLevel,
    arousal: VadLevel,
    dominance: VadLevel,
    descriptor: str,
    *,
    summary: str = "",
    caution: str = "",
) -> PoetryArchetype:
    return PoetryArchetype(
        archetype_id=archetype_id,
        name=name,
        valence_level=valence,
        arousal_level=arousal,
        dominance_level=dominance,
        short_descriptor=descriptor,
        summary=summary
        or (
            "A lexical-affective neighborhood combining "
            f"{_LEVEL_LANGUAGE['valence'][valence]}, "
            f"{_LEVEL_LANGUAGE['arousal'][arousal]}, and "
            f"{_LEVEL_LANGUAGE['dominance'][dominance]}; its concise "
            f"descriptor is {descriptor.casefold()}."
        ),
        interpretive_caution=caution
        or (
            "This name is an interpretive label for decontextualized normative "
            "lexical evidence. It does not identify a poem's emotion, a "
            "speaker's psychology, authorial intent, or reader response."
        ),
    )


L = VadLevel.LOW
M = VadLevel.MODERATE
H = VadLevel.HIGH

ARCHETYPES = (
    # High dominance
    _entry("sage", "The Sage", H, L, H, "Serene mastery"),
    _entry("steward", "The Steward", H, M, H, "Confident flourishing"),
    _entry("conqueror", "The Conqueror", H, H, H, "Triumphant force"),
    _entry("monk", "The Monk", M, L, H, "Disciplined restraint"),
    _entry("architect", "The Architect", M, M, H, "Measured command"),
    _entry("challenger", "The Challenger", M, H, H, "Force without sentiment"),
    _entry("stoic", "The Stoic", L, L, H, "Controlled suffering"),
    _entry(
        "survivor",
        "The Survivor",
        L,
        M,
        H,
        "Defiant endurance",
        summary=(
            "Negative but controlled language that persists, resists, or "
            "rebuilds under pressure."
        ),
        caution=(
            "The label describes a lexical-affective profile and must not "
            "romanticize suffering or imply biography."
        ),
    ),
    _entry("avenger", "The Avenger", L, H, H, "Empowered fury"),
    # Moderate dominance
    _entry("gardener", "The Gardener", H, L, M, "Gentle contentment"),
    _entry("companion", "The Companion", H, M, M, "Warm equilibrium"),
    _entry("celebrant", "The Celebrant", H, H, M, "Radiant animation"),
    _entry("still_water", "The Still Water", M, L, M, "Quiet equilibrium"),
    _entry("observer", "The Observer", M, M, M, "The balanced center"),
    _entry("adventurer", "The Adventurer", M, H, M, "Energized openness"),
    _entry("hermit", "The Hermit", L, L, M, "Melancholic withdrawal"),
    _entry("pilgrim", "The Pilgrim", L, M, M, "Sorrowful passage"),
    _entry("storm", "The Storm", L, H, M, "Uncontained distress"),
    # Low dominance
    _entry("sanctuary", "The Sanctuary", H, L, L, "Restorative surrender"),
    _entry("dreamer", "The Dreamer", H, M, L, "Hopeful yielding"),
    _entry("reveler", "The Reveler", H, H, L, "Ecstatic surrender"),
    _entry("echo", "The Echo", M, L, L, "Muted presence"),
    _entry("witness", "The Witness", M, M, L, "Receptive attention"),
    _entry("wanderer", "The Wanderer", M, H, L, "Restless uncertainty"),
    _entry("void", "The Void", L, L, L, "Depleted absence"),
    _entry("mourner", "The Mourner", L, M, L, "Vulnerable grief"),
    _entry("abyss", "The Abyss", L, H, L, "Overwhelmed terror"),
)

ARCHETYPE_BY_ID = {row.archetype_id: row for row in ARCHETYPES}
ARCHETYPE_BY_LEVELS = {
    (row.valence_level, row.arousal_level, row.dominance_level): row
    for row in ARCHETYPES
}

if len(ARCHETYPE_BY_ID) != 27 or len(ARCHETYPE_BY_LEVELS) != 27:
    raise RuntimeError("The canonical PoetryID registry must contain 27 unique profiles.")


def resolve_archetype(
    valence: VadLevel,
    arousal: VadLevel,
    dominance: VadLevel,
) -> PoetryArchetype:
    return ARCHETYPE_BY_LEVELS[(valence, arousal, dominance)]


__all__ = [
    "ARCHETYPES",
    "ARCHETYPE_BY_ID",
    "ARCHETYPE_BY_LEVELS",
    "PoetryArchetype",
    "VadLevel",
    "resolve_archetype",
]
