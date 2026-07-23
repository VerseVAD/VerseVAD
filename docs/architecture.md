# Architecture Decision: Local Modular Python Application

Status: accepted; the Phase 3 local graphical workspace has been validated.

Date: 2026-07-22

## Decision

VerseVAD will use a modular Python analysis engine, a local Streamlit interface,
and a SQLite project database. The interface will call the same tested engine
used by scripts and automated tests. Lexicon parsing will be isolated behind
versioned adapters.

The initial technology choices are:

- Python 3.12 as the first supported runtime;
- Streamlit 1.60.0 for the local browser-based graphical interface;
- the Python `sqlite3` module plus explicit, numbered SQL migrations;
- pandas for tabular analysis and interchange;
- spaCy with a pinned English pipeline for POS-sensitive lemmatization;
- Altair through Streamlit for current interactive charts;
- openpyxl or XlsxWriter for Excel exports after export requirements are tested;
- pytest for engine, adapter, migration, export, and interface smoke tests;
- Jinja templates for local HTML methods reports;
- `uv` as the project-local dependency and Python manager.

No system-wide package installation is required by the architecture. A Windows
launcher will activate the project environment and start the local application.
A packaged executable can be evaluated after the interface is stable; it is not
a Phase 1 dependency.

Phase 1 selected and locked Python 3.12, spaCy 3.8.14,
`en_core_web_sm` 3.8.0, Click 8.4.2, and pytest 9.1.1 in `uv.lock`. The working
runtime, package cache, and `uv` executable are kept in ignored project-local
directories rather than installed computer-wide.

Phase 2 adds no runtime dependency. Its adapter, phrase, categorical, intensity,
comparison, and CSV-export logic remains in the framework-independent Python
package.

Phase 3 pins Streamlit 1.60.0 and its resolved dependency tree in `uv.lock`.
`versevad.application` owns text validation, lexicon loading, analysis
orchestration, friendly view models, and download construction; the Streamlit
page only presents those services. Workspaces and downloads are in memory in
this phase. The development package version is `0.3.0.dev0`.

## Why this fits VerseVAD

Streamlit supplies accessible tables, controls, progress feedback, downloads,
and charts without requiring a separate JavaScript application. SQLite keeps
projects in a portable local file while supporting transactions and backups.
Python has mature linguistic, tabular, statistical, testing, and export tools.

The important boundary is not the framework; it is separation of concerns:

```text
Streamlit UI / CLI
        |
Application services
        |
Analysis engine ---- Scenario and recipe models
        |
Matching engine ---- Lexicon adapter interface
        |                      |
Token records           Read-only source files
        |
SQLite repositories / immutable exports
```

Streamlit must remain a thin presentation layer. Statistical or matching logic
inside page code would be difficult to test and audit.

## Planned package boundaries

```text
src/versevad/
  adapters/       source-specific parsing and validation
  analysis/       matching, coverage, summaries, comparisons
  db/             schema, repositories, transactions, migrations
  exports/        CSV, Excel, HTML, and chart-data outputs
  ui/             Streamlit pages and plain-language presentation
scripts/          diagnostics, setup helpers, and developer utilities
tests/            unit, integration, migration, and synthetic validation tests
```

## Traceability design

Every completed run will be immutable. A run signature will include:

- software and adapter versions;
- text-version checksum;
- lexicon file checksum and source metadata;
- linguistic pipeline and model version;
- preprocessing recipe version;
- analysis scenario version;
- phrase, stopword, negation, matching, and exclusion policies.

Displayed aggregates will be computed from included match records. A drill-down
will retrieve those same records rather than reconstructing an undocumented
approximation.

## Source-file handling

Adapters open source files read-only. Import creates validated internal records
or a cache keyed by the source checksum; it does not edit or replace the source.
Original and normalized scores are separate fields. For example:

- Warriner 1–9 values can be normalized as `(x - 1) / 8`;
- NRC VAD v1 values already occupy 0–1;
- NRC VAD v2.1 values can be normalized as `(x + 1) / 2`.

These formulas are tested adapter metadata. They never overwrite source values.
The Phase 3 comparison view uses only the separately derived values and labels
the original scales and formulas alongside them.

## Local privacy and networking

The running application will not require a cloud service. Setup may access the
internet to obtain the Python runtime, dependencies, or spaCy model after an
explicit explanation. Runtime analysis will not transmit source texts,
lexicons, projects, or results. Usage telemetry will be disabled where the
selected framework permits it.

## Principal risks and mitigations

### Linguistic analysis of poetry

Modern English POS models will make errors on poetic syntax, archaisms, coined
terms, and unusual punctuation. Exact source-form matching therefore precedes
lemma fallback. POS, lemma, context, warnings, and match method remain visible.
User mappings are reviewed, scoped, reversible, and versioned.

### Phrase overlap

NRC VAD v2.1 contains 10,073 whitespace-containing entries. The local policy
also activates Warriner's 102 and NRC VAD v1's 132 whitespace-containing
entries. The matching engine uses deterministic longest-first candidate
generation and an explicit overlap policy. Phrase and suppressed component
candidates remain auditable.

### Reruns and changing judgments

Edits, mappings, exclusions, and recipes can otherwise make old results
irreproducible. Completed runs will point to immutable versions and will never
be silently updated. New judgments create a new scenario and run.

### Installation complexity

The target computer currently has no ordinary `python` or `git` command on its
PATH. Phase 3 setup uses a checksum-verified project-local `uv` executable, a
project-managed Python runtime and environment, and no administrator access.
The launcher uses the locked environment offline and binds Streamlit only to
`127.0.0.1` with usage telemetry disabled.

### Interface scale

The final specification contains many specialist views. Progressive disclosure
will keep a basic create-import-analyze-review-export path visible while moving
advanced scenario and statistical controls behind clearly labeled sections.

## Rejected alternatives

- A cloud-hosted application conflicts with private-text and local-first goals.
- A spreadsheet as the authoritative store cannot reliably preserve versioned
  provenance and transactions.
- A large JavaScript web stack would add packaging and maintenance cost before
  demonstrating methodological value.
- A single monolithic notebook is difficult for beginners to operate and hard
  to test, migrate, or audit.
- A default cross-lexicon consensus would conceal source and family differences.

## Implementation references

- [Streamlit: run an app locally](https://docs.streamlit.io/develop/concepts/architecture/run-your-app)
- [Python: `sqlite3` transaction control](https://docs.python.org/3/library/sqlite3.html)
- [spaCy: models and versioned pipelines](https://spacy.io/usage/models)
- [uv: managed Python installations](https://docs.astral.sh/uv/guides/install-python/)
- [PyInstaller manual](https://pyinstaller.org/en/stable/index.html)
