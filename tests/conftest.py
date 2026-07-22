from __future__ import annotations

import pytest

from versevad.preprocessing import SpacyEnglishPreprocessor


@pytest.fixture(scope="session")
def preprocessor() -> SpacyEnglishPreprocessor:
    return SpacyEnglishPreprocessor()
