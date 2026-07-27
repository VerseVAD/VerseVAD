"""Review-only grapheme-to-phoneme predictions for unmatched observed forms.

Predictions in this module are never analysis matches. The caller must retain
the token's unmatched status until a user explicitly copies or edits the
candidate into the session pronunciation overrides.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from versevad.prosody.audio import (
    PronunciationAudioError,
    espeak_engine_version,
    normalize_arpabet_phones,
    phonemize_word_ipa,
)


class G2PPredictionError(RuntimeError):
    """A provisional pronunciation could not be generated safely."""


G2P_MODEL_ID = "espeak-ng-1.52.0-en-us-text-to-phonemes"

_STRESS_MARKS = {"ˈ": "1", "ˌ": "2"}
_ARPA_VOWELS = {
    "AA",
    "AE",
    "AH",
    "AO",
    "AW",
    "AY",
    "EH",
    "ER",
    "EY",
    "IH",
    "IY",
    "OW",
    "OY",
    "UH",
    "UW",
}

_IPA_TO_ARPABET: dict[str, tuple[str, ...]] = {
    # Consonants
    "p": ("P",),
    "b": ("B",),
    "t": ("T",),
    "d": ("D",),
    "k": ("K",),
    "ɡ": ("G",),
    "g": ("G",),
    "f": ("F",),
    "v": ("V",),
    "θ": ("TH",),
    "ð": ("DH",),
    "s": ("S",),
    "z": ("Z",),
    "ʃ": ("SH",),
    "ʒ": ("ZH",),
    "h": ("HH",),
    "m": ("M",),
    "n": ("N",),
    "ŋ": ("NG",),
    "l": ("L",),
    "ɹ": ("R",),
    "r": ("R",),
    "j": ("Y",),
    "w": ("W",),
    "tʃ": ("CH",),
    "dʒ": ("JH",),
    # US-English allophonic approximations used only in provisional output.
    "ɾ": ("T",),
    "ʔ": ("T",),
    # Monophthongs
    "i": ("IY",),
    "iː": ("IY",),
    "ɪ": ("IH",),
    "ᵻ": ("IH",),
    "ɨ": ("IH",),
    "e": ("EY",),
    "ɛ": ("EH",),
    "æ": ("AE",),
    "ɐ": ("AH",),
    "ʌ": ("AH",),
    "ə": ("AH",),
    "ɜ": ("ER",),
    "ɜː": ("ER",),
    "ɚ": ("ER",),
    "ɝ": ("ER",),
    "ɑ": ("AA",),
    "ɑː": ("AA",),
    "ɒ": ("AA",),
    "ɔ": ("AO",),
    "ɔː": ("AO",),
    "ʊ": ("UH",),
    "u": ("UW",),
    "uː": ("UW",),
    # Diphthongs and common rhotic sequences
    "eɪ": ("EY",),
    "oʊ": ("OW",),
    "aɪ": ("AY",),
    "aʊ": ("AW",),
    "ɔɪ": ("OY",),
    "ɪɹ": ("IH", "R"),
    "ɛɹ": ("EH", "R"),
    "ʊɹ": ("UH", "R"),
    "ɑɹ": ("AA", "R"),
    "ɑːɹ": ("AA", "R"),
    "ɔɹ": ("AO", "R"),
    "ɔːɹ": ("AO", "R"),
    "aɪɹ": ("AY", "R"),
    "aɪɚ": ("AY", "ER"),
    "aʊɹ": ("AW", "R"),
    "aʊɚ": ("AW", "ER"),
    "eɪɹ": ("EY", "R"),
    "oʊɹ": ("OW", "R"),
    "ɪə": ("IH", "AH"),
    "eə": ("EH", "AH"),
    "ʊə": ("UH", "AH"),
    # Syllabic consonants and eSpeak's usual American-English realizations.
    "n̩": ("AH", "N"),
    "m̩": ("AH", "M"),
    "l̩": ("AH", "L"),
    "əl": ("AH", "L"),
}


@dataclass(frozen=True)
class ProvisionalG2PPrediction:
    observed_form: str
    phones_text: str
    ipa_text: str
    model_id: str
    engine_version: str

    @property
    def source_label(self) -> str:
        return (
            f"eSpeak NG {self.engine_version} en-us G2P/text-to-phoneme "
            "(provisional)"
        )


def _split_ipa(ipa_text: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.split(r"[|\s]+", ipa_text.strip())
        if token
    )


def _convert_ipa_token(token: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFC", token).replace("͡", "")
    stress = ""
    if normalized[:1] in _STRESS_MARKS:
        stress = _STRESS_MARKS[normalized[0]]
        normalized = normalized[1:]
    phones = _IPA_TO_ARPABET.get(normalized)
    if phones is None:
        raise G2PPredictionError(
            "The local G2P engine returned an IPA phone that VerseVAD cannot "
            f"safely map to ARPAbet: {normalized!r}."
        )
    output = []
    for phone in phones:
        if phone in _ARPA_VOWELS:
            output.append(phone + (stress or "0"))
            stress = ""
        else:
            output.append(phone)
    return tuple(output)


@lru_cache(maxsize=512)
def predict_arpabet(observed_form: str) -> ProvisionalG2PPrediction:
    """Predict review-only ARPAbet for one out-of-dictionary observed form."""

    cleaned = observed_form.strip()
    if not cleaned:
        raise G2PPredictionError(
            "A provisional prediction needs a nonblank observed word."
        )
    try:
        ipa_text = phonemize_word_ipa(cleaned)
        phones = tuple(
            phone
            for token in _split_ipa(ipa_text)
            for phone in _convert_ipa_token(token)
        )
        phones_text = normalize_arpabet_phones(" ".join(phones))
    except PronunciationAudioError as error:
        raise G2PPredictionError(str(error)) from error
    if not phones_text:
        raise G2PPredictionError(
            "The local G2P engine returned no usable ARPAbet phones."
        )
    return ProvisionalG2PPrediction(
        observed_form=cleaned,
        phones_text=phones_text,
        ipa_text=ipa_text,
        model_id=G2P_MODEL_ID,
        engine_version=espeak_engine_version(),
    )
