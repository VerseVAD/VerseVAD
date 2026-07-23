# Changelog

All notable VerseVAD changes will be recorded here. The project has not yet
made a public release.

## Unreleased

### Added

- Phase 0 project structure and development safeguards.
- Read-only five-lexicon inspection utility.
- Verified lexicon inventory with hashes, formats, ranges, and citations.
- Initial architecture, methodology, data-model, testing, and user-guide
  documentation.
- Project-local, locked Python 3.12 environment configuration.
- Versioned VAD adapter contract and Warriner et al. adapter.
- Poetry-aware structural token records backed by a pinned spaCy English model.
- Exact-first, possessive, and POS-sensitive lemma matching with provenance.
- Token- and type-weighted original-scale and normalized VAD statistics.
- Coverage calculations and sparse/no-match warnings.
- Atomic token-audit, coverage, summary, and analysis-manifest CSV exports.
- Invented hand-calculated validation corpus and double-clickable Phase 1 test.
- Read-only NRC VAD v1, NRC VAD v2.1, NRC Emotion v0.92, and NRC Emotion
  Intensity v1 adapters with source-contract validation.
- Explicit source-value kinds, dimensions, formats, scales, column mappings,
  phrases, citations, usage notices, adapter versions, and source hashes.
- Deterministic longest-first exact phrase matching with phrase-preferred,
  unigram-only, and exploratory phrase-and-component policies.
- Auditable included, unmatched, ineligible, suppressed-component, and
  suppressed-overlap match records.
- Categorical emotion association counts, unique types, stated denominators,
  structural distributions, and contributing terms.
- Emotion-intensity prevalence plus separate token- and type-weighted matched
  intensity statistics without converting absent pairs to zero.
- Side-by-side cross-lexicon metrics that retain source/family identity and do
  not generate a consensus score.
- Seven-file Phase 2 CSV bundle and double-clickable five-lexicon validation.
- Framework-independent Phase 3 application services for validated UTF-8 text
  import, source selection, one-text analysis, view models, and downloads.
- Local Streamlit workspace with paste and `.txt` import, coverage overview,
  normalized VAD comparison, distinct association and intensity profiles,
  filterable match evidence, unmatched vocabulary, and embedded guidance.
- Friendly scholar-summary CSV and CSV reading guide alongside an in-memory ZIP
  containing the complete seven-file Phase 2 audit bundle.
- Project-local Windows setup, offline launcher, diagnostics launcher, and an
  in-app 11-check self-test.
- Phase 3 service, diagnostics, Streamlit smoke, launcher-safety, and local
  browser validation tests.
- Beginner-facing VAD definitions, midpoint interpretations, all-dimension
  token/type comparison, leave-one-type-out contributors, and cumulative
  normative lexical-load views.
- Explicit cumulative rating, above-midpoint, below-midpoint, net-midpoint, and
  absolute-midpoint totals with matched counts and coverage.
- Persistent local SQLite projects, first schema migration, stable work/text
  version identities, transactional import, extensible metadata, and immutable
  complete corpus batches.
- Browser folder import for UTF-8 `.txt` corpora, collection/author/genre
  filtering, and separate work-level analyses.
- Token-weighted and equal-work-weighted collection VAD profiles with divergence
  reporting for mixed-length collections.
- Persistent unmatched-vocabulary quality-control status, notes, and proposed
  mappings that do not alter completed scores.
- Styled Excel corpus workbook with a reading guide, dual collection profiles,
  work-level token/type VAD, cumulative loads, coverage/emotion data, unmatched
  notes, and text/version provenance.
- Lexicon Explorer with exact word/phrase, explicit lemma and user-mapped
  lookup, non-substituting suggestions, derived component averages, original
  and normalized VAD, emotion results, source provenance, and descriptive
  cross-lexicon spread.
- Warriner source standard deviations and dimension-specific rater counts for
  Lexicon Explorer uncertainty inspection.
- Phase 3.1/4 application, repository, aggregation, workbook, Explorer, adapter,
  and interface validation tests.
- Dual VAD reporting for all matched observations and a separately labeled
  stopword-excluded view in one-poem, corpus, comparison, and export workflows.
- A pinned spaCy English stopword policy with protected negation/modal/
  intensifier terms, surface/lemma audit evidence, custom additions/removals,
  text import/export, version, count, and SHA-256 provenance.
- Content-focused coverage, stopword-sensitivity differences, population
  dispersion, cumulative totals, and midpoint-centered contributor rankings
  for both reporting views.
- A machine-readable `phase2_results.json` alongside the CSV audit files.
- Safe local project deletion requiring an exact, case-sensitive project title
  and deleting only that project's related database records.
- Header workspace tabs for One poem, Projects & corpus, and Lexicon Explorer.
- Comprehensive Word user manual with a maintainable Markdown source and
  repeatable local build script.

### Changed

- The lexicon inspector now distinguishes duplicate source keys from
  case-insensitive lookup collisions.
- Phase 2 identifies NRC VAD v1 and v2.1 as versions of the same family rather
  than independent replications.
- Project development version advanced to `0.5.0.dev0`.
- VAD charts now present derived 0-1 dimensions side by side instead of
  visually stacking different dimensions.
- Warriner's 102 whitespace-containing entries now participate as exact,
  longest-first phrase candidates under the selected policy; the inactive-entry
  warning was removed without changing the source file.
- NRC VAD v1's 132 whitespace-containing entries now participate as exact,
  longest-first phrase candidates under the selected policy; its inactive-entry
  caution was removed without changing the source file.
- The visible interface now uses VerseVAD navigation and a minimal toolbar while
  retaining Streamlit only as the internal local UI framework.
- Corpus database schema version 2 records the stopword methodology and an
  explicit analysis view on every persisted comparison metric.
- Contributor ranking now uses the signed midpoint-centered contribution
  `frequency × (normalized rating - 0.5)` while retaining the mean-change audit
  value.

### Fixed

- Preserved ten differently rated Warriner capitalization pairs instead of
  allowing case-insensitive lookup to select one silently.
- Prevented stale Streamlit module state from breaking Lexicon Explorer after
  application-model updates.
- Prevented an already-open Streamlit process from pairing the updated corpus
  page with the older four-argument Excel exporter.
