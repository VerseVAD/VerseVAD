from __future__ import annotations

import pytest

from versevad.prosody.g2p import (
    G2P_MODEL_ID,
    G2PPredictionError,
    predict_arpabet,
)


def test_provisional_g2p_is_versioned_and_deterministic() -> None:
    first = predict_arpabet("quorvax")
    second = predict_arpabet("quorvax")

    assert first is second
    assert first.phones_text == "K W AO1 R V AE0 K S"
    assert first.engine_version == "1.52.0"
    assert first.model_id == G2P_MODEL_ID
    assert "provisional" in first.source_label


@pytest.mark.parametrize(
    ("word", "phones"),
    (
        ("button", "B AH1 T AH0 N"),
        ("little", "L IH1 T AH0 L"),
        ("xylophonic", "Z AY2 L AH0 F AA1 N IH0 K"),
        ("near", "N IH1 R"),
    ),
)
def test_provisional_g2p_maps_common_us_english_ipa_patterns(
    word: str,
    phones: str,
) -> None:
    assert predict_arpabet(word).phones_text == phones


def test_provisional_g2p_rejects_blank_or_multiword_input() -> None:
    with pytest.raises(G2PPredictionError, match="nonblank"):
        predict_arpabet("")
    with pytest.raises(G2PPredictionError, match="one observed word"):
        predict_arpabet("two words")
