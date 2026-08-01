# Changelog

All notable changes to VerseVAD are recorded here.

## [1.0.0] - 2026-07-24

### Added

- Local Windows and macOS setup, diagnostics, and browser launchers.
- Single Poem, Compare Poems, Other Text, Lexicon Explorer, Saved Projects,
  Personal Corpus, Reference Corpora, Analysis Library, VerseMap, Form
  Library, Corpus Browser, Documentation, and Methodology workspaces.
- Source-specific VAD, emotion association and intensity, VADER sentiment,
  concreteness, SUBTLEX rarity, Age of Acquisition, sensorimotor,
  readability, lexical diversity, structural, POS, pronunciation, meter,
  rhyme, inherited-form, PoetryID, and VerseMap evidence.
- Explicit token/type weighting, stopword scope, content-word scope,
  coverage, eligible counts, warnings, and provenance where applicable.
- Session pronunciation review and overrides with dependent reanalysis.
- CSV statistical exports, narrative Word reports, and full audit bundles.
- Persistent local projects, private Personal Corpus data, explicit saved
  analyses, versioned review scenarios, and contextual research notes.
- Public-domain VerseMap reference corpus and cross-platform reference updater.
- Six persistent high-contrast application themes.

### Changed

- Versioned VV-PRE as `vv-pre-content-word-profile-1.0`: Frequency, AoA, and
  Word Complexity now use token-weighted `NOUN`/`VERB`/`ADJ`/`ADV`
  occurrences with repetition retained, while Line Accessibility continues to
  use all lexical words per nonblank line. Profile identity and component scope
  are retained in the interface, provenance, and exports.
- Consolidated the interface under Analyze, Collections, Explore, and Learn.
- Standardized report navigation, default-collapsed sections, bottom collapse
  controls, frozen table identifiers, and three-decimal interface display.
- Kept full analytical precision in exports while making front-end tables and
  charts easier to read.
- Made category fit the primary PoetryID archetype and nearest centroid the
  secondary candidate.
- Limited inherited-form no-match results to the ten nearest profiles while
  retaining an inspectable complete registry.
- Reorganized public documentation around maintained user, methodology,
  resource, architecture, data-model, testing, and contributor references.

### Fixed

- Replaced historical-save widget-key heuristics with an allowlist of durable
  analytical state. Legacy action, upload, download, audio, and future
  unregistered widget values are ignored instead of being assigned through
  Streamlit session state.
- Streamlit widget-state conflicts when restoring historical saved analyses.
- Saved-analysis deletion, explicit-save controls, and duplicate-click flows.
- Empty and sparse-result table failures.
- Contraction handling in pronunciation review.
- Theme contrast, chart tooltip, button-label, metric-card overflow, and
  responsive navigation issues.
- Corpus and multi-poem result presentation and comparison edge cases.

### Data and licensing

- VerseVAD code and documentation are GPL-3.0-only.
- Most licensed lexicons and normative resources are intentionally excluded
  from the public repository and installed separately by each user.
- The bundled VerseMap reference corpus contains curated public-domain texts.
