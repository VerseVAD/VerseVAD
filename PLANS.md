# VerseVAD Implementation Plan

Last updated: 2026-07-23

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

## Phase 4.2 - NRC VAD v1 phrase activation

- [x] Activate all 132 source-supplied whitespace-containing NRC VAD v1 entries
  as exact, longest-first phrase candidates.
- [x] Keep line/punctuation boundaries, phrase policies, suppressed components,
  source ratings, stopword decisions, and match provenance fully auditable.
- [x] Remove the inactive-entry caution without modifying the source lexicon.
- [x] Update the complete documentation/manual, run full validation, and create
  a source-control checkpoint.

## Phase 5 - Review system

- [x] Add named project review scenarios and immutable scenario-version
  snapshots.
- [x] Add append-only, reversible flag, exclusion, and approved-mapping
  decision revisions with recorded rationales.
- [x] Add occurrence, work, project, and global-within-scenario-use scopes and
  reject conflicting same-scope mappings.
- [x] Apply mappings only after exact, apostrophe/possessive, and lemma
  candidates fail; verify every mapping target as an exact installed entry.
- [x] Preserve review-excluded candidates in the audit while omitting them from
  reviewed aggregates; keep flags non-scoring.
- [x] Add semantic-risk review candidates, optional exact-match review, and
  legacy unmatched-quality-control notes.
- [x] Pin every reviewed batch and run to its exact scenario version and
  decision revisions.
- [x] Add baseline-versus-reviewed immutable batch comparison and review
  decision provenance in CSV, JSON, ZIP, and Excel.
- [x] Create and verify a non-overwriting backup before schema-3 migration.
- [x] Separate positive/negative sentiment from the eight emotion categories.
- [x] Add lexicon-independent part-of-speech quantity/share profiles for one
  poem, combined corpus, work-level comparison, summaries, and Excel.
- [x] Merge common/proper noun tags into one displayed Noun category and label
  English `ADP` output as Preposition while retaining source tags in evidence.
- [x] Merge main-verb and auxiliary/copular tags into one displayed Verb
  category while retaining original `VERB`/`AUX` tags in token evidence.
- [x] Pair broad POS families with a detailed Universal Dependencies tag
  breakdown so every merge remains quantitatively auditable.
- [x] Standardize visible headings and navigation in title case.
- [x] Add a beginner-focused values/terminology Word guide and update the
  comprehensive user manual, methodology, data model, and validation steps.

### Phase 5 exit criteria

- [x] A scholar can retain an unreviewed baseline, apply a named reviewed
  scenario, compare immutable batches, and reproduce the exact active decision
  revisions.
- [x] Revoke, restore, and restore-snapshot operations append history rather
  than rewriting completed decisions, scenario versions, or analysis runs.
- [x] Flags do not change scores; exclusions and mappings change only the
  explicitly selected scenario.
- [x] Occurrence-scoped mappings affect only the pinned token position and
  broader scopes remain explicit in the audit.
- [x] Part-of-speech shares use all eligible lexical tokens independently of
  affective-lexicon coverage and retain the model/version caution.
- [x] Eight-emotion, positive/negative sentiment, and numeric intensity results
  remain separately labeled constructs.
- [x] All 100 automated tests, both synthetic validation demonstrations, the
  11-check diagnostic, source checks, and lock-file check pass.
- [x] Phase 5 documentation and beginner test steps match current behavior.
- [x] Create the Phase 5 source-control checkpoint using the bundled Git
  executable.

## Poetic Fingerprint expansion - Stage 0 reconciliation

- [x] Audit the expansion brief against the implemented Phase 5 architecture,
  data models, tests, exports, and local resources.
- [x] Record that the current Emotion Profile workspace is not a formal
  centroid/region classifier and defer that classifier until its scholarly
  specification is complete.
- [x] Select an explicitly versioned local SUBTLEX-US resource as the sole
  planned frequency source; do not use `wordfreq` as an alternate or fallback.
- [x] Add a framework-independent `AnalysisModule` protocol and immutable common
  module input, metric, coverage, warning, provenance, and result records.
- [x] Add a centralized read-only local resource manager with path containment,
  SHA-256 recording, and available/missing/malformed/unsupported-version states.
- [x] Protect future locally installed research resources from source control
  and document their expected local layout.
- [x] Document the additive Stage 1 `PoemDocument`/structural-unit design and a
  future schema-4 module-result migration without changing schema 3.
- [x] Add synthetic tests for module contracts, missing-value behavior,
  immutability, resource checksums, unsupported versions, malformed data, and
  path containment.
- [x] Run the complete automated suite, both synthetic demonstrations, and all
  local diagnostics; verify documentation and report beginner test steps.
- [x] Create the expansion Stage 0 source-control checkpoint when Git is
  available.

### Expansion Stage 0 exit criteria

- [x] Existing VAD, emotion, corpus, review, interface, and export behavior is
  unchanged.
- [x] Unmatched resource observations remain missing and no generic contract
  requires a neutral numeric fallback.
- [x] New module code is independent of Streamlit and the existing affective
  engine.
- [x] No source lexicon or private literary text is copied, changed, or added to
  source control.
- [x] All automated and local validation checks pass.
- [x] The contract, migration design, plans, changelog, and user-facing project
  status agree.
- [x] Create the expansion Stage 0 source-control checkpoint.

## Poetic Fingerprint expansion - Stage 1 shared processing

- [x] Add an immutable, framework-independent `PoemDocument` that retains the
  exact `TextDocument`, processing configuration, preprocessing provenance,
  structural units, sentences, tokens, dependencies, optional entities,
  orthographic spans, token classifications, coverage, and warnings.
- [x] Parse one exact section plus stanza and physical-line records without
  changing original characters, indentation, blank lines, or line endings.
- [x] Keep NFC lookup normalization separate from source text while preserving
  punctuation, capitalization, token surface forms, lemmas, part-of-speech
  tags, morphological features, and character offsets.
- [x] Record content/function/other/non-lexical roles, proper-noun evidence,
  hyphenated expressions, contractions, apostrophe forms, and model-vocabulary
  availability without inventing missing values.
- [x] Make named-entity recognition an explicit disabled-by-default
  configuration choice and retain sentence/dependency boundary crossings.
- [x] Process each one-poem request once, reuse the exact shared token records
  across all selected lexicons, and make the common document available to
  future `AnalysisModule` implementations.
- [x] Add `poem_document.json` to the full local audit ZIP and show shared
  processing coverage, configuration, provenance, and cautions in Language
  Profile.
- [x] Verify current behavior, methodology, limitations, exports, and
  beginner-friendly Stage 1 test steps in all maintained documentation and the
  rendered Word manual.
- [x] Run the complete automated suite, both synthetic demonstrations, all
  local diagnostics, and the required document render review.
- [x] Create the expansion Stage 1 source-control checkpoint.

### Expansion Stage 1 exit criteria

- [x] Blank stanza separators, em dashes, apostrophes, contractions,
  hyphenated compounds, unusual capitalization, one-word lines,
  punctuation-free poems, archaic forms, and repeated refrains have synthetic
  regression coverage.
- [x] Original source substrings reconstruct exactly from structural records;
  normalized/model-derived forms never overwrite them.
- [x] Unmatched lexicon observations remain missing, and unavailable
  small-model vocabulary coverage remains missing rather than becoming zero.
- [x] POS, lemma, morphology, sentence, dependency, and optional entity records
  are labeled as model outputs, not corrected literary facts.
- [x] Existing exact-first matching, calculations, database schema 3, source
  lexicons, and private literary data remain unchanged.
- [x] All automated and local validation checks pass and the manual render has
  no clipped, overlapping, or broken content.
- [x] Create the expansion Stage 1 source-control checkpoint.

## Poetic Fingerprint expansion - Stage 2 concreteness

- [x] Inspect the locally supplied Brysbaert, Warriner, and Kuperman
  supplementary workbook and paper without changing or redistributing either
  file; record their SHA-256 hashes, source structure, scale, citation, and
  stated limitations.
- [x] Add a versioned, read-only workbook adapter and an independent
  Concreteness `AnalysisModule` using the shared `PoemDocument`.
- [x] Apply exact normalized surface lookup before lemma lookup, followed only
  by documented conservative fallbacks; keep every unmatched observation
  missing and exclude model-tagged proper nouns by default.
- [x] Calculate token-weighted descriptive statistics, configurable extreme
  bands, token and normalized-surface-type coverage, part-of-speech summaries,
  line and stanza summaries, term rankings, and low-coverage warnings.
- [x] Activate exact source-supplied two-word expressions within physical-line
  boundaries and retain the phrase-to-token rating assignment in the audit.
- [x] Add optional one-poem interface controls, a dedicated Concreteness
  Profile, readable summary rows, and complete CSV/JSON audit exports.
- [x] Add synthetic adapter, matching, missing-resource, Unicode, proper-name,
  repetition, empty-input, low-coverage, deterministic-output, and export
  tests, plus an optional local-source contract check.
- [x] Update methodology, architecture, user guidance, validation notes,
  changelog, and the rendered Word manual with exact beginner-friendly test
  steps.
- [x] Run the complete automated suite, synthetic demonstrations, diagnostics,
  source checks, lock-file check, and document render review.
- [x] Create the expansion Stage 2 source-control checkpoint.

### Expansion Stage 2 exit criteria

- [x] The installed 39,954-row source passes its exact adapter contract in
  place, including 37,058 single words, 2,896 two-word expressions, the 1-5
  scale, and the recorded source checksum.
- [x] Exact surface matches take priority over lemma matches; phrases,
  fallbacks, proper-name exclusions, and unmatched tokens remain explicit in
  the token audit.
- [x] Empty and wholly unmatched inputs produce missing aggregates and missing
  coverage rates rather than zero or neutral concreteness scores.
- [x] Thresholds are configurable VerseVAD orientation aids and are not
  attributed to the source paper as validated categories.
- [x] Results are described as normative lexical concreteness evidence, not
  imagery success, readability, literary quality, cognition, or the emotion
  of a poem.
- [x] Existing affective results, review behavior, database schema 3, source
  lexicons, private texts, and local research resources remain unchanged and
  excluded from source control.
- [x] All automated and local validation checks pass, and the manual render has
  no clipped, overlapping, or broken content.
- [x] Create the expansion Stage 2 source-control checkpoint.

## Poetic Fingerprint expansion - Stage 3 lexical frequency and rarity

- [x] Download the official Ghent University SUBTLEX-US Zipf workbook and
  methodological papers into the ignored local `resources/` directory; inspect
  them without modification and record filenames, SHA-256 hashes, source
  structure, scale, citation, and limitations.
- [x] Add a versioned, read-only SUBTLEX-US adapter and an independent
  Frequency `AnalysisModule` using the shared immutable `PoemDocument`.
- [x] Apply exact normalized word-form lookup before explicit lemma lookup,
  followed only by documented conservative fallbacks; leave absent forms
  unmatched rather than assigning frequency zero, and exclude model-tagged
  proper nouns by default.
- [x] Calculate token-weighted median Zipf frequency as the primary summary,
  plus mean, population standard deviation, inclusive quartiles, IQR, range,
  configurable rarity/commonness bands, token/type coverage, content-word-only
  summaries, an optional non-default `NOUN`/`VERB`/`ADJ`/`ADV`-only analysis
  scope, POS/line/stanza summaries, term rankings, and warnings.
- [x] Add optional one-poem interface controls, a dedicated Frequency & Rarity
  Profile, readable summary rows, distribution-ready data, and complete
  CSV/JSON audit exports.
- [x] Add synthetic adapter, matching, missing-resource, malformed-resource,
  Unicode, proper-name, repetition, empty-input, low-coverage, deterministic,
  configuration, export, and optional local-source contract tests.
- [x] Update methodology, architecture, user guidance, validation notes,
  changelog, and both rendered Word guides with exact beginner-friendly test
  steps and corpus-relative interpretation limits.
- [x] Run the complete automated suite, all synthetic demonstrations,
  diagnostics, source checks, lock-file check, and full document render review.
- [x] Create the expansion Stage 3 source-control checkpoint.

### Expansion Stage 3 exit criteria

- [x] The pinned official SUBTLEX-US source passes its exact read-only adapter
  contract in place and retains its recorded source checksum.
- [x] Exact word forms take priority over lemma matches; fallbacks,
  proper-name exclusions, and unmatched tokens remain explicit in the audit.
- [x] Empty and wholly unmatched inputs produce missing aggregates and missing
  coverage rates rather than zero or invented Zipf scores.
- [x] Median Zipf frequency is emphasized, the logarithmic 1-7 scale and
  corpus dependence are explained, and configurable bands are identified as
  VerseVAD orientation aids.
- [x] Results are described as corpus-relative lexical frequency evidence, not
  difficulty, sophistication, accessibility, intelligence, or literary quality.
- [x] No `wordfreq` dependency or fallback is introduced, and values from
  different frequency resources are not combined.
- [x] Existing affective and concreteness results, review behavior, database
  schema 3, source lexicons, private texts, and local research resources remain
  unchanged and excluded from source control.
- [x] All automated and local validation checks pass, and both rendered Word
  guides have no clipped, overlapping, or broken content.
- [x] Create the expansion Stage 3 source-control checkpoint.

## Poetic Fingerprint expansion - Stage 4 age of acquisition

- [x] Download and inspect the official Kuperman, Stadthagen-Gonzalez, and
  Brysbaert erratum supplement and publisher paper without modifying either;
  record their SHA-256 hashes, source structure, rating method, citation, and
  usage limitations.
- [x] Reconcile the paper's content-word sampling description with the actual
  supplement, which includes rated polyfunctional forms that can occur as
  function words in a poem; retain an optional contextual
  `NOUN`/`VERB`/`ADJ`/`ADV` scope rather than assuming every exact spelling
  match is a content-word use.
- [x] Add a versioned, read-only Kuperman adapter and an independent optional
  Age of Acquisition `AnalysisModule` using the shared immutable
  `PoemDocument`.
- [x] Apply exact normalized observed-form lookup before explicit lemma lookup,
  followed only by documented conservative fallbacks; keep unrated and
  unmatched observations missing and exclude model-tagged proper nouns by
  default.
- [x] Calculate mean, median, population dispersion, inclusive quartiles, IQR,
  range, configurable early/later orientation bands, token/type coverage,
  part-of-speech, line, stanza, term, and source-response summaries.
- [x] Add optional non-default content-word-only analysis, descriptive
  type-level relationships with enabled frequency and concreteness modules,
  low-coverage and sparse-pair warnings, and stable longitudinal-ready metric
  identifiers without adding a schema migration.
- [x] Add optional one-poem interface controls, a dedicated Age of Acquisition
  Profile, readable summary rows, and complete CSV/JSON audit exports.
- [x] Add synthetic adapter, matching, missing/malformed-resource, Unicode,
  proper-name, function-word-scope, repetition, empty-input, low-coverage,
  deterministic, relationship, configuration, export, and optional
  local-source contract tests.
- [x] Update methodology, architecture, user guidance, validation notes,
  changelog, local resource instructions, and both rendered Word guides with
  exact beginner-friendly test steps and the required non-diagnostic warning.
- [~] Run the complete automated suite, all synthetic demonstrations,
  diagnostics, source checks, lock-file check, and full PDF/Word render review.
- [x] Create the expansion Stage 4 source-control checkpoint.

### Expansion Stage 4 exit criteria

- [x] The pinned official supplement passes its exact read-only adapter
  contract in place, retains its recorded source checksum, and preserves the
  19 source entries without numeric AoA ratings as unavailable values.
- [x] Exact word forms take priority over lemma matches; fallbacks,
  proper-name exclusions, optional contextual content-word exclusions,
  low-response evidence, and unmatched tokens remain explicit in the audit.
- [x] Empty and wholly unmatched inputs produce missing aggregates and missing
  coverage rates rather than zero or an invented acquisition age.
- [x] Configurable early/later bands are identified as VerseVAD orientation
  aids, and source response counts and uncertainty remain distinct from the
  poem-level dispersion of matched normative means.
- [x] Results are described as retrospective normative lexical AoA evidence,
  not word difficulty, grade level, intelligence, familiarity, comprehension,
  or evidence of cognitive impairment or decline.
- [x] Kuperman ratings are not combined with the separate derivative and
  test-based AoA workbooks; existing affective, concreteness, and frequency
  behavior, database schema 3, private texts, and local research resources
  remain unchanged and excluded from source control.
- [~] All automated and local validation checks pass, the downloaded paper has
  been visually verified page by page, and both Word guides have no clipped,
  overlapping, or broken content.
- [x] Create the expansion Stage 4 source-control checkpoint.

## Phase 6 - Scholarly diagnostics

- [ ] Add anomaly candidates and structured close-reading prompts.
- [ ] Add corpus trends, source-disagreement views, and optional descriptive
  change-over-sequence views.
- [ ] Add additional sensitivity views beyond the completed stopword,
  weighting, phrase-policy, and review-scenario comparisons.

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
- [x] VerseVAD activates Warriner's 102 and NRC VAD v1's 132
  whitespace-containing rows as exact, longest-first phrase candidates at the
  user's request. NRC VAD v2.1 explicitly supports multiword expressions.
- [x] Publication years, approximate dates, and date ranges can be recorded as a
  free text date label at import/edit time; structured date inference is not
  performed.
