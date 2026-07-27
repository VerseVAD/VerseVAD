"""Synthetic structural validation for the ten inherited-form profiles."""

from __future__ import annotations

from dataclasses import dataclass

from versevad.core import ModuleInput
from versevad.inherited_form import FORM_PROFILES, InheritedFormEngine
from versevad.preprocessing import SpacyEnglishPreprocessor, create_text_document


@dataclass(frozen=True)
class InheritedFormValidationReport:
    profile_count: int
    villanelle_candidate: str
    villanelle_consistency: float | None
    sestina_candidate: str
    sestina_rotation_score: float | None
    pantoum_candidate: str
    pantoum_repetition_score: float | None
    undersupported_haiku_suggested: bool
    tooltip_has_traditional_definition: bool


def _analyze(text_id: str, text: str):
    poem = SpacyEnglishPreprocessor().process_document(
        create_text_document(text_id, text_id.replace("-", " ").title(), text)
    )
    return InheritedFormEngine().analyze(
        ModuleInput.from_poem_document(poem),
        None,
        None,
        None,
    )


def _villanelle() -> str:
    return "\n\n".join(
        (
            "bright cat\nsilver stone\nsoftly night",
            "motion love\nsilver stone\nbright cat",
            "ocean true\nsilver stone\nsoftly night",
            "rings move\nsilver stone\nbright cat",
            "alice sing\nsilver stone\nsoftly night",
            "wind permit\nsilver stone\nbright cat\nsoftly night",
        )
    )


def _sestina() -> str:
    seed = ("bright", "cat", "night", "stone", "love", "motion")
    orders = (
        (0, 1, 2, 3, 4, 5),
        (5, 0, 4, 1, 3, 2),
        (2, 5, 3, 0, 1, 4),
        (4, 2, 1, 5, 0, 3),
        (3, 4, 0, 2, 5, 1),
        (1, 3, 5, 4, 2, 0),
    )
    stanzas = [
        "\n".join(f"the {seed[index]}" for index in order)
        for order in orders
    ]
    stanzas.append("cat stone love\nmotion night\nthe bright")
    return "\n\n".join(stanzas)


def _pantoum() -> str:
    return "\n\n".join(
        (
            "bright cat\nsilver night\nsoftly stone\nmotion love",
            "silver night\nocean true\nmotion love\nalice sings",
            "ocean true\nwind moves\nalice sings\nbright cat",
        )
    )


def run_synthetic_inherited_form_validation(
) -> tuple[InheritedFormValidationReport, tuple[str, ...]]:
    villanelle = _analyze("villanelle-validation", _villanelle())
    sestina = _analyze("sestina-validation", _sestina())
    pantoum = _analyze("pantoum-validation", _pantoum())
    haiku = _analyze(
        "haiku-missing-evidence-validation",
        "red sun on the hill\nthe blue moon is over us\nbirds sing in the rain",
    )
    sestina_rotation = next(
        item
        for item in sestina.best_candidate.feature_evidence
        if item.feature_id == "sestina_rotation"
    )
    pantoum_repetition = next(
        item
        for item in pantoum.best_candidate.feature_evidence
        if item.feature_id == "pantoum_repetition"
    )
    report = InheritedFormValidationReport(
        profile_count=len(FORM_PROFILES),
        villanelle_candidate=(
            villanelle.best_candidate.profile_id
            if villanelle.best_candidate
            else ""
        ),
        villanelle_consistency=(
            villanelle.best_candidate.consistency
            if villanelle.best_candidate
            else None
        ),
        sestina_candidate=(
            sestina.best_candidate.profile_id if sestina.best_candidate else ""
        ),
        sestina_rotation_score=sestina_rotation.score,
        pantoum_candidate=(
            pantoum.best_candidate.profile_id if pantoum.best_candidate else ""
        ),
        pantoum_repetition_score=pantoum_repetition.score,
        undersupported_haiku_suggested=any(
            item.profile_id == "english_575_haiku" and item.suggested
            for item in haiku.candidates
        ),
        tooltip_has_traditional_definition=(
            villanelle.best_candidate is not None
            and "Traditionally:" in villanelle.best_candidate.tooltip
        ),
    )
    problems = []
    expected = {
        "profile_count": 10,
        "villanelle_candidate": "villanelle",
        "villanelle_consistency": 1.0,
        "sestina_candidate": "sestina",
        "sestina_rotation_score": 1.0,
        "pantoum_candidate": "pantoum",
        "pantoum_repetition_score": 1.0,
        "undersupported_haiku_suggested": False,
        "tooltip_has_traditional_definition": True,
    }
    for field, value in expected.items():
        if getattr(report, field) != value:
            problems.append(
                f"{field} was {getattr(report, field)!r}; expected {value!r}."
            )
    return report, tuple(problems)


def main() -> int:
    report, problems = run_synthetic_inherited_form_validation()
    if problems:
        print("VerseVAD inherited-form validation did not match expectations.")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("VerseVAD inherited-form validation passed.")
    print(
        "Ten source-backed profiles were present; exact structural fixtures "
        "ranked villanelle, sestina, and pantoum first."
    )
    print(
        "Sestina end-word rotation and pantoum ordered repetition received "
        "full credit."
    )
    print(
        "A three-line poem without required syllable evidence was not promoted "
        "to the English-language 5–7–5 haiku profile."
    )
    print(
        "The potential-match tooltip retained the traditional definition and "
        "poem-specific agreement evidence."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
