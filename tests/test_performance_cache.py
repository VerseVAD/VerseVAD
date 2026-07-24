from __future__ import annotations

from dataclasses import replace
from concurrent.futures import ThreadPoolExecutor
from time import sleep

from versevad.application import (
    AnalysisRequest,
    detailed_export_zip,
    run_workspace_analysis,
)
from versevad.performance import (
    BoundedResultCache,
    clear_all_caches,
)
from versevad.poetry_id import PoetryIDConfiguration
from versevad.prosody import PronunciationConfiguration
from versevad.prosody.pronunciation import parse_pronunciation_overrides
from tests.test_pronunciation import _module as pronunciation_module


def _statuses(workspace) -> dict[str, str]:
    assert workspace.performance is not None
    return {
        operation.module: operation.cache_status
        for operation in workspace.performance.operations
    }


def test_unchanged_analysis_reuses_only_valid_module_results(
    preprocessor,
) -> None:
    clear_all_caches()
    request = AnalysisRequest(
        project_name="Cache test",
        title="Same source",
        original_text="bright night bright night",
        lexicon_ids=("nrc_vad_v1",),
    )

    first = run_workspace_analysis(request, preprocessor=preprocessor)
    second = run_workspace_analysis(request, preprocessor=preprocessor)

    assert _statuses(first)["affective_lexicon:nrc_vad_v1"] == "miss"
    assert _statuses(second)["affective_lexicon:nrc_vad_v1"] == "hit"
    assert _statuses(second)["cross_lexicon_comparison"] == "hit"
    assert first.results == second.results
    assert first.comparison == second.comparison


def test_poetry_id_change_does_not_invalidate_upstream_vad(
    preprocessor,
) -> None:
    clear_all_caches()
    request = AnalysisRequest(
        project_name="Partial invalidation",
        title="One changed threshold",
        original_text="joy love peace light happy calm strong",
        lexicon_ids=("nrc_vad_v1",),
        include_poetry_id=True,
    )
    changed = replace(
        request,
        poetry_id_configuration=replace(
            PoetryIDConfiguration(),
            low_coverage_caution_threshold=0.45,
        ),
    )

    first = run_workspace_analysis(request, preprocessor=preprocessor)
    second = run_workspace_analysis(changed, preprocessor=preprocessor)
    statuses = _statuses(second)

    assert first.results == second.results
    assert statuses["affective_lexicon:nrc_vad_v1"] == "hit"
    assert statuses["cross_lexicon_comparison"] == "hit"
    assert statuses["poetry_id"] == "miss"


def test_disabling_cache_recomputes_without_changing_results(
    preprocessor,
) -> None:
    clear_all_caches()
    cached_request = AnalysisRequest(
        project_name="Cache disabled",
        title="Debugging",
        original_text="bright night",
        lexicon_ids=("nrc_vad_v1",),
    )
    uncached_request = replace(
        cached_request,
        analysis_cache_enabled=False,
    )

    cached = run_workspace_analysis(cached_request, preprocessor=preprocessor)
    uncached = run_workspace_analysis(
        uncached_request,
        preprocessor=preprocessor,
    )

    assert cached.results == uncached.results
    assert _statuses(uncached)["affective_lexicon:nrc_vad_v1"] == "disabled"


def test_pronunciation_change_invalidates_meter_but_not_unrelated_module(
    tmp_path,
    preprocessor,
) -> None:
    clear_all_caches()
    base = AnalysisRequest(
        project_name="Pronunciation invalidation",
        title="Dependent result",
        original_text="\n".join(
            "the stone the stone the stone the stone" for _ in range(4)
        ),
        lexicon_ids=(),
        include_pronunciation=True,
        include_meter=True,
        include_lexical_style=True,
    )
    changed = replace(
        base,
        pronunciation_configuration=PronunciationConfiguration(
            overrides=parse_pronunciation_overrides(
                "stone = S T OW1 N | explicit reading for invalidation test"
            ),
        ),
    )
    module = pronunciation_module(tmp_path)

    run_workspace_analysis(
        base,
        preprocessor=preprocessor,
        pronunciation_module=module,
    )
    second = run_workspace_analysis(
        base,
        preprocessor=preprocessor,
        pronunciation_module=module,
    )
    third = run_workspace_analysis(
        changed,
        preprocessor=preprocessor,
        pronunciation_module=module,
    )

    assert _statuses(second)["meter"] == "hit"
    assert _statuses(second)["lexical_style"] == "hit"
    assert _statuses(third)["meter"] == "miss"
    assert _statuses(third)["lexical_style"] == "hit"


def test_invalid_entry_is_discarded_and_bounded_cache_evicts() -> None:
    cache: BoundedResultCache[object] = BoundedResultCache("test", 2)
    first, first_lookup = cache.get_or_compute("one", lambda: {"valid": True})
    recomputed, second_lookup = cache.get_or_compute(
        "one",
        lambda: {"valid": "recomputed"},
        validator=lambda value: False,
    )
    cache.get_or_compute("two", lambda: 2)
    cache.get_or_compute("three", lambda: 3)
    stats = cache.statistics()

    assert first == {"valid": True}
    assert first_lookup.status == "miss"
    assert recomputed == {"valid": "recomputed"}
    assert second_lookup.status == "miss"
    assert stats.corruptions == 1
    assert stats.evictions >= 1
    assert stats.entry_count == 2


def test_concurrent_same_key_is_computed_once() -> None:
    cache: BoundedResultCache[object] = BoundedResultCache("concurrent", 2)
    calls = []

    def compute():
        calls.append("called")
        sleep(0.02)
        return "shared immutable result"

    with ThreadPoolExecutor(max_workers=4) as executor:
        values = tuple(
            executor.map(
                lambda _index: cache.get_or_compute("same", compute)[0],
                range(4),
            )
        )

    assert values == ("shared immutable result",) * 4
    assert calls == ["called"]
    assert cache.statistics().hits == 3


def test_complete_export_is_cached_by_analysis_identity(
    preprocessor,
) -> None:
    clear_all_caches()
    workspace = run_workspace_analysis(
        AnalysisRequest(
            project_name="Export cache",
            title="Export identity",
            original_text="bright night",
            lexicon_ids=("nrc_vad_v1",),
        ),
        preprocessor=preprocessor,
    )

    first = detailed_export_zip(workspace)
    second = detailed_export_zip(workspace)

    assert first == second
    assert first.startswith(b"PK")
