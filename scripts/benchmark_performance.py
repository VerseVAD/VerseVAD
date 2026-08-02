r"""Repeatable VerseVAD performance benchmark using synthetic verse fixtures.

Run from the repository root:
    .venv\Scripts\python.exe scripts\benchmark_performance.py

The script never reads project texts. It uses fixed synthetic lines and writes
only aggregate timing/cache data.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from versevad.application import (  # noqa: E402
    AnalysisRequest,
    detailed_export_zip,
    run_workspace_analysis,
)
from versevad.performance import (  # noqa: E402
    cache_statistics,
    clear_all_caches,
)
from versevad.phonology import PhonologicalConfiguration  # noqa: E402
from versevad.preprocessing import SpacyEnglishPreprocessor  # noqa: E402
from versevad.prosody import MeterAnalysisMode, MeterConfiguration  # noqa: E402


FIXED_LINE = "the stone the stone the stone the stone"


@dataclass(frozen=True)
class BenchmarkResult:
    scenario: str
    line_count: int
    cold_ms: float
    warm_median_ms: float
    warm_samples_ms: tuple[float, ...]
    peak_memory_mib: float | None
    export_cold_ms: float
    export_warm_ms: float
    cache_hits_after: int
    cache_misses_after: int


def _timed(callable_):
    started = time.perf_counter()
    value = callable_()
    return value, (time.perf_counter() - started) * 1000


def _request(name: str, line_count: int, *, complete: bool) -> AnalysisRequest:
    text = "\n".join(FIXED_LINE for _ in range(line_count))
    return AnalysisRequest(
        project_name="VerseVAD synthetic benchmark",
        title=name,
        original_text=text,
        lexicon_ids=(("nrc_vad_v1",) if complete else ()),
        include_concreteness=complete,
        include_frequency=complete,
        include_aoa=complete,
        include_pronunciation=True,
        include_meter=True,
        meter_configuration=MeterConfiguration(
            analysis_mode=MeterAnalysisMode.PERFORMANCE_AWARE,
        ),
        include_phonology=True,
        # The long synthetic fixture is intentionally a single stanza, so its
        # all-pairs rhyme audit exceeds the conservative interactive default.
        # Raise the ceiling only inside the benchmark; the application safety
        # guard and user-facing default remain unchanged.
        phonological_configuration=PhonologicalConfiguration(
            maximum_pair_evaluations=50_000,
        ),
        include_lexical_style=True,
        performance_diagnostics=True,
    )


def _run_scenario(
    name: str,
    line_count: int,
    *,
    complete: bool,
    repetitions: int,
    memory: bool,
    preprocessor: SpacyEnglishPreprocessor,
) -> BenchmarkResult:
    clear_all_caches()
    request = _request(name, line_count, complete=complete)
    if memory:
        tracemalloc.start()
    workspace, cold_ms = _timed(
        lambda: run_workspace_analysis(request, preprocessor=preprocessor)
    )
    peak_mib = None
    if memory:
        _current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mib = peak / (1024 * 1024)
    warm_samples = []
    for _ in range(repetitions):
        _workspace, elapsed = _timed(
            lambda: run_workspace_analysis(
                request,
                preprocessor=preprocessor,
            )
        )
        warm_samples.append(elapsed)
    _archive, export_cold_ms = _timed(
        lambda: detailed_export_zip(workspace)
    )
    _archive, export_warm_ms = _timed(
        lambda: detailed_export_zip(workspace)
    )
    stats = cache_statistics()
    return BenchmarkResult(
        scenario=name,
        line_count=line_count,
        cold_ms=cold_ms,
        warm_median_ms=statistics.median(warm_samples),
        warm_samples_ms=tuple(warm_samples),
        peak_memory_mib=peak_mib,
        export_cold_ms=export_cold_ms,
        export_warm_ms=export_warm_ms,
        cache_hits_after=sum(item.hits for item in stats),
        cache_misses_after=sum(item.misses for item in stats),
    )


def _markdown(
    environment: dict[str, object],
    results: tuple[BenchmarkResult, ...],
) -> str:
    rows = [
        "# VerseVAD performance benchmark",
        "",
        "Synthetic fixtures only; wall-clock values are descriptive, not unit-test gates.",
        "",
        "## Environment",
        "",
    ]
    rows.extend(f"- {key}: {value}" for key, value in environment.items())
    rows.extend(
        (
            "",
            "## Results",
            "",
            "| Scenario | Lines | Cold ms | Warm median ms | Peak MiB | Export cold ms | Export warm ms |",
            "|---|---:|---:|---:|---:|---:|---:|",
        )
    )
    for item in results:
        peak = (
            f"{item.peak_memory_mib:.1f}"
            if item.peak_memory_mib is not None
            else "not measured"
        )
        rows.append(
            f"| {item.scenario} | {item.line_count} | "
            f"{item.cold_ms:.1f} | {item.warm_median_ms:.1f} | {peak} | "
            f"{item.export_cold_ms:.1f} | {item.export_warm_ms:.1f} |"
        )
    rows.extend(
        (
            "",
            "Warm samples use an unchanged source and configuration. A cache miss "
            "is forced before each scenario; immutable static resources may remain "
            "loaded in the process, matching normal local-session behavior.",
            "",
        )
    )
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--memory", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "performance-benchmark-latest.json",
    )
    arguments = parser.parse_args()
    if arguments.repetitions < 1:
        parser.error("--repetitions must be at least one")
    environment = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "logical_cpus": os.cpu_count(),
        "memory_tracing": arguments.memory,
    }
    preprocessor, preprocessor_ms = _timed(SpacyEnglishPreprocessor)
    environment["preprocessor_initialization_ms"] = round(
        preprocessor_ms,
        3,
    )
    sizes = (
        (8, 20, 60)
        if arguments.quick
        else (12, 80, 300)
    )
    results = (
        _run_scenario(
            "short_sound_and_form",
            sizes[0],
            complete=False,
            repetitions=arguments.repetitions,
            memory=arguments.memory,
            preprocessor=preprocessor,
        ),
        _run_scenario(
            "medium_complete",
            sizes[1],
            complete=True,
            repetitions=arguments.repetitions,
            memory=arguments.memory,
            preprocessor=preprocessor,
        ),
        _run_scenario(
            "long_sound_and_form",
            sizes[2],
            complete=False,
            repetitions=arguments.repetitions,
            memory=arguments.memory,
            preprocessor=preprocessor,
        ),
    )
    output = {
        "environment": environment,
        "results": [asdict(item) for item in results],
    }
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(
        json.dumps(output, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path = arguments.output.with_suffix(".md")
    markdown_path.write_text(
        _markdown(environment, results),
        encoding="utf-8",
    )
    print(_markdown(environment, results))
    print(f"JSON: {arguments.output}")
    print(f"Markdown: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
