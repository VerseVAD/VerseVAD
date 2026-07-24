from versevad.performance_meter_validation import (
    run_synthetic_performance_meter_validation,
)


def test_synthetic_performance_meter_validation_passes() -> None:
    report, problems = run_synthetic_performance_meter_validation()

    assert problems == ()
    assert report.analyzed_lines == 4
    assert report.lexical_stress_preserved
    assert report.named_stanza_form_absent
