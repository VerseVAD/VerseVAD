# VerseVAD

VerseVAD is a planned local scholarly application for transparent analysis of
affective vocabulary in poetry and other literary texts.

It will measure the distribution of words and phrases associated with
normative valence, arousal, dominance, emotion categories, and emotion
intensity. It will **not** determine what a poem "feels," what an author
intended, or what a reader experiences.

## Current status

**Phase 4: the local one-poem, corpus, and Lexicon Explorer workspaces are
complete.** The one-poem path now explains VAD, shows token/type weighting,
top contributors, and cumulative normative lexical loads. Persistent projects
can import an entire folder as separate works, preserve text versions and
metadata, compare works, record unmatched-vocabulary notes, and export a
readable Excel workbook. Collection VAD reports both a token-weighted volume
profile and an equal-work-weighted profile so long poems do not determine the
only result.

Every VAD analysis also reports two clearly labeled lexical views: all matched
tokens and stopwords excluded. The stopword-excluded view uses a pinned,
versioned English list, protects meaning-changing terms such as `not`, `never`,
and `without`, supports auditable custom additions/removals, and preserves
published phrase matches intact. Neither view assigns a value to unmatched
tokens.

Lexicon Explorer searches all five installed sources for exact entries,
phrases, explicitly labeled lemma-derived or user-mapped lookups, emotion
associations/intensities, Warriner uncertainty fields, source provenance, and
derived normalized comparisons. Warriner's 102 and NRC VAD v1's 132
whitespace-containing source entries now participate as exact phrase candidates
under the selected policy.

See:

- [Implementation plan](PLANS.md)
- [Architecture decision](docs/architecture.md)
- [Lexicon inventory](docs/lexicons.md)
- [Methodological commitments](docs/methodology.md)
- [Data model](docs/data-model.md)
- [Testing strategy](docs/testing.md)
- [Beginner user guide](docs/user-guide.md)
- [Comprehensive Word user manual](docs/VerseVAD_User_Manual.docx)
- [Phase 3 validation and test steps](docs/phase3-validation.md)
- [Phase 4 validation and test steps](docs/phase4-validation.md)

## Privacy and source materials

Ordinary analysis will run locally. Runtime code must not upload literary
texts, lexicons, projects, or results.

The installed application does not call ChatGPT or the OpenAI API. After setup,
ordinary use does not depend on a ChatGPT subscription. Cancelling a
subscription would only remove access to future ChatGPT/Codex assistance, not
the already installed local application.

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

In the app, use the workspace tabs across the top:

1. **One poem** accepts pasted text or one `.txt` file and provides readable
   results plus the audit bundle.
2. **Projects & corpus** creates persistent local projects, imports a folder of
   `.txt` works, analyzes complete batches, compares collection views, records
   quality-control notes, and exports Excel.
3. **Lexicon Explorer** looks up one word or phrase in every installed source
   while preserving original scales and match provenance.

See the [beginner user guide](docs/user-guide.md) for interpretation and
troubleshooting, or open the
[comprehensive Word manual](docs/VerseVAD_User_Manual.docx) for every feature,
term, output, and formula in one document.

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
the auditable CSV files plus a machine-readable JSON result to
`phase2_demo_output/` and creates no consensus score. See
[the Phase 2 validation report](docs/phase2-validation.md).
