from versevad.pronunciation_validation import (
    run_synthetic_pronunciation_validation,
)


def test_synthetic_pronunciation_validation_passes() -> None:
    report, problems = run_synthetic_pronunciation_validation()
    assert problems == ()
    assert report.eligible_tokens == 4
    assert report.resolved_tokens_before_override == 3
    assert report.resolved_tokens_after_override == 4
    assert report.complete_lines_before_override == 1
    assert report.complete_lines_after_override == 2
    assert report.source_files_unchanged
