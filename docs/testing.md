# Testing and Validation Strategy

## Principles

Tests must establish calculation and provenance behavior, not merely that the
program runs. Synthetic fixtures will be small enough to calculate by hand and
will never contain copyrighted poems or redistributed lexicon data.

No phase is complete until its applicable automated tests and manual validation
examples pass.

## Test layers

### Unit tests

Cover pure normalization, token, matching, coverage, aggregation, and formula
functions. These tests should avoid the interface and database when possible.

### Adapter contract tests

Run every adapter against synthetic format fixtures and, locally, against the
user-supplied source file. Verify columns, encoding, keys, duplicates, ranges,
blank terms, malformed rows, category sets, phrase counts, and checksums.

Tests in a distributable repository must not embed restricted source entries.

### Integration tests

Exercise text version -> tokenization -> matching -> inclusion -> summary ->
export. Validate stable IDs and drill-down from aggregates to contributing
matches.

### Database and migration tests

Create temporary databases, apply every migration from empty, upgrade from
each supported prior version, verify rollback/failure behavior, and confirm
automatic pre-migration backups.

### Interface smoke tests

Test the beginner path, warnings, disabled actions, empty states, downloads,
and the built-in self-test. Calculation assertions remain in engine tests.

### Visual checks

Render charts and reports with representative long titles, sparse data,
missing values, grayscale, and color-vision-deficiency checks. Verify that
axes, denominators, lexicons, scenarios, sample sizes, and warnings remain
legible.

## Required synthetic cases

- repeated word showing token versus type weighting;
- exact surface match taking precedence over a different lemma entry;
- regular plural and irregular verb lemma fallbacks;
- participle whose direct entry takes precedence;
- ambiguous form used with different parts of speech;
- apostrophe, possessive, and Unicode punctuation variants;
- longest phrase overlapping shorter phrases and components;
- phrase-preferred, unigram-only, and exploratory double-count modes;
- hyphenated compound direct, variant, component, and unmatched outcomes;
- reviewed mappings at occurrence, text, author, and project scopes;
- semantic-risk exclusion in an alternative scenario;
- stopword and proper-noun sensitivity policies;
- negated emotion term flagged without primary-score inversion;
- repeated influential term and leave-one-type-out contribution change;
- no matches, one match, all excluded, empty line, and empty stanza;
- categorical emotion with multiple associations and explicit denominators;
- emotion prevalence separated from mean matched intensity;
- source-scale normalization at minimum, midpoint, and maximum;
- disagreement between VAD sources without a consensus score;
- low coverage and minimum-match sparse-result warnings;
- malformed, duplicate, blank, out-of-range, and encoding-error lexicon rows;
- backup, restore, interrupted run, export, and migration failure behavior.

## Hand-calculated validation corpus

Phase 1 will add invented texts and tiny synthetic lexicons. Every fixture will
include a plain-language worksheet showing tokens, selected matches, coverage,
token-weighted mean, type-weighted mean, and expected warnings. Later phases
will extend the same corpus for phrases, emotions, mappings, sensitivity, and
cross-lexicon disagreement.

## Phase 0 validation performed

The read-only inspection utility validated all five selected source files for
presence, parseable structure, required columns, score ranges, blank terms,
duplicate primary keys, and malformed rows. SHA-256 checksums were recorded in
`docs/lexicons.md`.
