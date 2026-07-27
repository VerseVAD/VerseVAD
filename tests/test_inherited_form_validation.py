from versevad.inherited_form_validation import (
    run_synthetic_inherited_form_validation,
)


def test_inherited_form_synthetic_validation() -> None:
    report, problems = run_synthetic_inherited_form_validation()

    assert problems == ()
    assert report.profile_count == 10
    assert report.villanelle_candidate == "villanelle"
    assert report.sestina_candidate == "sestina"
    assert report.pantoum_candidate == "pantoum"
    assert not report.undersupported_haiku_suggested
