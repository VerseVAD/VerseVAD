# Poetic Fingerprint Expansion Stage 6 Validation

Date: 2026-07-24

## What this stage validates

Stage 6 automated and synthetic checks cover:

- all 40 fixed candidates: five patterns across monometer through octameter;
- exact iambic, trochaic, anapestic, dactylic, and amphibrachic lines;
- feminine endings, initial inversion, catalexis, extra and omitted syllables;
- local spondaic and pyrrhic substitutions;
- secondary-stress and function-word flexibility costs;
- retained pronunciation alternatives and the per-line path limit;
- missing pronunciation, empty/nonlexical lines, coverage, deterministic
  ranking, fit, alternatives, and rule-based confidence;
- stanza-aware common meter as iambic `4-3-4-3`, restarted at each stanza;
- framework-independent application integration, UI, scholar summary,
  CSV/JSON/ZIP exports, and operation-level audit evidence; and
- unchanged affective, concreteness, frequency, AoA, pronunciation, database,
  corpus, review, and resource behavior.

All ordinary meter fixtures use invented stress strings or tiny invented
dictionary entries. No literary corpus or complete research resource is
embedded in tracked tests.

## Hand-calculated synthetic command

Run:

```powershell
.\.venv\Scripts\python.exe -m versevad.meter_validation
```

The command checks:

1. the fixed grid contains 40 candidates;
2. exact `0101010101` is nearest to iambic pentameter with zero cost and fit
   `1.0`;
3. an extra final unstressed syllable records one feminine ending;
4. a reversed first iamb records one initial inversion;
5. a missing final syllable in trochaic tetrameter records one catalectic
   ending;
6. an exact common-meter quatrain with iambic foot counts `4-3-4-3` matches
   all four lines and receives scheme fit `1.0`; and
7. a line with an unknown word remains `missing_pronunciation` with no fit.

The expected fit formula for an exact line is:

```text
fit = 1 - 0 / template syllable count = 1.0
```

## Beginner-friendly interface check

1. Double-click `start_versevad.bat`.
2. Open **One Poem** and enter a title.
3. Clear the affective lexicons if you want a meter-only run.
4. Paste this invented pronunciation-friendly quatrain:

   ```text
   the stone the stone the stone the stone
   the stone the stone the stone
   the stone the stone the stone the stone
   the stone the stone the stone
   ```

5. Select **Meter & rhythmic regularity**. Leave its advanced settings at
   their defaults.
6. Click **Analyze this text**.
7. Open **Meter & Rhythm**.
8. Confirm the nearest result says **Common meter (alternating iambic
   tetrameter/trimeter)**, the scheme fit is 100%, the expected foot-count
   column reads `4, 3, 4, 3`, and the complete-quatrain count is `1/1`.
9. Confirm the warning says this is a nearest configured candidate rather than
   definitive scansion or performed rhythm.
10. Download the full audit ZIP and inspect all six `meter_*` files.

For a real poem, out-of-dictionary spellings, dialect, historical forms, and
context-sensitive pronunciations may need documented Stage 5 overrides. Never
interpret an incomplete line as a low or neutral fit.

## Full local checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.phase2_demo
.\.venv\Scripts\python.exe -m versevad.concreteness_validation
.\.venv\Scripts\python.exe -m versevad.frequency_validation
.\.venv\Scripts\python.exe -m versevad.aoa_validation
.\.venv\Scripts\python.exe -m versevad.pronunciation_validation
.\.venv\Scripts\python.exe -m versevad.meter_validation
.\.venv\Scripts\python.exe -m versevad.diagnostics
.\.tools\uv\uv.exe --offline --cache-dir .uv-cache lock --check
git diff --check
```

Rebuild both Word guides from their Markdown sources, render every page, and
inspect all page images before closing Stage 6.

## Completion results

The Stage 6 completion pass on 2026-07-24 produced:

- `204 passed` in the complete automated suite;
- passing Phase 2, Concreteness, SUBTLEX-US Frequency, Kuperman AoA,
  pronunciation, and candidate-meter synthetic validations;
- all 11 local diagnostics passing;
- all five affective source lexicons passing read-only hash and structure
  inspection;
- all three installed CMUdict resources available at official repository
  commit `74790861f652b15e4ac49015a90074ad62a27690` with their expected hashes;
- the offline lock-file check resolving all 86 packages without a lock change;
- `git diff --check` passing; and
- complete visual inspection of both rebuilt Word guides: 40 User Manual pages
  and 28 Values and Terminology Guide pages, with no clipped, overlapping,
  broken, or missing content.

The exact common-meter fixture selected **Common meter (alternating iambic
tetrameter/trimeter)**, assigned expected foot counts `4, 3, 4, 3`, matched all
four analyzable lines, and reported scheme fit `1.0` with complete-stanza
coverage `1/1`.
