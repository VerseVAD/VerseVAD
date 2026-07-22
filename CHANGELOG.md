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

### Changed

- The lexicon inspector now distinguishes duplicate source keys from
  case-insensitive lookup collisions.

### Fixed

- Preserved ten differently rated Warriner capitalization pairs instead of
  allowing case-insensitive lookup to select one silently.
