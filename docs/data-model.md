# Initial Data Model

This model began as the Phase 0 design. Phase 4 implements persistent local
projects and corpus results. Schema version 2 adds explicit analysis-view and
stopword-methodology fields. Phase 5 schema version 3 adds named review
scenarios, immutable scenario-version snapshots, append-only decision
revisions, semantic-risk candidates, and scenario-version links on batches and
runs. Existing version-1 or version-2 databases migrate transactionally after
a verified, non-overwriting `pre-v3` SQLite backup is created.

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
request signature. Expansion Stage 1 adds the shared `PoemDocument` to that
workspace. The one-poem workspace remains temporary and in memory; it does not
pretend to be a persistent Phase 4 `Project` or `AnalysisRun`. Download
manifests still carry the stable text version, analysis, scenario, adapter,
recipe, software, source-hash, and inclusion metadata produced by the engine.

Phase 3.1 adds VAD definition, interpretation, contributor, and cumulative-load
view records. The framework-independent application layer also exposes a
lexicon-independent `PartOfSpeechView` over the preserved run's token records.
Phase 4 implements `projects`, `texts`, `text_versions`,
`corpus_batches`, `analysis_runs`, `analysis_metrics`,
`unmatched_observations`, and `unmatched_notes`. Every stored run links to the
active preserved text version, source hashes, adapter versions, recipe,
scenario, software version, selected lexicons, phrase policy, and minimum-match
choice. Phase 4.1 additionally records stopword mode, source/version/hash,
protected words, custom additions/removals, and `analysis_view` on persisted
metrics. Completed corpus batches are immutable; pending or failed batches do
not appear as the current comparison. Excel remains a derived export.

Phase 5 adds `review_scenarios`, `review_scenario_versions`,
`review_decisions`, and `review_candidates`. `corpus_batches` and
`analysis_runs` store the exact `scenario_version_id`. The scenario-version
snapshot stores its active decision-revision IDs, and every completed analysis
manifest retains the resolved rule payload. Flags are non-scoring; exclusions
and mappings remain auditable and scenario-specific. Part-of-speech corpus
profiles are derived locally from current preserved text versions and the
pinned preprocessing model; they do not depend on lexicon matches.

The local source lexicons are not copied into the project database. Their
immutable adapter models are loaded in place from known source paths and hashes.
Lexicon Explorer exposes exact source rows, source values, optional Warriner
standard-deviation/rater fields, normalization formulas, and provenance without
creating a second authoritative copy.

## Poetic Fingerprint expansion Stages 0 and 1

Stage 0 adds an immutable, framework-independent common envelope for future
optional modules:

```text
ModuleInput
  TextDocument
  TokenRecord[]
  PreprocessingMetadata
  optional PoemDocument (materialized in Stage 1)

ModuleResult
  module/result/text identities
  ModuleMetric[]
  ModuleCoverage[]
  ModuleWarning[]
  ModuleProvenance
    resource provenance[]
```

Metrics distinguish direct observations, computed summaries, and
interpretations. Coverage records carry eligible, matched, and unmatched counts
and keep empty denominators missing. Module provenance records the source-text
hash, software, preprocessing recipe, pipeline, configuration, scenario, and
explicit lookup and inclusion policies plus exact resource checksums.

This contract does not replace `AnalysisResult`, `Phase2AnalysisResult`, or
`WorkspaceAnalysis` in Stage 0. Existing completed runs remain authoritative.
A later read-time compatibility adapter may expose an existing VAD result
through the common envelope without rewriting it.

Stage 1 materializes the additive design:

```text
PoemDocument
  source: TextDocument
  configuration: PreprocessingConfiguration
  preprocessing: PreprocessingMetadata
  structural_units: StructuralUnit[] (section, stanza, physical line)
  sentences: SentenceUnit[]
  tokens: TokenRecord[]
  dependencies: DependencyRecord[]
  entities: EntityRecord[] (optional; disabled by default)
  orthographic_spans: OrthographicSpan[]
  token_classifications: TokenClassification[]
  coverage: ProcessingCoverage
  warnings: DocumentWarning[]
```

The single section and all physical-line records point to exact substrings of
the original, and the lines must reconstruct it exactly. Lookup normalization,
lemma, POS, morphology, sentence, dependency, and optional entity values remain
separate model-derived fields. Orthographic spans expose hyphenated
expressions, contractions, and apostrophe forms without replacing their token
components. Token classifications retain content/function/other/non-lexical
roles, proper-noun evidence through the source POS tag, and model-vocabulary
availability.

Processing coverage validates all count/rate pairs. Model OOV count/rate must
remain missing when the installed model has no usable vector vocabulary.
Dependency confidence likewise remains missing because the pipeline does not
provide calibrated per-edge confidence.

`WorkspaceAnalysis` now carries the common document, and
`ModuleInput.from_poem_document` supplies the exact same source, tokens, and
preprocessing provenance to later optional modules. `poem_document.json`
exports this record in the local one-poem audit bundle.

These records remain in memory and in the derived JSON export. Stage 1 does not
add schema-3 database tables. The approved possible schema-4 tables remain
documented in
[`poetic-fingerprint-stage0.md`](poetic-fingerprint-stage0.md); any migration
still requires tested transactional backup and compatibility behavior.

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

A typed decision revision: flag, exclusion, or mapping. It stores the source
form, optional verified mapping target, lexicon, project, optional preserved
text/version and token position, occurrence/work/project/global scope,
semantic-risk category, rationale, timestamp, active/revoked state, and stable
decision identity. Revoke and restore operations append revisions rather than
updating prior history.

### AnalysisScenarioVersion

Names an immutable snapshot of the active decision revisions in one named
project review scenario. Restoring an older snapshot creates a new version.
An analysis also records recipe, lexicons, minimum-match rule, weighting,
stopword policy, software version, and other calculation inputs separately.

### ReviewCandidate

Stores occurrence-level evidence produced by an analysis for semantic-risk
review, including unmatched forms, case collisions, lemma/possessive/phrase
matches, prior mappings/exclusions, and optionally exact matches. It retains
text/version/token identity, context, proposed lemma, source candidate, match
method, and risk category. Candidate presence does not itself change a score.

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

The part-of-speech profile follows a separate non-lexicon path:

```text
PartOfSpeechView -> TokenOccurrence(s) -> TextVersion
 -> preserved original text -> pinned preprocessing model/version
```

## Transaction and backup rules

- Database migrations run inside transactions where SQLite permits it.
- A verified, non-overwriting backup is created before every schema-3 upgrade
  from an earlier supported database.
- Analysis completion is one atomic state transition.
- Restores never overwrite an open project without explicit confirmation.
- Cached results are disposable and keyed by all relevant input versions.
