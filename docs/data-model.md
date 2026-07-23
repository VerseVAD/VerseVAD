# Initial Data Model

This model began as the Phase 0 design. Phase 4 implements persistent local
projects and corpus results. Schema version 2 adds explicit analysis-view and
stopword-methodology fields while migrating existing version-1 databases
transactionally.

Phase 1 now implements immutable in-memory forms of `TextDocument`,
`TokenRecord`, `LexiconMetadata`, `LexiconValidation`, `VadEntry`, `TokenMatch`,
`CoverageStatistics`, `VadSummary`, `PreprocessingMetadata`, and
`AnalysisResult`. CSV exports carry their stable text, token, analysis,
scenario, source-hash, adapter, recipe, and model identifiers. The engine
records remain immutable in-memory values; Phase 4 persists their declared
aggregate and unmatched-review subset for corpus comparison.

Phase 2 adds immutable emotion-association and emotion-intensity entries and
lexicons, explicit lexicon value kinds and dimensions, span-based
`AffectMatchRecord` values, phrase-policy and match-selection enums, category
and intensity statistics, `Phase2AnalysisResult`, and source-specific
`CrossLexiconComparison` metrics. Match records can link one phrase to multiple
token IDs and can point from a suppressed component or overlap to the selected
phrase responsible for suppression. No consensus-score entity is populated.

Phase 3 adds an immutable `AnalysisRequest` and `WorkspaceAnalysis` plus plain
coverage, VAD, emotion-association, emotion-intensity, match, and unmatched view
records. They are framework-independent application models used by both tests
and the Streamlit page. The workspace contains the preserved `TextDocument`,
selected source-specific results, comparison record, recipe choices, and
request signature. The one-poem workspace remains temporary and in memory; it
does not pretend to be a persistent Phase 4 `Project` or `AnalysisRun`. Download manifests
still carry the stable text version, analysis, scenario, adapter, recipe,
software, source-hash, and inclusion metadata produced by the engine.

Phase 3.1 adds VAD definition, interpretation, contributor, and cumulative-load
view records. Phase 4 implements `projects`, `texts`, `text_versions`,
`corpus_batches`, `analysis_runs`, `analysis_metrics`,
`unmatched_observations`, and `unmatched_notes`. Every stored run links to the
active preserved text version, source hashes, adapter versions, recipe,
scenario, software version, selected lexicons, phrase policy, and minimum-match
choice. Phase 4.1 additionally records stopword mode, source/version/hash,
protected words, custom additions/removals, and `analysis_view` on persisted
metrics. Completed corpus batches are immutable; pending or failed batches do
not appear as the current comparison. Excel remains a derived export.

The local source lexicons are not copied into the project database. Their
immutable adapter models are loaded in place from known source paths and hashes.
Lexicon Explorer exposes exact source rows, source values, optional Warriner
standard-deviation/rater fields, normalization formulas, and provenance without
creating a second authoritative copy.

## Identity and versioning

All primary entities use stable opaque IDs. Human-readable titles and filenames
are not identifiers. Versioned scholarly objects are append-only once an
analysis uses them.

```text
Project
  +-- Corpus membership and metadata schema
  +-- Text
  |     +-- TextVersion
  |            +-- StructuralUnit (section/stanza/line/sentence)
  |            +-- TokenOccurrence
  +-- PreprocessingRecipeVersion
  +-- AnalysisScenarioVersion
  +-- ReviewDecisionVersion
  +-- AnalysisRun
        +-- MatchRecord
        +-- AggregateResult
        +-- Warning
        +-- ExportRecord
```

## Core entities

### Project

Title, description, principal researcher, language, research notes, creation
and modification timestamps, and active defaults. User-defined metadata fields
belong to a project schema rather than being added as ad hoc database columns.

### Text and TextVersion

`Text` is the continuing scholarly item. `TextVersion` stores the exact imported
content, SHA-256 checksum, import source, encoding, preservation warnings,
created date, and optional predecessor. Existing analyses retain their original
text-version link after later edits.

### StructuralUnit

Represents hierarchical units such as section, stanza, line, and sentence. It
records type, ordinal position, character span, and parent unit. Empty stanzas
or lines may be represented when needed to preserve structure.

### TokenOccurrence

Records text-version ID, character offsets, structural positions, token and
sentence positions, original surface form, lower form, punctuation-stripped
form, normalized form, POS, lemma, morphological features, token flags,
surrounding context, and preprocessing warnings. Model-derived fields record
the pipeline and model version that produced them.

### LexiconSource and LexiconImport

`LexiconSource` describes the scholarly resource, family, version, citation,
license notice, source scale, language, and unit of analysis. `LexiconImport`
records the local file path, checksum, observed format, validation report,
adapter version, and import date. Original values are retained as source data.

### LexiconEntry and LexiconValue

An entry stores the source term and source row identity. Values store a
dimension or category, original value, original limits, optional normalized
value, formula identifier, and source/import link. Categorical association and
numeric intensity are different value kinds.

### PreprocessingRecipeVersion

Captures Unicode, case, punctuation, tokenization, linguistic model,
possessive, phrase, compound, stopword, proper-noun, numeric, and negation
policies. It is immutable after use.

### ReviewDecisionVersion

A typed decision: annotation, exclusion, or mapping. It stores target and
scope, proposed and approved values, reason, evidence, creator, timestamps,
approval state, predecessor, and whether it affects future runs. Occurrence,
text, author, and project scopes are explicit.

### AnalysisScenarioVersion

Names a reproducible combination of recipe, lexicons, mappings, exclusions,
semantic-risk decisions, minimum-match rules, weighting, and comparison set.

### AnalysisRun

Records lifecycle state (`pending`, `running`, `complete`, `failed`, or
`cancelled`), all input-version IDs, software and adapter versions, timestamps,
warnings, and an integrity signature. Results from incomplete runs are never
presented as complete.

### MatchRecord

Links a token occurrence or phrase span to an exact lexicon entry. It records
candidate order, selected/suppressed state, match method, matched form, POS,
source value, normalized value, negation flag, inclusion status, and the review
decision responsible for any change.

### AggregateResult

Stores or caches a declared statistic only when it can link back to the run and
included match set. Dimensions include structural scope, weighting policy,
denominator, count, coverage, estimate, uncertainty, sparse-result status, and
the explicit `all_matched` or `stopwords_excluded` analysis view.

### ExportRecord

Records format, path, checksum, creation time, run/scenario IDs, and the export
schema version. Excel is an export, never the authoritative database.

## Traceability invariant

Every displayed numeric result must support this path:

```text
AggregateResult -> AnalysisRun -> included MatchRecord(s)
 -> TokenOccurrence(s) -> TextVersion -> preserved original text
 -> LexiconEntry/LexiconValue -> LexiconImport -> source checksum
```

The active scenario, recipe, matching method, and review decision must also be
recoverable from that path.

## Transaction and backup rules

- Database migrations run inside transactions where SQLite permits it.
- A verified backup is created before migration.
- Analysis completion is one atomic state transition.
- Restores never overwrite an open project without explicit confirmation.
- Cached results are disposable and keyed by all relevant input versions.
