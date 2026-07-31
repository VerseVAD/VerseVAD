# VerseVAD Data Model

Status: current for VerseVAD 1.0.0.

VerseVAD separates supplied text, processing annotations, source-resource
entries, match evidence, calculated summaries, saved research objects, and
project/corpus persistence. That separation is essential to auditability.

## Identity and immutability

Stable opaque IDs identify projects, texts, text versions, analyses, runs,
module results, scenarios, saves, and notes. Titles and filenames are labels,
not identifiers.

A completed analysis is immutable. Editing a poem creates a new text version;
reanalyzing creates a new run. Older results retain links to the exact text,
configuration, software, model, adapter, and resource versions used.

## Text and processing records

### TextDocument

Stores the exact imported or pasted text, encoding and preservation warnings,
checksum, and stable text-version identity.

### PoemDocument

Adds a separate processing representation:

```text
PoemDocument
  source TextDocument
  preprocessing configuration and provenance
  section, stanza, and physical-line records
  model sentence records
  token records
  lemma, POS, morphology, and dependency annotations
  orthographic spans and contractions
  optional entity annotations
  processing coverage and warnings
```

Structural records point back to exact source spans. Normalized forms and
model annotations never replace the original.

## Resource and match records

Every resource adapter exposes metadata, supported source hash, adapter
version, original source values, and validation results. Match records retain:

- token occurrence and source span;
- observed, normalized, and lemma forms;
- selected resource entry;
- exact, phrase, lemma, mapped, suppressed, unmatched, or ineligible status;
- source value and any derived normalized value;
- scenario and user decision where applicable; and
- inclusion, exclusion, and denominator decisions.

Phrase matches may reference multiple token IDs. Suppressed component or
overlap candidates point to the selected match responsible for suppression.

## Workspace analysis

A single-text `WorkspaceAnalysis` contains the preserved document, shared
`PoemDocument`, selected affective-source results, optional module results,
cross-source comparison records, configurations, request signature, warnings,
and export artifacts.

Optional modules use a common envelope:

```text
ModuleResult
  module, result, text, and run identities
  direct observations
  calculated metrics
  coverage records
  warnings
  resource and processing provenance
```

Module-specific typed results retain detailed token, line, stanza, term,
candidate, or pair evidence without flattening every method into one ambiguous
table.

## Project database

SQLite schema version 4 is implemented in
`src/versevad/db/repository.py`.

Core tables cover:

- `projects`
- `texts`
- `text_versions`
- `corpus_batches`
- `analysis_runs`
- `analysis_metrics`
- `unmatched_observations`
- `unmatched_notes`
- `review_scenarios`
- `review_scenario_versions`
- `review_decisions`
- `review_candidates`
- `module_results`
- `module_metrics`
- `module_coverage`
- `module_warnings`
- `module_artifacts`
- `corpus_module_aggregates`

Completed corpus batches are immutable. Collection views aggregate persisted
run evidence and never overwrite the work-level results. Equal-work and
observation-weighted summaries remain separate. Pooled lexical measures are
recomputed only where the method requires ordered pooled evidence.

Database migrations are numbered and transactional. Before an older database
is migrated, VerseVAD creates a non-overwriting pre-migration backup.

## Personal Corpus

Personal Corpus uses the project schema and the same analysis services. Its
default database is `projects/personal_corpus.sqlite3`, which is excluded from
Git. Editing creates a new text version; confirmed deletion removes the
selected local poem record through repository services.

## Analysis Library and notes

Analysis Library schema version 1 stores only explicit saves. Its main records
are:

- library item: stable research object and workspace type;
- immutable revision: historical snapshot and privacy mode;
- research note: parent context, optional analysis/project association,
  module or metric anchor, title, body, tags, dates, and export eligibility.

A full save may retain the supplied text and restorable results. A
results-only save retains exported evidence without source text and therefore
cannot restore the original input. Reopening an older save displays the
historical result and version information; it is not silently recalculated.

## VerseMap records

VerseMap Standard Profile schema version 1.0 stores normalized features,
eligible counts, coverage, source identities, and configuration. Reference
corpus schema version 1.0 stores deterministic poem profiles, poet centroids,
PCA coordinates, release metadata, and a manifest tied to source checksums.

PCA coordinates are presentation dimensions. Nearest-neighbor distance uses
the complete coverage-aware standardized feature space, not only the two
displayed axes.

## Missingness and denominators

Missing, unmatched, unresolved, ineligible, suppressed, and unavailable are
distinct states. A missing rating is never serialized as zero. A metric with
no valid denominator is missing rather than reported as `0%`.

Coverage records carry eligible, matched, and unmatched counts plus the policy
that defined eligibility. Exports retain these values even when the interface
shows a rounded summary.

## Local file boundaries

The public repository excludes `source_lexicons/`, most `resources/`,
`projects/`, `source_texts/`, exports, backups, private data, SQLite files,
and environments. The explicit tracked exception is the redistributable
public-domain VerseMap reference corpus.

See [architecture.md](architecture.md), [methodology.md](methodology.md), and
[research-library.md](research-library.md).
