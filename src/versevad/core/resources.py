"""Read-only validation and provenance for locally installed research resources."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Iterable


class ResourceState(StrEnum):
    AVAILABLE = "available"
    MISSING = "missing"
    MALFORMED = "malformed"
    UNSUPPORTED_VERSION = "unsupported_version"


@dataclass(frozen=True)
class ResourceSpec:
    """One locally configured resource expected by an analysis module."""

    resource_id: str
    display_name: str
    relative_path: Path | str
    version: str = ""
    accepted_sha256: tuple[str, ...] = ()
    minimum_bytes: int = 1
    citation: str = ""
    license_notice: str = ""

    def __post_init__(self) -> None:
        if not self.resource_id.strip() or not self.display_name.strip():
            raise ValueError("A resource requires both an ID and a display name.")
        if not str(self.relative_path).strip():
            raise ValueError("A resource requires a configured relative path.")
        if self.minimum_bytes < 0:
            raise ValueError("A resource minimum size cannot be negative.")
        invalid_hashes = [
            value
            for value in self.accepted_sha256
            if len(value) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in value)
        ]
        if invalid_hashes:
            raise ValueError("Accepted resource SHA-256 values must be 64 hex digits.")


@dataclass(frozen=True)
class ResourceStatus:
    resource_id: str
    display_name: str
    state: ResourceState
    configured_path: Path
    version: str
    source_sha256: str
    size_bytes: int | None
    message: str

    @property
    def available(self) -> bool:
        return self.state is ResourceState.AVAILABLE


@dataclass(frozen=True)
class ResourceProvenance:
    """Resource identity retained on a completed module result."""

    resource_id: str
    display_name: str
    version: str
    source_sha256: str
    citation: str = ""
    license_notice: str = ""
    adapter_version: str = ""

    def __post_init__(self) -> None:
        if not self.resource_id.strip() or not self.display_name.strip():
            raise ValueError("Resource provenance requires an ID and display name.")
        if not self.version.strip():
            raise ValueError(
                "Completed resource provenance requires an explicit version."
            )
        if len(self.source_sha256) != 64 or any(
            character not in "0123456789abcdefABCDEF"
            for character in self.source_sha256
        ):
            raise ValueError(
                "Resource provenance requires a 64 hexadecimal digit SHA-256 "
                "checksum."
            )

    @classmethod
    def from_available_status(
        cls,
        status: ResourceStatus,
        *,
        citation: str = "",
        license_notice: str = "",
        adapter_version: str = "",
    ) -> ResourceProvenance:
        if not status.available:
            raise ValueError("Only an available resource can become result provenance.")
        return cls(
            resource_id=status.resource_id,
            display_name=status.display_name,
            version=status.version,
            source_sha256=status.source_sha256,
            citation=citation,
            license_notice=license_notice,
            adapter_version=adapter_version,
        )


class LocalResourceManager:
    """Validate resources in place without editing, copying, or normalizing them."""

    def __init__(self, resource_root: Path | str) -> None:
        self.resource_root = Path(resource_root).resolve()

    @staticmethod
    @lru_cache(maxsize=64)
    def _sha256_for_signature(
        path_text: str,
        size_bytes: int,
        modified_ns: int,
    ) -> str:
        """Hash one unchanged file once per process.

        File size and modification time are part of the cache key, so adding or
        replacing a user-installed resource is detected on the next check.
        """

        del size_bytes, modified_ns
        path = Path(path_text)
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def clear_validation_cache(cls) -> None:
        cls._sha256_for_signature.cache_clear()

    def _path(self, spec: ResourceSpec) -> Path | None:
        candidate = (self.resource_root / Path(spec.relative_path)).resolve()
        if candidate == self.resource_root or self.resource_root in candidate.parents:
            return candidate
        return None

    def validate(self, spec: ResourceSpec) -> ResourceStatus:
        path = self._path(spec)
        fallback_path = self.resource_root / Path(spec.relative_path)
        if path is None:
            return ResourceStatus(
                resource_id=spec.resource_id,
                display_name=spec.display_name,
                state=ResourceState.MALFORMED,
                configured_path=fallback_path,
                version=spec.version,
                source_sha256="",
                size_bytes=None,
                message=(
                    f"{spec.display_name} is configured outside the configured "
                    "resource directory. No file was opened."
                ),
            )
        if not path.exists():
            return ResourceStatus(
                resource_id=spec.resource_id,
                display_name=spec.display_name,
                state=ResourceState.MISSING,
                configured_path=path,
                version=spec.version,
                source_sha256="",
                size_bytes=None,
                message=(
                    f"{spec.display_name} was not found at the configured local path: "
                    f"{path}"
                ),
            )
        if not path.is_file():
            return ResourceStatus(
                resource_id=spec.resource_id,
                display_name=spec.display_name,
                state=ResourceState.MALFORMED,
                configured_path=path,
                version=spec.version,
                source_sha256="",
                size_bytes=None,
                message=f"{spec.display_name} is not a regular file: {path}",
            )
        try:
            file_stat = path.stat()
            size_bytes = file_stat.st_size
            source_sha256 = self._sha256_for_signature(
                str(path),
                size_bytes,
                file_stat.st_mtime_ns,
            )
        except OSError as error:
            return ResourceStatus(
                resource_id=spec.resource_id,
                display_name=spec.display_name,
                state=ResourceState.MALFORMED,
                configured_path=path,
                version=spec.version,
                source_sha256="",
                size_bytes=None,
                message=f"{spec.display_name} could not be read: {error}",
            )
        if size_bytes < spec.minimum_bytes:
            return ResourceStatus(
                resource_id=spec.resource_id,
                display_name=spec.display_name,
                state=ResourceState.MALFORMED,
                configured_path=path,
                version=spec.version,
                source_sha256=source_sha256,
                size_bytes=size_bytes,
                message=f"{spec.display_name} is empty or smaller than expected: {path}",
            )
        accepted_hashes = {value.lower() for value in spec.accepted_sha256}
        if accepted_hashes and source_sha256.lower() not in accepted_hashes:
            return ResourceStatus(
                resource_id=spec.resource_id,
                display_name=spec.display_name,
                state=ResourceState.UNSUPPORTED_VERSION,
                configured_path=path,
                version=spec.version,
                source_sha256=source_sha256,
                size_bytes=size_bytes,
                message=(
                    f"{spec.display_name} is readable, but its checksum is not a "
                    "supported version. The file was not changed."
                ),
            )
        return ResourceStatus(
            resource_id=spec.resource_id,
            display_name=spec.display_name,
            state=ResourceState.AVAILABLE,
            configured_path=path,
            version=spec.version,
            source_sha256=source_sha256,
            size_bytes=size_bytes,
            message=(
                f"{spec.display_name} is available locally and its SHA-256 "
                "checksum was recorded."
            ),
        )

    def validate_many(
        self, specs: Iterable[ResourceSpec]
    ) -> tuple[ResourceStatus, ...]:
        return tuple(self.validate(spec) for spec in specs)
