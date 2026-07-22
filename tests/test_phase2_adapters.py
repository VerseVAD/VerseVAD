from pathlib import Path

import pytest

from versevad.adapters import (
    LexiconAdapterError,
    NrcEmotionAdapter,
    NrcEmotionIntensityAdapter,
    NrcVadV1Adapter,
    NrcVadV21Adapter,
)


SOURCE_ROOT = Path(__file__).parents[1] / "source_lexicons"


@pytest.fixture(scope="module")
def nrc_vad_v1():
    path = SOURCE_ROOT / "NRC-VAD-Lexicon" / "NRC-VAD-Lexicon" / "NRC-VAD-Lexicon.txt"
    return NrcVadV1Adapter().load(path)


@pytest.fixture(scope="module")
def nrc_vad_v21():
    path = (
        SOURCE_ROOT
        / "NRC-VAD-Lexicon-v2.1"
        / "NRC-VAD-Lexicon-v2.1"
        / "NRC-VAD-Lexicon-v2.1.txt"
    )
    return NrcVadV21Adapter().load(path)


@pytest.fixture(scope="module")
def nrc_emotion():
    path = (
        SOURCE_ROOT
        / "NRC-Emotion-Lexicon"
        / "NRC-Emotion-Lexicon"
        / "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt"
    )
    return NrcEmotionAdapter().load(path)


@pytest.fixture(scope="module")
def nrc_intensity():
    path = (
        SOURCE_ROOT
        / "NRC-Emotion-Intensity-Lexicon"
        / "NRC-Emotion-Intensity-Lexicon"
        / "NRC-Emotion-Intensity-Lexicon-v1.txt"
    )
    return NrcEmotionIntensityAdapter().load(path)


def test_nrc_vad_v1_contract_and_identity_normalization(nrc_vad_v1) -> None:
    assert nrc_vad_v1.validation.is_valid
    assert nrc_vad_v1.validation.total_rows == 19_971
    assert nrc_vad_v1.validation.usable_entries == 19_971
    assert nrc_vad_v1.validation.phrase_entries == 132
    assert nrc_vad_v1.validation.source_sha256 == (
        "fd49023f760155c8377424d96ca18d57c6685891d78ba381e47af6f4a1b148a7"
    )
    entry = nrc_vad_v1.lookup("aback")
    assert entry is not None
    assert entry.original.valence == pytest.approx(0.385)
    assert entry.normalized == entry.original
    assert not nrc_vad_v1.metadata.phrase_support


def test_nrc_vad_v21_contract_and_linear_normalization(nrc_vad_v21) -> None:
    assert nrc_vad_v21.validation.is_valid
    assert nrc_vad_v21.validation.total_rows == 54_801
    assert nrc_vad_v21.validation.usable_entries == 54_801
    assert nrc_vad_v21.validation.phrase_entries == 10_073
    assert nrc_vad_v21.validation.source_sha256 == (
        "42c718817fc91d5c133581b24b0bb31d2b14a0b16edb19bc6ce6ab70343e5a45"
    )
    entry = nrc_vad_v21.lookup("a battery")
    assert entry is not None
    assert entry.original.valence == pytest.approx(0.134)
    assert entry.normalized.valence == pytest.approx(0.567)
    assert entry.normalized.arousal == pytest.approx(0.351)
    assert nrc_vad_v21.metadata.phrase_support


def test_nrc_vad_versions_share_family_but_not_version(nrc_vad_v1, nrc_vad_v21) -> None:
    assert nrc_vad_v1.metadata.family == nrc_vad_v21.metadata.family
    assert nrc_vad_v1.metadata.version != nrc_vad_v21.metadata.version


def test_nrc_vad_v21_normalizes_declared_endpoints_and_midpoint(tmp_path: Path) -> None:
    source = tmp_path / "vad-v21.tsv"
    source.write_text(
        "term\tvalence\tarousal\tdominance\n"
        "low\t-1\t-1\t-1\n"
        "middle\t0\t0\t0\n"
        "high\t1\t1\t1\n",
        encoding="utf-8",
    )
    lexicon = NrcVadV21Adapter().load(source)
    assert lexicon.entries["low"].normalized.valence == 0.0
    assert lexicon.entries["middle"].normalized.valence == 0.5
    assert lexicon.entries["high"].normalized.valence == 1.0


def test_nrc_emotion_contract_and_multi_category_associations(nrc_emotion) -> None:
    assert nrc_emotion.validation.is_valid
    assert nrc_emotion.validation.total_rows == 141_540
    assert nrc_emotion.validation.usable_entries == 14_154
    assert nrc_emotion.validation.source_sha256 == (
        "02c661544f4f12ae0c14f9576a10959e8d39a151bb091e455a71a08dcaa2535a"
    )
    happy = nrc_emotion.entries["happy"]
    assert happy.associations == ("anticipation", "joy", "positive", "trust")
    assert len(happy.source_rows) == 10


def test_nrc_intensity_contract_and_missing_categories_remain_absent(nrc_intensity) -> None:
    assert nrc_intensity.validation.is_valid
    assert nrc_intensity.validation.total_rows == 9_829
    assert nrc_intensity.validation.usable_entries == 5_891
    assert nrc_intensity.validation.source_sha256 == (
        "2bed5450b43134e4f849b013424eb76a76e2bdc0ec35df7ec0a0a477031239cb"
    )
    outraged = nrc_intensity.entries["outraged"]
    assert outraged.intensity_map()["anger"] == pytest.approx(0.964)
    assert "joy" not in outraged.intensity_map()


def test_invalid_nrc_vad_source_stops_without_mutating_input(tmp_path: Path) -> None:
    source = tmp_path / "bad-vad.tsv"
    original = b"word\tnot-a-number\t0.2\t0.3\n"
    source.write_bytes(original)
    with pytest.raises(LexiconAdapterError, match="structural problems"):
        NrcVadV1Adapter().load(source)
    assert source.read_bytes() == original
