from versevad.meter_validation import run_synthetic_meter_validation


def test_synthetic_meter_validation_passes() -> None:
    report, problems = run_synthetic_meter_validation()
    assert problems == ()
    assert report.fixed_candidate_count == 40
    assert report.iambic_pentameter_fit == 1.0
    assert report.common_meter_cycle == (4, 3, 4, 3)
    assert report.common_meter_fit == 1.0
    assert report.common_meter_matching_lines == 4
    assert report.common_meter_complete_stanzas == 1
    assert not report.missing_line_has_fit
