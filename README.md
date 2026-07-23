# VerseVAD

VerseVAD is a planned local scholarly application for transparent analysis of
affective vocabulary in poetry and other literary texts.

It will measure the distribution of words and phrases associated with
normative valence, arousal, dominance, emotion categories, and emotion
intensity. It will **not** determine what a poem "feels," what an author
intended, or what a reader experiences.

## Current status

**Phase 3: the local graphical one-poem workspace is complete.** A scholar can
paste a poem or choose a UTF-8 `.txt` file, select any of the five supplied
lexicons, analyze it locally, and begin with readable coverage and profile
views. Matches, unmatched vocabulary, formulas, denominators, source values,
and provenance remain available for audit. Downloads include a compact scholar
summary, a CSV reading guide, and the complete seven-file audit bundle.

The workspace is temporary in Phase 3, so download results before closing the
app. Persistent projects, corpus import, review decisions, and Excel export
belong to later phases.

See:

- [Implementation plan](PLANS.md)
- [Architecture decision](docs/architecture.md)
- [Lexicon inventory](docs/lexicons.md)
- [Methodological commitments](docs/methodology.md)
- [Data model](docs/data-model.md)
- [Testing strategy](docs/testing.md)
- [Beginner user guide](docs/user-guide.md)
- [Phase 3 validation and test steps](docs/phase3-validation.md)

## Privacy and source materials

Ordinary analysis will run locally. Runtime code must not upload literary
texts, lexicons, projects, or results.

The supplied NRC resources prohibit redistribution, and the Warriner data has
non-commercial and no-derivatives conditions. Consequently,
`source_lexicons/` is intentionally excluded from source control. A future
public code release may contain adapters and instructions, but not the source
lexicon data.

## Start the graphical application

On the first run, double-click `setup_windows.bat`. It creates a locked
project-local Python environment; it does not require administrator access or a
system-wide Python installation. Setup may use the internet to download the
pinned runtime and dependencies.

For ordinary use, double-click `start_versevad.bat`. Your browser opens the
local address `http://127.0.0.1:8501`. Keep the small launcher window open while
working. Ordinary startup and analysis use the already installed local files
and do not upload the poem or results.

In the app:

1. paste a poem or choose a UTF-8 `.txt` file;
2. enter a title, select the evidence sources, and click **Analyze this text**;
3. begin with **Overview**, then read **VAD profile** or **Emotion profile**;
4. use **Evidence** only when you want to inspect individual matches;
5. download the friendly summary or full audit ZIP before closing.

See the [beginner user guide](docs/user-guide.md) for interpretation and
troubleshooting.

## Development-only inspection

The Phase 0 inspection script uses only the Python standard library and never
writes to `source_lexicons/`:

```powershell
python scripts\inspect_lexicons.py
```

Nontechnical users do not need to run this inspection command routinely.

## Test the Phase 1 engine

Double-click `test_phase1.bat`. A console window will run an invented,
hand-calculated example and pause so the result can be read. Success is shown as
`VerseVAD Phase 1 validation passed.` The generated CSV files are placed in
`phase1_demo_output/`, which is excluded from source control.

See [the Phase 1 validation report](docs/phase1-validation.md) for the expected
numbers, limitations, and removal instructions.

## Test Phase 2

Double-click `test_phase2.bat`. The test verifies all five source checksums,
reproduces the hand-calculated phrase, category, and intensity examples, then
runs one short invented text independently through all five lexicons. It writes
seven auditable CSV files to `phase2_demo_output/` and creates no consensus
score. See [the Phase 2 validation report](docs/phase2-validation.md).
