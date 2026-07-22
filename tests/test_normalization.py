from versevad.normalization import (
    canonicalize_apostrophes,
    normalize_lookup,
    possessive_base,
    strip_edge_punctuation,
)


def test_lookup_normalization_retains_visible_form_distinctions() -> None:
    assert normalize_lookup("  ÉCLAT  ") == "éclat"
    assert normalize_lookup("death’s") == "death’s"


def test_possessive_normalization_accepts_common_apostrophe_variants() -> None:
    assert canonicalize_apostrophes("death’s") == "death's"
    assert possessive_base("Death’s") == "death"
    assert possessive_base("birds'") == "birds"
    assert possessive_base("it's") == "it"
    assert possessive_base("plain") is None


def test_edge_punctuation_does_not_remove_internal_marks() -> None:
    assert strip_edge_punctuation("“well-being”") == "well-being"
    assert strip_edge_punctuation("o’er") == "o’er"
