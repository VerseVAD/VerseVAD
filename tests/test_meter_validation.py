from versevad.meter_validation import run_synthetic_meter_validation


def test_synthetic_meter_validation_passes() -> None:
    report, problems = run_synthetic_meter_validation()
    assert problems == ()
    assert report.fixed_candidate_count == 40
    assert report.iambic_pentameter_fit == 1.0
    assert report.trochaic_tetrameter_label == "Trochaic tetrameter"
    assert report.trochaic_tetrameter_fit == 1.0
    assert not report.missing_line_has_fit
