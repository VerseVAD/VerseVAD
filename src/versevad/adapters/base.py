"""Adapter contracts and user-facing lexicon errors."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from versevad.models import (
    EmotionAssociationLexicon,
    EmotionIntensityLexicon,
    VadLexicon,
)


class LexiconAdapterError(RuntimeError):
    """A safe, plain-language error raised before analysis begins."""

    def __init__(
        self,
        message: str,
        *,
        technical_detail: str = "",
        data_changed: bool = False,
    ) -> None:
        super().__init__(message)
        self.technical_detail = technical_detail
        self.data_changed = data_changed


class VadLexiconAdapter(Protocol):
    adapter_version: str

    def load(self, source_path: Path) -> VadLexicon: ...


class EmotionAssociationAdapter(Protocol):
    adapter_version: str

    def load(self, source_path: Path) -> EmotionAssociationLexicon: ...


class EmotionIntensityAdapter(Protocol):
    adapter_version: str

    def load(self, source_path: Path) -> EmotionIntensityLexicon: ...


def source_sha256(source_path: Path) -> str:
    digest = hashlib.sha256()
    with source_path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_readable_utf8(source_path: Path, display_name: str) -> None:
    if not source_path.is_file():
        raise LexiconAdapterError(
            f"VerseVAD could not find the {display_name} source file. No data "
            "were changed.",
            technical_detail=f"Missing path: {source_path}",
        )
    try:
        source_path.read_bytes().decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise LexiconAdapterError(
            f"VerseVAD could not read the {display_name} file as UTF-8. No "
            "source file was changed.",
            technical_detail=str(error),
        ) from error
