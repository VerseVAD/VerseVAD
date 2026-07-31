from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _benchmark_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / (
        "benchmark_performance.py"
    )
    specification = importlib.util.spec_from_file_location(
        "performance_benchmark",
        path,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def test_performance_benchmark_uses_synthetic_fixture_and_renders_report() -> None:
    module = _benchmark_module()
    result = module.BenchmarkResult(
        scenario="smoke",
        line_count=2,
        cold_ms=10.0,
        warm_median_ms=1.0,
        warm_samples_ms=(1.0,),
        peak_memory_mib=None,
        export_cold_ms=2.0,
        export_warm_ms=0.2,
        cache_hits_after=1,
        cache_misses_after=1,
    )

    report = module._markdown({"python": "test"}, (result,))

    assert module.FIXED_LINE == "the stone the stone the stone the stone"
    assert "| smoke | 2 | 10.0 | 1.0 |" in report
    assert "Synthetic fixtures only" in report
