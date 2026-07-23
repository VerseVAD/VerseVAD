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

### Changed

- The lexicon inspector now distinguishes duplicate source keys from
  case-insensitive lookup collisions.
- Phase 2 identifies NRC VAD v1 and v2.1 as versions of the same family rather
  than independent replications.
- Project development version advanced to `0.3.0.dev0`.
- VAD charts now present derived 0-1 dimensions side by side instead of
  visually stacking different dimensions.

### Fixed

- Preserved ten differently rated Warriner capitalization pairs instead of
  allowing case-insensitive lookup to select one silently.
