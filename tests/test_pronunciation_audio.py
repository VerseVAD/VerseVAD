from __future__ import annotations

import io
import wave

import pytest

from versevad.prosody.audio import (
    PronunciationAudioError,
    arpabet_to_espeak,
    espeak_engine_version,
    normalize_arpabet_phones,
    phonemize_word_ipa,
    synthesize_arpabet_wav,
)


def test_arpabet_conversion_retains_stress_and_rhotic_vowels() -> None:
    assert arpabet_to_espeak("P ER1 M IH2 T") == "[[p'3:m,It]]"
    assert arpabet_to_espeak("K AA1 R") == "[[k'A@]]"
    assert arpabet_to_espeak("DH AH0") == "[[D@]]"


def test_arpabet_conversion_rejects_unmarked_or_unknown_phones() -> None:
    with pytest.raises(PronunciationAudioError, match="stress digit"):
        arpabet_to_espeak("P ER M IH1 T")
    with pytest.raises(PronunciationAudioError, match="preview inventory"):
        arpabet_to_espeak("P XX1 T")


def test_editable_arpabet_is_validated_and_normalized() -> None:
    assert (
        normalize_arpabet_phones("  k w ao1 r v ae0 k s  ")
        == "K W AO1 R V AE0 K S"
    )


def test_local_engine_exposes_versioned_us_english_phonemization() -> None:
    assert espeak_engine_version() == "1.52.0"
    ipa = phonemize_word_ipa("quorvax")
    assert "ˈ" in ipa
    assert "|" in ipa


def test_offline_preview_returns_audible_wav_container() -> None:
    preview = synthesize_arpabet_wav("P ER1 M IH2 T")

    assert preview.startswith(b"RIFF")
    with wave.open(io.BytesIO(preview), "rb") as audio:
        assert audio.getnchannels() == 1
        assert audio.getsampwidth() == 2
        assert audio.getframerate() > 0
        assert audio.getnframes() > 1_000
