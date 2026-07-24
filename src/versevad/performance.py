"""Bounded, inspectable process caches and lightweight timing records.

The caches in this module hold derived, immutable VerseVAD objects only. Source
texts and source lexicons are never rewritten or serialized to an external
service. Entries are process-local, versioned, bounded, and safe to discard.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import sys
import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from time import perf_counter
from typing import Callable, Generic, TypeVar


T = TypeVar("T")
CACHE_SCHEMA_VERSION = "stage14-cache-v1"


def _json_value(value: object) -> object:
    if dataclasses.is_dataclass(value):
        return {
            field.name: _json_value(getattr(value, field.name))
            for field in dataclasses.fields(value)
        }
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value.resolve())
    if isinstance(value, dict):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted((_json_value(item) for item in value), key=repr)
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return {
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        "repr": repr(value),
    }


def stable_fingerprint(*values: object) -> str:
    """Return a deterministic local fingerprint for cache dependencies."""

    payload = json.dumps(
        _json_value(values),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CacheEntryMetadata:
    schema_version: str
    created_at: str
    dependency_fingerprint: str
    approximate_size_bytes: int


@dataclass(frozen=True)
class CacheLookup:
    status: str
    reason: str
    lookup_ms: float
    metadata: CacheEntryMetadata


@dataclass(frozen=True)
class CacheStatistics:
    name: str
    max_entries: int
    entry_count: int
    approximate_size_bytes: int
    hits: int
    misses: int
    evictions: int
    corruptions: int


@dataclass(frozen=True)
class OperationTiming:
    module: str
    status: str
    queue_ms: float
    resource_load_ms: float
    processing_ms: float
    serialization_ms: float
    total_ms: float
    cache_status: str
    cache_reason: str


@dataclass(frozen=True)
class AnalysisPerformanceReport:
    enabled: bool
    total_ms: float
    operations: tuple[OperationTiming, ...]
    caches: tuple[CacheStatistics, ...]
    dependency_graph_version: str = "analysis-dependencies-v1"
    note: str = (
        "Timings are descriptive wall-clock observations for this run. "
        "Process-local caches are bounded and may be cleared without data loss."
    )


@dataclass(frozen=True)
class _CacheEntry(Generic[T]):
    value: T
    metadata: CacheEntryMetadata


class BoundedResultCache(Generic[T]):
    """Thread-safe LRU cache with entry validation and diagnostics."""

    def __init__(self, name: str, max_entries: int) -> None:
        if max_entries < 1:
            raise ValueError("A bounded cache requires at least one entry.")
        self.name = name
        self.max_entries = max_entries
        self._entries: OrderedDict[str, _CacheEntry[T]] = OrderedDict()
        self._lock = threading.RLock()
        self._inflight: dict[str, threading.Event] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._corruptions = 0

    def get_or_compute(
        self,
        key: str,
        compute: Callable[[], T],
        *,
        enabled: bool = True,
        validator: Callable[[T], bool] | None = None,
    ) -> tuple[T, CacheLookup]:
        started = perf_counter()
        if not enabled:
            value = compute()
            metadata = self._metadata(key, value)
            return value, CacheLookup(
                status="disabled",
                reason="cache_disabled_for_debugging",
                lookup_ms=(perf_counter() - started) * 1000,
                metadata=metadata,
            )
        while True:
            with self._lock:
                entry = self._entries.get(key)
                if entry is not None:
                    valid = (
                        entry.metadata.schema_version == CACHE_SCHEMA_VERSION
                        and entry.metadata.dependency_fingerprint == key
                        and (validator is None or validator(entry.value))
                    )
                    if valid:
                        self._entries.move_to_end(key)
                        self._hits += 1
                        return entry.value, CacheLookup(
                            status="hit",
                            reason="matching_dependency_fingerprint",
                            lookup_ms=(perf_counter() - started) * 1000,
                            metadata=entry.metadata,
                        )
                    self._entries.pop(key, None)
                    self._corruptions += 1
                inflight = self._inflight.get(key)
                if inflight is None:
                    inflight = threading.Event()
                    self._inflight[key] = inflight
                    break
            # Another caller is computing this exact dependency key. Waiting
            # here prevents duplicate resource-heavy work without serializing
            # unrelated keys.
            inflight.wait()
        try:
            value = compute()
        except BaseException:
            with self._lock:
                self._inflight.pop(key, None)
                inflight.set()
            raise
        metadata = self._metadata(key, value)
        with self._lock:
            self._misses += 1
            self._entries[key] = _CacheEntry(value=value, metadata=metadata)
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
                self._evictions += 1
            self._inflight.pop(key, None)
            inflight.set()
        return value, CacheLookup(
            status="miss",
            reason="no_matching_dependency_fingerprint",
            lookup_ms=(perf_counter() - started) * 1000,
            metadata=metadata,
        )

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def statistics(self) -> CacheStatistics:
        with self._lock:
            return CacheStatistics(
                name=self.name,
                max_entries=self.max_entries,
                entry_count=len(self._entries),
                approximate_size_bytes=sum(
                    item.metadata.approximate_size_bytes
                    for item in self._entries.values()
                ),
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                corruptions=self._corruptions,
            )

    @staticmethod
    def _metadata(key: str, value: T) -> CacheEntryMetadata:
        return CacheEntryMetadata(
            schema_version=CACHE_SCHEMA_VERSION,
            created_at=datetime.now(UTC).isoformat(),
            dependency_fingerprint=key,
            # Shallow size is intentionally inexpensive; diagnostics label it
            # approximate rather than delaying every cache miss with traversal.
            approximate_size_bytes=sys.getsizeof(value),
        )


PREPROCESSING_CACHE: BoundedResultCache[object] = BoundedResultCache(
    "preprocessing",
    max_entries=24,
)
MODULE_RESULT_CACHE: BoundedResultCache[object] = BoundedResultCache(
    "analysis_results",
    max_entries=192,
)
VISUALIZATION_CACHE: BoundedResultCache[object] = BoundedResultCache(
    "visualization_data",
    max_entries=48,
)
EXPORT_CACHE: BoundedResultCache[object] = BoundedResultCache(
    "exports",
    max_entries=24,
)


def cache_statistics() -> tuple[CacheStatistics, ...]:
    return tuple(
        cache.statistics()
        for cache in (
            PREPROCESSING_CACHE,
            MODULE_RESULT_CACHE,
            VISUALIZATION_CACHE,
            EXPORT_CACHE,
        )
    )


def resource_cache_statistics() -> tuple[CacheStatistics, ...]:
    """Expose bounded static-resource and alignment cache counts."""

    from versevad.application import load_lexicon
    from versevad.lexical_semantic.aoa import _load_cached as load_aoa
    from versevad.lexical_semantic.concreteness import (
        _load_cached as load_concreteness,
    )
    from versevad.lexical_semantic.frequency import (
        _load_cached as load_frequency,
    )
    from versevad.prosody.meter import meter_alignment_cache_info
    from versevad.prosody.pronunciation import (
        _load_cached as load_pronunciation,
    )

    caches = (
        ("resource:affective_lexicons", load_lexicon.cache_info()),
        ("resource:concreteness", load_concreteness.cache_info()),
        ("resource:frequency", load_frequency.cache_info()),
        ("resource:age_of_acquisition", load_aoa.cache_info()),
        ("resource:pronunciation", load_pronunciation.cache_info()),
    )
    rows = [
        CacheStatistics(
            name=name,
            max_entries=info.maxsize or 0,
            entry_count=info.currsize,
            approximate_size_bytes=0,
            hits=info.hits,
            misses=info.misses,
            evictions=max(info.misses - info.currsize, 0),
            corruptions=0,
        )
        for name, info in caches
    ]
    meter = meter_alignment_cache_info()
    rows.append(
        CacheStatistics(
            name="meter:alignment_plans",
            max_entries=int(meter["maxsize"]),
            entry_count=int(meter["currsize"]),
            approximate_size_bytes=0,
            hits=int(meter["hits"]),
            misses=int(meter["misses"]),
            evictions=max(
                int(meter["misses"]) - int(meter["currsize"]),
                0,
            ),
            corruptions=0,
        )
    )
    return tuple(rows)


def clear_resource_caches() -> None:
    """Release reloadable static resources and meter alignment plans."""

    from versevad.application import _default_preprocessor, load_lexicon
    from versevad.core.resources import LocalResourceManager
    from versevad.lexical_semantic.aoa import _load_cached as load_aoa
    from versevad.lexical_semantic.concreteness import (
        _load_cached as load_concreteness,
    )
    from versevad.lexical_semantic.frequency import (
        _load_cached as load_frequency,
    )
    from versevad.prosody.meter import (
        clear_candidate_template_cache,
        clear_meter_alignment_cache,
    )
    from versevad.prosody.pronunciation import (
        _load_cached as load_pronunciation,
    )

    load_lexicon.cache_clear()
    load_concreteness.cache_clear()
    load_frequency.cache_clear()
    load_aoa.cache_clear()
    load_pronunciation.cache_clear()
    clear_candidate_template_cache()
    clear_meter_alignment_cache()
    LocalResourceManager.clear_validation_cache()
    _default_preprocessor.cache_clear()


def clear_analysis_caches() -> None:
    PREPROCESSING_CACHE.clear()
    MODULE_RESULT_CACHE.clear()


def clear_visualization_cache() -> None:
    VISUALIZATION_CACHE.clear()


def clear_export_cache() -> None:
    EXPORT_CACHE.clear()


def clear_all_caches() -> None:
    clear_analysis_caches()
    clear_visualization_cache()
    clear_export_cache()
