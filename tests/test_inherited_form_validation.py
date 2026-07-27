from versevad.inherited_form_validation import (
    run_synthetic_inherited_form_validation,
)


def test_inherited_form_synthetic_validation() -> None:
    report, problems = run_synthetic_inherited_form_validation()

    assert problems == ()
    assert report.profile_count == 169
    assert report.automatic_profile_count == 58
    assert report.partial_profile_count == 27
    assert report.manual_profile_count == 84
    assert not report.manual_profile_suggested
    assert report.villanelle_candidate == "villanelle"
    assert report.sestina_candidate == "sestina"
    assert report.pantoum_candidate == "pantoum"
    assert not report.undersupported_haiku_suggested
