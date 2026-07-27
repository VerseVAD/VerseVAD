"""Offline audible previews for explicit CMUdict ARPAbet candidates.

The preview is intentionally separate from pronunciation analysis. It converts
the already selected source phones to eSpeak NG's English phoneme notation and
synthesizes a short local WAV file. No text, phones, or audio leave the user's
computer.
"""

from __future__ import annotations

import ctypes
import io
import re
import threading
import wave
from functools import lru_cache
from pathlib import Path

try:
    import espeakng_loader
except ModuleNotFoundError:  # pragma: no cover - guarded degraded startup
    espeakng_loader = None


class PronunciationAudioError(RuntimeError):
    """A local pronunciation preview could not be generated."""


_PHONE_PATTERN = re.compile(r"^(?P<base>[A-Z]+)(?P<stress>[012])?$")

_CONSONANTS = {
    "B": "b",
    "CH": "tS",
    "D": "d",
    "DH": "D",
    "F": "f",
    "G": "g",
    "HH": "h",
    "JH": "dZ",
    "K": "k",
    "L": "l",
    "M": "m",
    "N": "n",
    "NG": "N",
    "P": "p",
    "R": "r",
    "S": "s",
    "SH": "S",
    "T": "t",
    "TH": "T",
    "V": "v",
    "W": "w",
    "Y": "j",
    "Z": "z",
    "ZH": "Z",
}

_VOWELS = {
    "AA": "A:",
    "AE": "a",
    "AH": "V",
    "AO": "O:",
    "AW": "aU",
    "AY": "aI",
    "EH": "E",
    "ER": "3:",
    "EY": "eI",
    "IH": "I",
    "IY": "i:",
    "OW": "oU",
    "OY": "OI",
    "UH": "U",
    "UW": "u:",
}

_RHOTIC_VOWELS = {
    "AA": "A@",
    "AE": "A@",
    "AO": "O@",
    "AW": "aU@",
    "AY": "aI@",
    "EH": "e@",
    "EY": "e@",
    "IH": "i@",
    "IY": "i@",
    "OW": "o@",
    "OY": "OI@",
    "UH": "U@",
    "UW": "U@",
}


def _parse_phones(phones_text: str) -> tuple[tuple[str, str], ...]:
    parsed: list[tuple[str, str]] = []
    for phone in phones_text.strip().upper().split():
        match = _PHONE_PATTERN.fullmatch(phone)
        if match is None:
            raise PronunciationAudioError(
                f"{phone!r} is not a supported ARPAbet phone."
            )
        base = match.group("base")
        stress = match.group("stress") or ""
        if base in _VOWELS and not stress:
            raise PronunciationAudioError(
                f"Vowel {phone!r} needs a CMUdict stress digit."
            )
        if base in _CONSONANTS and stress:
            raise PronunciationAudioError(
                f"Consonant {phone!r} cannot carry a stress digit."
            )
        if base not in _VOWELS and base not in _CONSONANTS:
            raise PronunciationAudioError(
                f"{phone!r} is not in VerseVAD's CMUdict preview inventory."
            )
        parsed.append((base, stress))
    if not parsed:
        raise PronunciationAudioError(
            "A pronunciation preview needs at least one ARPAbet phone."
        )
    if not any(base in _VOWELS for base, _ in parsed):
        raise PronunciationAudioError(
            "A pronunciation preview needs at least one vowel."
        )
    return tuple(parsed)


def normalize_arpabet_phones(phones_text: str) -> str:
    """Validate and normalize an editable CMUdict-style ARPAbet sequence."""

    return " ".join(
        base + stress
        for base, stress in _parse_phones(phones_text)
    )


def arpabet_to_espeak(phones_text: str) -> str:
    """Convert one validated CMUdict phone string to eSpeak English notation."""

    phones = _parse_phones(phones_text)
    converted: list[str] = []
    index = 0
    while index < len(phones):
        base, stress = phones[index]
        if base in _CONSONANTS:
            converted.append(_CONSONANTS[base])
            index += 1
            continue

        next_is_r = (
            index + 1 < len(phones)
            and phones[index + 1][0] == "R"
            and base in _RHOTIC_VOWELS
        )
        if next_is_r:
            value = _RHOTIC_VOWELS[base]
            index += 2
        elif base == "AH" and stress == "0":
            value = "@"
            index += 1
        elif base == "ER" and stress == "0":
            value = "3"
            index += 1
        elif base == "IH" and stress == "0":
            value = "I2"
            index += 1
        elif base == "IY" and stress == "0":
            value = "i"
            index += 1
        else:
            value = _VOWELS[base]
            index += 1

        stress_marker = "'" if stress == "1" else "," if stress == "2" else ""
        converted.append(stress_marker + value)
    return "[[" + "".join(converted) + "]]"


class _ESpeakEngine:
    """Minimal process-local wrapper around the bundled eSpeak NG C API."""

    _AUDIO_OUTPUT_SYNCHRONOUS = 2
    _POSITION_CHARACTER = 1
    _CHARS_UTF8 = 1
    _PHONEMES = 0x100
    _END_PAUSE = 0x1000
    _RATE_PARAMETER = 1
    _CALLBACK = ctypes.CFUNCTYPE(
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_short),
        ctypes.c_int,
        ctypes.c_void_p,
    )

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._chunks: list[bytes] = []
        try:
            if espeakng_loader is None:
                raise PronunciationAudioError(
                    "The optional local speech engine is not installed. Run "
                    "VerseVAD setup again to synchronize locked dependencies."
                )
            self._library = ctypes.CDLL(espeakng_loader.get_library_path())
            self._configure_api()
            data_parent = str(
                Path(espeakng_loader.get_data_path()).parent
            ).encode("utf-8")
            self.sample_rate = self._library.espeak_Initialize(
                self._AUDIO_OUTPUT_SYNCHRONOUS,
                0,
                data_parent,
                0,
            )
            if self.sample_rate <= 0:
                raise PronunciationAudioError(
                    "The local speech engine could not initialize."
                )
            self._callback = self._CALLBACK(self._receive_samples)
            self._library.espeak_SetSynthCallback(self._callback)
            if self._library.espeak_SetVoiceByName(b"en-us") != 0:
                raise PronunciationAudioError(
                    "The local American English preview voice is unavailable."
                )
            self._library.espeak_SetParameter(
                self._RATE_PARAMETER,
                145,
                0,
            )
        except PronunciationAudioError:
            raise
        except Exception as error:
            raise PronunciationAudioError(
                "The local pronunciation preview engine is unavailable."
            ) from error

    def _configure_api(self) -> None:
        library = self._library
        library.espeak_Initialize.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
        )
        library.espeak_Initialize.restype = ctypes.c_int
        library.espeak_SetSynthCallback.argtypes = (self._CALLBACK,)
        library.espeak_SetSynthCallback.restype = None
        library.espeak_SetVoiceByName.argtypes = (ctypes.c_char_p,)
        library.espeak_SetVoiceByName.restype = ctypes.c_int
        library.espeak_SetParameter.argtypes = (
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
        )
        library.espeak_SetParameter.restype = ctypes.c_int
        library.espeak_Synth.argtypes = (
            ctypes.c_void_p,
            ctypes.c_size_t,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_uint,
            ctypes.c_uint,
            ctypes.POINTER(ctypes.c_uint),
            ctypes.c_void_p,
        )
        library.espeak_Synth.restype = ctypes.c_int
        library.espeak_Synchronize.argtypes = ()
        library.espeak_Synchronize.restype = ctypes.c_int
        library.espeak_TextToPhonemes.argtypes = (
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_int,
            ctypes.c_int,
        )
        library.espeak_TextToPhonemes.restype = ctypes.c_char_p
        library.espeak_Info.argtypes = (ctypes.POINTER(ctypes.c_char_p),)
        library.espeak_Info.restype = ctypes.c_char_p

    def _receive_samples(
        self,
        samples: ctypes.POINTER(ctypes.c_short),
        sample_count: int,
        _events: ctypes.c_void_p,
    ) -> int:
        if samples and sample_count > 0:
            self._chunks.append(
                ctypes.string_at(samples, sample_count * ctypes.sizeof(ctypes.c_short))
            )
        return 0

    def synthesize(self, phoneme_input: str) -> bytes:
        with self._lock:
            self._chunks = []
            encoded = phoneme_input.encode("utf-8")
            text_buffer = ctypes.create_string_buffer(encoded + b"\0")
            identifier = ctypes.c_uint()
            result = self._library.espeak_Synth(
                text_buffer,
                len(text_buffer),
                0,
                self._POSITION_CHARACTER,
                0,
                self._CHARS_UTF8 | self._PHONEMES | self._END_PAUSE,
                ctypes.byref(identifier),
                None,
            )
            synchronized = self._library.espeak_Synchronize()
            if result != 0 or synchronized != 0 or not self._chunks:
                raise PronunciationAudioError(
                    "The local speech engine could not synthesize this candidate."
                )
            pcm = b"".join(self._chunks)

        output = io.BytesIO()
        with wave.open(output, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(ctypes.sizeof(ctypes.c_short))
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(pcm)
        return output.getvalue()

    def phonemize_ipa(self, text: str) -> str:
        """Return separated US-English IPA from eSpeak's local G2P rules."""

        cleaned = text.strip()
        if not cleaned:
            raise PronunciationAudioError(
                "A provisional prediction needs a nonblank observed word."
            )
        if any(character.isspace() for character in cleaned):
            raise PronunciationAudioError(
                "Provisional pronunciation prediction accepts one observed "
                "word form at a time."
            )
        with self._lock:
            encoded = cleaned.encode("utf-8")
            text_buffer = ctypes.create_string_buffer(encoded + b"\0")
            text_pointer = ctypes.c_void_p(ctypes.addressof(text_buffer))
            pieces: list[str] = []
            phoneme_mode = 0x02 | (ord("|") << 8)
            while text_pointer.value:
                result = self._library.espeak_TextToPhonemes(
                    ctypes.byref(text_pointer),
                    self._CHARS_UTF8,
                    phoneme_mode,
                )
                if not result:
                    break
                piece = result.decode("utf-8").strip()
                if piece:
                    pieces.append(piece)
            if not pieces:
                raise PronunciationAudioError(
                    "The local G2P engine did not produce a provisional "
                    "pronunciation for this form."
                )
            return " ".join(pieces)

    def version(self) -> str:
        data_path = ctypes.c_char_p()
        value = self._library.espeak_Info(ctypes.byref(data_path))
        return value.decode("utf-8") if value else "unknown"


@lru_cache(maxsize=1)
def _engine() -> _ESpeakEngine:
    return _ESpeakEngine()


@lru_cache(maxsize=256)
def synthesize_arpabet_wav(phones_text: str) -> bytes:
    """Return a locally synthesized mono WAV preview for one ARPAbet sequence."""

    return _engine().synthesize(arpabet_to_espeak(phones_text))


@lru_cache(maxsize=512)
def phonemize_word_ipa(word: str) -> str:
    """Return a local, provisional US-English IPA prediction for one word."""

    return _engine().phonemize_ipa(word)


def espeak_engine_version() -> str:
    """Return the bundled eSpeak NG engine version used for local previews."""

    return _engine().version()
