"""Adapter contracts and user-facing lexicon errors."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from versevad.models import VadLexicon


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
