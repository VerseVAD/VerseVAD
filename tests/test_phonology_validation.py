from versevad.phonology_validation import run_synthetic_phonology_validation


def test_synthetic_phonology_validation_passes() -> None:
    report, problems = run_synthetic_phonology_validation()
    assert problems == ()
    assert report.abab_scheme == "ABAB"
    assert report.perfect_pair_count == 2
    assert report.masculine_pair_count == 2
    assert report.feminine_pair_count == 1
    assert report.multisyllabic_pair_count == 1
    assert report.slant_pair_count >= 1
    assert report.eye_pair_count >= 1
    assert report.internal_pair_count == 1
    assert report.unresolved_scheme == "?"
    assert report.unresolved_coverage == 0.0
    assert report.source_files_unchanged
