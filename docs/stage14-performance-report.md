# Stage 14 Performance Report

## Environment

Measurements were taken locally on Windows 11, Python 3.12.13, with 12 logical
CPUs. Fixed synthetic text was used; no private project text entered the
benchmark.

## Pre-change evidence

The pre-change audit recorded:

| Scenario | Cold | Warm unchanged | Peak traced memory |
|---|---:|---:|---:|
| Short Essential | 4,537.8 ms | 65.6 ms | 73.5 MiB cold |
| Medium Sound/Form | 30,495.1 ms | 12,830.3 ms | 147.9 MiB cold |
| Medium Complete | 53,115.7 ms | 14,118.2 ms | 93.1 MiB cold |
| Long Essential | not recorded | 401.5 ms | 10.9 MiB warm |

Those measurements used `tracemalloc`, which materially increases execution
time. A separate no-tracing profile measured the repeated medium meter path at
4,544 ms. Meter consumed 4,497 ms, made 8,064 alignment calls, and dominated
the run.

The initial Streamlit test render took 12,552.7 ms and an unchanged rerun took
168.1 ms. Both rendered without exceptions.

## Implemented changes

- cached token-independent dynamic-programming alignment plans;
- cached the fixed candidate template grid;
- added shared spaCy-preprocessing reuse;
- added dependency-specific immutable module-result caching;
- retained source-hash-keyed resource caches and exposed their statistics;
- cached checksum validation by absolute path, size, and modification time so
  startup readiness checks detect replaced files without re-hashing unchanged
  multi-megabyte workbooks on every Streamlit rerun;
- added duplicate-concurrent-work suppression;
- added cached, on-demand complete exports;
- removed normal-session development reloads;
- added module timing and cache-state diagnostics;
- added cache disable, clear, and resource-release controls;
- retained sequential per-work corpus transactions and added safe
  between-work cancellation hooks;
- added the repeatable `scripts/benchmark_stage14.py` harness.

## Comparable meter result

The same repeated-line meter workload changed from 4,544 ms before caching to:

- 2,889 ms for the first run while populating 1,944 distinct plans;
- 267 ms for the unchanged warm run;
- 14,184 cache hits and no added misses after the second run.

The warm meter portion fell by about 94.1 percent. Exact Stage 6 candidate
outputs were captured before the refactor and remain byte-for-value equivalent
in regression tests.

## Current repeatable quick benchmark

The latest generated report is in
`docs/stage14-benchmark-latest.md` and its machine-readable companion JSON.
The initial post-change quick run without memory tracing recorded:

| Scenario | Lines | Cache-cold analysis | Warm unchanged median | Export cold | Export warm |
|---|---:|---:|---:|---:|---:|
| Sound/Form | 8 | 2,320.4 ms | 1.1 ms | 99.0 ms | 0.1 ms |
| Complete | 20 | 8,776.0 ms | 2.1 ms | 480.4 ms | 0.1 ms |
| Sound/Form | 60 | 1,697.3 ms | 1.2 ms | 795.3 ms | 0.1 ms |

The long repeated-line fixture is intentionally favorable to alignment reuse;
it is not presented as a general corpus-throughput claim. Static resources
remain loaded between cache-cold scenarios, matching an ordinary local
session.

The separate `--memory` observation recorded traced peaks of 147.8 MiB for
short first-use Sound/Form, 81.0 MiB for
medium Complete after resource reuse, and 9.0 MiB for long repeated-line
Sound/Form after resources and plans were warm. `tracemalloc` increased
cache-cold wall time to 18.1, 38.8, and 7.8 seconds respectively; warm
unchanged medians remained between 0.8 and 2.1 ms.

## Invalidation evidence

Automated tests establish that:

- an unchanged source/configuration returns the identical result from cache;
- disabling caches recomputes an identical result;
- a PoetryID-only threshold change reuses VAD and cross-source comparison;
- a pronunciation override invalidates meter while unrelated lexical-style
  evidence remains cached;
- an invalid cache entry is discarded and recomputed;
- four concurrent requests for one exact key perform one computation;
- cache bounds evict least-recently-used entries;
- a completed export is reused only for the same analysis identity.

## Remaining bottlenecks and limits

- First use must still load the selected spaCy model and source resources.
- First-time complete analysis remains dominated by lexical matching and
  source parsing when those resources have not yet been loaded.
- Full ZIP construction is memory-backed because the current Streamlit
  download API consumes bytes. It is now explicit and cached rather than
  rebuilt on hidden-tab reruns. Truly streaming browser downloads remain a
  future architectural change.
- The corpus engine stays sequential because the current workload shares
  large read-only Python objects, and uncontrolled worker processes would
  increase memory substantially. Parallel workers were not introduced without
  evidence that their memory/transaction cost is justified.
- Safe cancellation is available at document boundaries through the engine
  hook. The synchronous Streamlit execution model does not yet expose a live
  cancel button while Python is executing.
- Process-local caches do not persist across an application restart. Saved
  project results remain the persistent research record.

## Performance budgets

The benchmark is intentionally separate from ordinary unit tests. Future
changes should investigate when repeated medians regress by more than 15
percent on the same machine and environment. Correctness, coverage,
provenance, and export-equivalence tests remain hard gates; timing noise does
not make the normal suite flaky.
