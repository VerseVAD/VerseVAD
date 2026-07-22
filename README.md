# VerseVAD

VerseVAD is a planned local scholarly application for transparent analysis of
affective vocabulary in poetry and other literary texts.

It will measure the distribution of words and phrases associated with
normative valence, arousal, dominance, emotion categories, and emotion
intensity. It will **not** determine what a poem "feels," what an author
intended, or what a reader experiences.

## Current status

**Phase 1: minimum validated engine is complete.** VerseVAD now has a tested
Warriner VAD adapter, poetry-preserving token records, exact-first matching,
POS-sensitive lemma fallback, coverage, token- and type-weighted descriptive
VAD statistics, token-level audit data, and CSV export. The included validation
demonstration uses only invented text and ratings.

The full graphical application is not built yet. Project persistence, the
remaining four adapters, phrase matching, review scenarios, and corpus analysis
belong to later phases.

See:

- [Implementation plan](PLANS.md)
- [Architecture decision](docs/architecture.md)
- [Lexicon inventory](docs/lexicons.md)
- [Methodological commitments](docs/methodology.md)
- [Data model](docs/data-model.md)
- [Testing strategy](docs/testing.md)
- [Beginner user guide](docs/user-guide.md)

## Privacy and source materials

Ordinary analysis will run locally. Runtime code must not upload literary
texts, lexicons, projects, or results.

The supplied NRC resources prohibit redistribution, and the Warriner data has
non-commercial and no-derivatives conditions. Consequently,
`source_lexicons/` is intentionally excluded from source control. A future
public code release may contain adapters and instructions, but not the source
lexicon data.

## Development-only inspection

The Phase 0 inspection script uses only the Python standard library and never
writes to `source_lexicons/`:

```powershell
python scripts\inspect_lexicons.py
```

Python setup and double-clickable launchers will be added in a later phase.
Nontechnical users will not be expected to run this command routinely.

## Test the Phase 1 engine

Double-click `test_phase1.bat`. A console window will run an invented,
hand-calculated example and pause so the result can be read. Success is shown as
`VerseVAD Phase 1 validation passed.` The generated CSV files are placed in
`phase1_demo_output/`, which is excluded from source control.

See [the Phase 1 validation report](docs/phase1-validation.md) for the expected
numbers, limitations, and removal instructions.
