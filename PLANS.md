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
- [x] No malformed rows, blank terms, or duplicate primary keys were found.
- [x] Phase 1 can begin without a data-format blocker.

## Phase 1 - Minimum validated engine

- [ ] Define a versioned adapter interface and validation result model.
- [ ] Implement the first VAD adapter using a synthetic fixture before the
  full source file.
- [ ] Preserve line and stanza structure during tokenization.
- [ ] Add exact normalized matching and POS-sensitive lemma fallback.
- [ ] Produce a token-level audit table with match provenance.
- [ ] Calculate coverage and token- and type-weighted VAD summaries.
- [ ] Export the token audit and summaries to CSV.
- [ ] Add hand-calculated validation cases and automated tests.
- [ ] Document exactly how the first engine can be tested.

## Phase 2 - All five lexicons

- [ ] Implement and validate the remaining four adapters.
- [ ] Retain source-scale values and add explicit derived normalization.
- [ ] Implement categorical emotion and intensity calculations.
- [ ] Implement longest-first phrase matching and overlap policies.
- [ ] Add side-by-side cross-lexicon results without a default consensus score.

## Phase 3 - Local graphical interface

- [ ] Add project creation, text import, analysis, coverage, and audit views.
- [ ] Keep core choices simple while exposing advanced methodology settings.
- [ ] Add a local Windows setup workflow and double-clickable launcher.
- [ ] Add diagnostics and a "Run self-test" control.

## Phase 4 - Corpus and metadata

- [ ] Add the persistent SQLite project database and migrations.
- [ ] Add batch imports, extensible metadata, grouping, and filtering.
- [ ] Add corpus summaries and Excel exports.

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
- [?] Decide, during Phase 2, whether whitespace-containing entries in the
  nominally word-level Warriner and NRC VAD v1 files should participate in
  phrase matching or be treated as exceptional source entries.
- [?] Confirm whether publication years, approximate dates, and date ranges
  should be modeled at import time or deferred until the corpus phase.
