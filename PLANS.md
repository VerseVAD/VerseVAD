# VerseVAD Implementation Plan

Last updated: 2026-07-22

Status markers: `[x]` complete, `[ ]` pending, `[~]` in progress, `[?]` human
review required.

## Phase 0 - Inspection and planning

- [x] Inspect the repository without modifying source lexicons.
- [x] Identify the five supplied lexicon packages and their primary files.
- [x] Inspect supplied README files and relevant research-paper PDFs.
- [x] Record versions, formats, scales, counts, citations, and usage terms.
- [x] Compute source-file hashes and run structural validation.
- [x] Document architecture, methodology, data model, and testing strategy.
- [x] Create repository safeguards and an initial package/test structure.
- [x] Record unresolved scholarly, licensing, and provenance questions.
- [x] Create a source-control checkpoint if repository initialization is
  available in the working environment.

### Phase 0 exit criteria

- [x] No supplied lexicon file changed.
- [x] All five primary source files are readable and within documented ranges.
- [x] No malformed rows, blank terms, or duplicate source primary keys were
  found; ten Warriner case-insensitive lookup collisions were documented.
- [x] Phase 1 can begin without a data-format blocker.

## Phase 1 - Minimum validated engine

- [x] Define a versioned adapter interface and validation result model.
- [x] Implement the first VAD adapter using a synthetic fixture before the
  full source file.
- [x] Preserve line and stanza structure during tokenization.
- [x] Add exact normalized matching, conservative possessive normalization,
  and POS-sensitive lemma fallback.
- [x] Produce a token-level audit table with match provenance.
- [x] Calculate coverage and token- and type-weighted VAD summaries.
- [x] Export the token audit, coverage, summaries, and manifest to CSV.
- [x] Add hand-calculated validation cases and automated tests.
- [x] Document exactly how the first engine can be tested.

### Phase 1 exit criteria

- [x] The invented validation example reproduces all hand-calculated counts and
  means.
- [x] The local supplied Warriner source passes its adapter contract and works
  end to end without source-file modification.
- [x] Exact entries take priority over lemma entries.
- [x] Unmatched words remain missing rather than receiving neutral scores.
- [x] Case-insensitive source collisions remain separate and unresolved cases
  are sent to review instead of being guessed.
- [x] All Phase 0 and Phase 1 automated tests pass.
- [x] Create the Phase 1 source-control checkpoint.

## Phase 2 - All five lexicons

- [x] Implement and validate the remaining four adapters.
- [x] Retain source-scale values and add explicit derived normalization.
- [x] Implement categorical emotion and intensity calculations.
- [x] Implement longest-first phrase matching and overlap policies.
- [x] Add side-by-side cross-lexicon results without a default consensus score.
- [x] Add a double-clickable five-lexicon validation and audit export.

### Phase 2 exit criteria

- [x] All five private source files pass their adapter contracts and known
  SHA-256 checksums without modification.
- [x] NRC VAD v1 retains its 0-1 source scale; NRC VAD v2.1 retains -1-1 source
  values and separately derives `(original + 1) / 2` values.
- [x] Longest-first phrase selection, suppressed overlaps, and all three phrase
  policies reproduce hand-calculated fixtures.
- [x] Categorical associations state both lexical-token and matched-bearing-token
  denominators, and category rates are not forced to total 100%.
- [x] Emotion-intensity prevalence remains separate from matched-entry intensity;
  missing word-emotion pairs never become zero observations.
- [x] Cross-lexicon exports remain source-specific and contain no consensus score.
- [x] All Phase 0-2 automated tests and the five-lexicon demonstration pass.
- [x] Create the Phase 2 source-control checkpoint.

## Phase 3 - Local graphical interface

- [x] Add a temporary private workspace, paste/UTF-8 text import, analysis,
  coverage, profile, evidence, guidance, and download views.
- [x] Keep the beginner path visible while exposing phrase policy and sparse
  result controls under advanced methodology settings.
- [x] Add a local Windows setup workflow and double-clickable launcher.
- [x] Add command-line diagnostics and an in-app "Run self-test" control.
- [x] Add a friendly scholar summary and CSV reading guide alongside the full
  seven-file audit bundle.

### Phase 3 exit criteria

- [x] A scholar can paste a poem or choose a UTF-8 `.txt` file, analyze it
  locally with any supplied lexicon selection, and inspect results without
  using the command line.
- [x] The original text, line breaks, source hashes, original ratings,
  separately derived normalized ratings, denominators, and match provenance
  remain traceable.
- [x] VAD sources can be viewed on a documented derived 0-1 scale while
  categorical associations and intensity ratings remain separate constructs.
- [x] The Overview, profile, evidence, guidance, friendly CSV, and full audit
  ZIP use plain scholarly language and avoid claims about a poem's emotion.
- [x] Windows setup is project-local; ordinary startup and analysis are offline
  and usage telemetry is disabled.
- [x] All 62 automated tests, the 11-check diagnostic, synthetic validation,
  and a live beginner-path browser test pass.
- [x] Documentation reflects the tested Phase 3 behavior and limitations.
- [x] Create the Phase 3 source-control checkpoint.

## Phase 3.1 - Interpretation and usability

- [x] Define valence, arousal, and dominance in beginner-facing language.
- [x] Explain each normalized mean relative to the derived midpoint with matched
  counts, coverage, and an explicit lexical-evidence scope statement.
- [x] Display all three token- and type-weighted VAD means side by side.
- [x] Rank the largest leave-one-matched-type-out contributors to each token
  mean with source evidence and examples.
- [x] Add cumulative rating and midpoint-deviation totals without presenting
  them as a measured psychological load on a reader.
- [x] Keep Streamlit internal while using VerseVAD titles, navigation, styling,
  and a minimal hidden-branding toolbar configuration.

## Phase 4 - Corpus and metadata

- [x] Add the persistent SQLite project database and explicit first migration.
- [x] Add browser folder import, preserved text versions, stable IDs, source
  hashes, extensible metadata, grouping, and filtering.
- [x] Analyze each work separately and publish comparisons only after a complete
  immutable corpus batch.
- [x] Add token-weighted and work-weighted collection VAD profiles so long works
  can be influential without being the only collection view.
- [x] Add length-sensitive cumulative normative VAD loads alongside mean-based
  token/type results.
- [x] Add persistent per-text, per-lexicon unmatched-vocabulary quality-control
  notes that do not silently alter analyses.
- [x] Add a readable Excel workbook with collection profiles, work-level data,
  cumulative loads, quality-control notes, and provenance.
- [x] Add a local Lexicon Explorer for exact, phrase, lemma-derived, component,
  mapped, uncertainty, comparison, and provenance views.

### Phase 4 exit criteria

- [x] Imported literary texts, projects, results, notes, and workbooks remain
  local and excluded from source control.
- [x] Pending or failed batches never replace the most recent complete corpus
  comparison.
- [x] Missing words and missing work scores remain missing rather than neutral.
- [x] Warriner whitespace-containing entries participate as audited exact phrase
  candidates without modifying the supplied source file.
- [x] Automated calculations reproduce a deliberately divergent long/short-work
  example for token- and work-weighted collection means.
- [x] All 78 automated tests, both synthetic validation demonstrations, the
  11-check diagnostic, live browser workflow, and rendered workbook review pass.
- [x] Current behavior, methodology, limitations, and beginner test steps are
  documented.
- [x] Create the Phase 4 source-control checkpoint using the bundled Git
  executable supplied by the local Codex workspace runtime.

## Phase 4.1 - Dual VAD reporting and project usability

- [x] Report every VAD result for both all matched observations and a separately
  labeled stopword-excluded view.
- [x] Pin and record the spaCy English stopword source, version, active-list
  hash, protected meaning-changing terms, and custom additions/removals.
- [x] Preserve exact published phrase matches as one unit in both views.
- [x] Add content-focused coverage, stopword-sensitivity differences, separate
  contributors, cumulative totals, and population dispersion for both views.
- [x] Persist both views in corpus metrics and include the methodology in CSV,
  JSON, ZIP, and Excel exports.
- [x] Add header workspace tabs and remove the workspace selector from the
  sidebar.
- [x] Add project-scoped deletion requiring an exact, case-sensitive project
  title confirmation.
- [x] Keep the existing visible Windows launcher behavior unchanged.
- [x] Add a comprehensive maintainable Word user manual covering every
  workspace, output, formula, term, safeguard, and troubleshooting path.

### Phase 4.1 exit criteria

- [x] Stopword recognition uses surface and lemma evidence without changing
  exact-first lexicon matching.
- [x] Protected negation, modal, and intensifier terms remain included unless a
  scholar explicitly overrides the protection.
- [x] Custom stopword changes are normalized, auditable, importable, and
  exportable.
- [x] Deleting a project cannot delete another project and is unavailable until
  the exact title is entered.
- [x] Full automated, synthetic, diagnostic, and live browser validation.
- [x] Create a source-control checkpoint using the bundled Git executable.

## Phase 5 - Review system

- [ ] Add reversible flags, exclusions, normalization mappings, and scenarios.
- [ ] Add semantic-risk review and scoped, versioned decisions.

## Phase 6 - Scholarly diagnostics

- [ ] Add contribution analysis, anomaly candidates, close-reading prompts,
  sensitivity analysis, trends, and disagreement views.

## Phase 7 - Publication support

- [ ] Add polished accessible charts and underlying-data exports.
- [ ] Add methods and reproducibility reports.
- [ ] Add backup/restore, a public-domain demonstration project, full user
  documentation, and accessibility review.

## Decisions deliberately deferred

- definitive primary lexicon;
- universal coverage or minimum-match thresholds;
- Jeffers-specific semantic-shift judgments;
- comparison authors or corpora;
- universal text-length controls;
- negation score adjustment;
- a cross-lexicon consensus score;
- a primary inferential statistical test.

## Human review items

- [?] Confirm the provenance and original documentation of the locally supplied
  Warriner data. The package is a secondary XANEW distribution and does not
  include the original Warriner paper or an independent license file.
- [x] Phase 4 activates Warriner's 102 whitespace-containing rows as exact,
  longest-first phrase candidates at the user's request. NRC VAD v1 remains
  word-level by default; NRC VAD v2.1 explicitly supports multiword expressions.
- [x] Publication years, approximate dates, and date ranges can be recorded as a
  free text date label at import/edit time; structured date inference is not
  performed.
