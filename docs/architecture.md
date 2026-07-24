# Architecture Decision: Local Modular Python Application

Status: accepted; the Phase 5 local workspace and Poetic Fingerprint expansion
Stage 4 Age of Acquisition module have been validated.

Date: 2026-07-23

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
this phase.

Phase 4 adds the persistent SQLite repository, immutable complete corpus
batches, dual collection weighting, and Excel export. Phase 4.1 adds the
versioned dual stopword reporting policy. Phase 5 advances the development
package to `0.6.0.dev0`, migrates the database to schema version 3, and adds
named/versioned review scenarios, append-only decisions, occurrence evidence,
baseline-versus-reviewed batch comparison, a separate sentiment presentation,
and lexicon-independent part-of-speech profiles.

The Poetic Fingerprint expansion Stage 0 adds a framework-independent common
module contract under `versevad.core` and a read-only local resource manager.
It is additive: the validated VAD engine and schema version 3 remain unchanged.
Future modules will return immutable common result envelopes containing
explicit observation/calculation/interpretation layers, coverage, warnings, and
reproducibility provenance. See
[`poetic-fingerprint-stage0.md`](poetic-fingerprint-stage0.md).

Expansion Stage 1 advances the development package to `0.7.0.dev0` and
materializes the planned immutable `PoemDocument`. It retains exact
section/stanza/physical-line structure, separate model sentences, shared
tokens, morphology and dependency annotations, optional entities,
orthographic spans, configuration, coverage, and warnings. A one-poem request
is processed once and the same tokens are reused across all selected lexicons.
The common document is available to Stage 0 module inputs and is exported
locally as `poem_document.json`. Stage 1 does not change database schema 3 or
existing affective calculations. See
[`poetic-fingerprint-stage1.md`](poetic-fingerprint-stage1.md).

Expansion Stage 2 advances the development package to `0.8.0.dev0`. Its
read-only workbook adapter and framework-independent concreteness module
consume the shared document without changing it. The optional one-poem path
adds source-scale descriptive statistics, coverage, structural/POS groups,
term rankings, warnings, provenance, and token-level audit exports. The
Streamlit page only presents these tested application results. Stage 2 remains
in memory and does not change database schema 3. See
[`poetic-fingerprint-stage2.md`](poetic-fingerprint-stage2.md).

Expansion Stage 3 advances the development package to `0.9.0.dev0`. Its
read-only SUBTLEX-US workbook adapter and independent frequency module consume
the same shared document without changing it. The optional one-poem path adds
a primary token-weighted median Zipf value, distribution, coverage,
structural/POS groups, term rankings, warnings, provenance, and token-level
audit exports. A non-default scope restricts eligibility to exact model tags
`NOUN`, `VERB`, `ADJ`, and `ADV`; it does not adopt the Language Profile's
broader `VERB`/`AUX` display grouping. Stage 3 uses no `wordfreq` fallback,
remains in memory, and does not change database schema 3. See
[`poetic-fingerprint-stage3.md`](poetic-fingerprint-stage3.md).

Expansion Stage 4 advances the development package to `0.10.0.dev0`. Its
read-only official Kuperman erratum-supplement adapter and independent Age of
Acquisition module consume the same shared document without changing it. The
optional one-poem path adds age-in-years descriptive statistics, coverage,
configurable orientation bands, structural/POS groups, source-response
evidence, represented-term rankings, warnings, provenance, and a token-level
audit. When the corresponding modules are enabled, it can also report
descriptive unique-surface-type Spearman relationships with Frequency and
Concreteness. The non-default contextual content-word scope uses exact model
tags `NOUN`, `VERB`, `ADJ`, and `ADV`; it remains meaningful even though the
source paper describes content-word sampling. Stage 4 remains in memory and
does not change database schema 3 or add these optional results to Projects &
Corpus. See
[`poetic-fingerprint-stage4.md`](poetic-fingerprint-stage4.md).

The formal centroid/region emotional-profile classifier is deferred; the
existing Emotion Profile workspace must not be represented as though it
already implements that model.

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
Shared PoemDocument ---- Scenario and recipe models
        |
Analysis engine ---- Optional analysis modules
        |
Matching engine ---- Lexicon adapter interface
        |                      |
Token records           Read-only source files
        |
SQLite repositories / immutable exports
```

Streamlit must remain a thin presentation layer. Statistical or matching logic
inside page code would be difficult to test and audit.

The part-of-speech calculation therefore lives in framework-independent
application services. The corpus UI derives project/work profiles from current
preserved text versions using the pinned preprocessor, caches the exact
version/model signature for the active session, and exports the resulting
counts and shares without treating them as affective-lexicon metrics.

For the temporary one-poem path, application services create one
`PoemDocument` and pass a prepared read-only view to every selected lexicon.
Structural, sentence, token, dependency, entity, and coverage records therefore
cannot drift between source-specific analyses in the same request.

## Planned package boundaries

```text
src/versevad/
  core/           common module and local-resource contracts
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
- shared preprocessing configuration ID;
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

Future non-affective datasets will be installed locally under an ignored
`resources/` tree or another explicitly configured local root. The common
resource manager records file presence, size, checksum, and support status but
does not replace resource-specific adapter validation.

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

### Pronunciation alternatives and future prosody

Stage 5 is a framework-independent `PronunciationModule` under
`versevad.prosody`. Its read-only `CMUDictAdapter` owns all source parsing and
validation. The analysis engine consumes `ModuleInput`, not Streamlit, and
returns the shared `ModuleResult` contract plus typed token, observed-type, and
physical-line evidence.

The exact local CMUdict dictionary, phone inventory, and symbol inventory are
the authoritative source. The pinned `pronouncing` library supplies only
stress/syllable utilities; its package-bundled dictionary is not an
analysis-time substitute.

All dictionary alternatives travel together from adapter to result. The module
does not collapse them into one hidden candidate. Scholar overrides are
configuration inputs, not edits to the source or shared poem document.

Stage 5 results are currently in-memory One Poem results and exports. A future
schema-4 module-result design can persist the same module envelope,
configuration ID, three resource hashes, token candidates, override evidence,
and line summaries without changing the adapter or calculation API. Stage 6
candidate-meter and Stage 7 rhyme modules will consume explicit alternatives
rather than retrofitting a silently chosen pronunciation.

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
