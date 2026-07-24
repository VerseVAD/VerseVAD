from versevad.concreteness_validation import (
    run_synthetic_concreteness_validation,
)


def test_hand_calculated_concreteness_validation() -> None:
    report, problems = run_synthetic_concreteness_validation()

    assert problems == ()
    assert report.eligible_tokens == 6
    assert report.rated_tokens == 5
    assert report.mean_normative_concreteness == 4.0
    assert report.unmatched_tokens == 1
    assert report.source_unchanged
