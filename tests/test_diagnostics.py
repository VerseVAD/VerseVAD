from versevad.diagnostics import run_self_test


def test_local_self_test_checks_model_formulas_and_all_sources() -> None:
    checks = run_self_test()
    assert len(checks) == 12
    assert all(check.passed for check in checks)
    assert {check.check for check in checks} >= {
        "Graphical framework",
        "English linguistic model",
        "Phrase and VAD calculation",
        "Categorical emotion calculation",
        "Emotion intensity calculation",
        "Performance-aware meter safeguards",
        "Warriner VAD",
        "NRC VAD v1",
        "NRC VAD v2.1",
        "NRC Emotion",
        "NRC Emotion Intensity",
    }
