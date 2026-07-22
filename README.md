# VerseVAD

VerseVAD is a planned local scholarly application for transparent analysis of
affective vocabulary in poetry and other literary texts.

It will measure the distribution of words and phrases associated with
normative valence, arousal, dominance, emotion categories, and emotion
intensity. It will **not** determine what a poem "feels," what an author
intended, or what a reader experiences.

## Current status

**Phase 0: inspection and planning.** The application is not yet runnable.
The supplied lexicons have been identified and structurally inspected, and the
initial architecture and data model are documented. Phase 1 will implement the
first validated command-line analysis engine using synthetic text and one VAD
adapter before any full graphical interface is attempted.

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
