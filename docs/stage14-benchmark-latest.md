# Stage 14 performance benchmark

Synthetic fixtures only; wall-clock values are descriptive, not unit-test gates.

## Environment

- platform: Windows-11-10.0.26200-SP0
- python: 3.12.13
- logical_cpus: 12
- memory_tracing: False
- preprocessor_initialization_ms: 299.067

## Results

| Scenario | Lines | Cold ms | Warm median ms | Peak MiB | Export cold ms | Export warm ms |
|---|---:|---:|---:|---:|---:|---:|
| short_sound_and_form | 8 | 2320.4 | 1.1 | not measured | 99.0 | 0.1 |
| medium_complete | 20 | 8776.0 | 2.1 | not measured | 480.4 | 0.1 |
| long_sound_and_form | 60 | 1697.3 | 1.2 | not measured | 795.3 | 0.1 |

Warm samples use an unchanged source and configuration. A cache miss is forced before each scenario; immutable static resources may remain loaded in the process, matching normal local-session behavior.
