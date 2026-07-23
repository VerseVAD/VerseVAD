# Poetic Fingerprint Expansion: Stage 0 Reconciliation

Status: implemented as an additive foundation; current VAD behavior is
unchanged.

Date: 2026-07-23

Current-status note: Stage 1 now materializes the shared `PoemDocument`
designed here. See
[`poetic-fingerprint-stage1.md`](poetic-fingerprint-stage1.md). Statements
below about what did not yet exist describe the completed Stage 0 checkpoint,
not current software behavior.

## Purpose

This Stage 0 reconciles the Poetic Fingerprint expansion brief with the
implemented VerseVAD 0.6 foundation. It is distinct from the original,
completed repository-inspection Phase 0.

Stage 0 adds a common module-result contract and a read-only local resource
manager. It records the Stage 1 document-model design and a future persistence
migration, but deliberately does not migrate the database or route existing VAD
analysis through the new contract.

## Decisions

### Emotional-profile classifier deferred

The current **Emotion Profile** workspace presents VAD, eight emotion
associations, sentiment associations, and emotion-intensity evidence. It does
not implement centroid regions, archetype assignment, distance, confidence, or
nearest-alternative profiles.

A formal candidate-profile classifier is deferred until its scholarly model is
specified and validated. Its future interface must say "nearest candidate
profile" or similarly qualified language. The existing workspace must not be
described as though that classifier already exists.

### SUBTLEX-US is the planned frequency source

The lexical-frequency module will use one explicitly identified local
SUBTLEX-US edition. `wordfreq` is not a planned dependency, alternate source,
or fallback. Values from different frequency resources will not be combined.
An absent SUBTLEX entry will remain unmatched, never a numeric zero.

### Existing behavior remains authoritative

The current affective engine, result classes, exports, SQLite schema 3,
review-scenario system, and interface remain unchanged. The new common
contracts are available for future modules and eventual compatibility wrappers.

## Implemented common contract

`versevad.core.modules` provides:

- `AnalysisModule`, a framework-independent protocol with `analyze()` and
  `validate_resources()`;
- `ModuleInput`, linking one preserved `TextDocument`, its traceable token
  representation, and preprocessing metadata;
- `ModuleResult`, an immutable result envelope;
- `ModuleMetric`, with an explicit direct-observation, computed-summary, or
  interpretation layer;
- `ModuleCoverage`, with hand-checkable eligible, matched, and unmatched
  counts; and
- structured warnings and complete module provenance.

The result envelope records:

- stable result, text, and text-version identities;
- module name and version;
- explicitly named metrics and structural scope;
- declared units, weighting, and denominators;
- coverage and unmatched items;
- warnings;
- source-text checksum;
- software, recipe, linguistic-pipeline, configuration, and scenario
  identities;
- explicit lookup and inclusion policies; and
- zero or more exact resource-provenance records.

Metric values may be `None`. Missing or undefined values may not be represented
as NaN or infinity. Coverage for an empty denominator remains `None`.

## Implemented local resource manager

`versevad.core.resources` provides:

- `ResourceSpec`;
- `ResourceStatus`;
- `ResourceState` values `available`, `missing`, `malformed`, and
  `unsupported_version`;
- `ResourceProvenance`; and
- `LocalResourceManager`.

The manager:

- resolves a declared relative path beneath one configured local root;
- refuses paths that escape that root;
- opens source files read-only;
- records size and SHA-256;
- can restrict a module to reviewed checksums;
- distinguishes absence, unreadable or empty data, and an unsupported source
  version; and
- never copies, cleans, normalizes, or writes a resource.

Resource-specific parsing and structural validation will remain inside future
adapters. File presence and checksum validation alone do not prove that a
dataset's rows or values are semantically valid.

## Stage 1 document-model design

### Current implemented representation

`TextDocument` preserves the exact original text and checksum. `TokenRecord`
retains character offsets, stanza and line numbers, sentence and token
positions, surface and normalized forms, POS, lemma, morphology, and flags.
This already protects poetic formatting during current VAD analysis.

It is not yet a materialized hierarchical `PoemDocument`: stanza, line, and
sentence units are encoded through token coordinates rather than explicit
immutable structural records.

### Planned additive representation

Stage 1 should add these records without replacing the preserved source text:

```text
PoemDocument
  TextDocument identity and original text
  StructuralUnit[]  (section, stanza, line)
  SentenceUnit[]    (stored separately because sentences can cross lines)
  TokenRecord[]
  DependencyRecord[]
  EntityRecord[]
```

`StructuralUnit` should contain:

- stable unit ID and text-version ID;
- kind, ordinal, optional parent ID, and display label;
- exact character start and end offsets;
- exact raw substring;
- explicit blank-line or spacing status where applicable; and
- preservation warnings.

`SentenceUnit` should contain its own stable ID and character/token span. It
must not be nested under one line because a sentence can cross line and stanza
boundaries.

`DependencyRecord` should link a token to its head token, dependency label, and
sentence. Dependency and entity fields are model predictions with exact model
provenance. They must remain correctable or replaceable without altering the
original text.

NER should be optional. The current pipeline intentionally disables NER, and
Stage 1 should not enable it silently.

Out-of-vocabulary status must distinguish:

- absence from a statistical language-model vocabulary;
- absence from a named lexical resource;
- absence from a pronunciation dictionary; and
- a failed or uncertain linguistic annotation.

These are different claims and must not share one undifferentiated flag.

## Future persistence migration design

Stage 0 does not change SQLite schema version 3. A later stage may introduce
schema version 4 only after migration tests and a verified, non-overwriting
backup test exist.

The proposed additive tables are:

```text
module_runs
  module_run_id
  project_id / text_id / text_version_id / batch_id
  module_name / module_version
  configuration_id / scenario_id / scenario_version_id
  status / run_signature / provenance_json
  created_at / completed_at

module_metrics
  module_run_id
  metric_id / result_layer / structural_scope
  value type and value
  unit / weighting / denominator / note

module_coverage
  module_run_id
  coverage_id / unit
  eligible_count / matched_count / unmatched_count / coverage_rate
  unmatched_items_json / note

module_resources
  module_run_id
  resource_id / display_name / version / source_sha256
  adapter_version / citation / license_notice

module_warnings
  module_run_id
  code / severity / message / technical_detail
```

Possible structural tables for the shared processing layer are:

```text
structural_units
sentence_units
dependency_records
entity_records
```

The migration must preserve all current tables and completed analysis runs.
Old VAD runs will not be rewritten into the new shape. A future compatibility
adapter may expose an existing immutable VAD result as a `ModuleResult` at read
time.

Module-run completion must be transactional. Incomplete module runs must never
appear in current corpus comparisons.

## Stage 1 entry criteria

Stage 1 may begin when:

1. the complete existing test suite and new Stage 0 tests pass;
2. both synthetic validation demonstrations pass;
3. all five local lexicon diagnostics pass;
4. the contract and migration design match the code;
5. source lexicons remain unchanged; and
6. a source-control checkpoint exists when Git is available.

## Known limitations

- No current analysis is orchestrated through `AnalysisModule`.
- No new research dataset is installed or validated by Stage 0.
- No explicit `PoemDocument` or structural database tables exist yet.
- No formal emotional-profile classifier exists.
- The current general-purpose English model remains fallible on poetry.
- Stage 0 validates resource files at the path and checksum level only;
  adapters must validate resource-specific formats and ranges.
