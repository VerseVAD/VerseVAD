from __future__ import annotations

from versevad.lexical_style_validation import main


def test_lexical_style_validation_demo_passes(capsys) -> None:
    assert main() == 0
    output = capsys.readouterr().out
    assert "VerseVAD lexical style validation passed." in output
    assert "Line word counts: 3, 2, 0, 2" in output
    assert "Stanza word counts: 5, 2" in output
