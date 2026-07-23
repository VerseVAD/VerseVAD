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

Phase 1 added an invented VAD text and tiny synthetic lexicon. Phase 2 extends
the validation materials with overlapping phrases, categorical associations,
emotion intensities, all three phrase policies, explicit denominators, and
cross-lexicon results with no consensus score. Phase 3 reuses those engine
fixtures through framework-independent application services and adds UTF-8
import, friendly-view, download-bundle, diagnostic, launcher, and interface
smoke cases.

## Validation performed

The read-only inspection utility validated all five selected source files for
presence, parseable structure, required columns, score ranges, blank terms,
duplicate primary keys, and malformed rows. SHA-256 checksums were recorded in
`docs/lexicons.md`.

Phase 1 adds 32 passing automated tests. They cover normalization, poem
structure, the pinned POS-sensitive model, exact-first matching, possessives,
lemma fallbacks, repeated words, sparse/no-match behavior, source and
normalized descriptive statistics, case-insensitive source collisions,
Warriner adapter errors and local integration, atomic CSV exports, empty-text
exports, and the hand-calculated demonstration.

Phase 2 brings the full suite to 49 passing tests. The added tests cover all
four new adapters against the local supplied files, exact counts and hashes,
scale normalization, multi-category terms, missing intensity pairs, malformed
source refusal, longest-first phrase selection, overlap and component audit,
line-boundary behavior, all phrase policies, categorical denominators,
token/type intensity statistics, source-specific comparison, seven-file CSV
export, UTF-8 byte-order marks, and safe replacement of prior exports.

Phase 3 brings the full suite to 62 passing tests. Its 13 added tests cover
UTF-8 and CRLF-preserving `.txt` import, invalid and oversized input errors,
plain request validation, all readable view models, match and unmatched
drill-down, scholar-summary and guide encoding, complete in-memory audit ZIPs,
eleven installation/source diagnostics, Streamlit empty and successful states,
all six result tabs, three download controls, and the offline/local-only Windows
helpers. The full suite passes with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

A live local browser validation also exercised the beginner path using all five
private source files: start the app, paste a three-line invented poem, analyze,
read Overview and the normalized VAD view, open normalization details, and run
the in-app self-test. It produced no application error, the VAD chart remained
bounded to 0-1, and all 11 self-test checks passed. File import is verified at
the service and Streamlit smoke-test layers; the manual browser pass deliberately
used paste input to avoid copying any private literary file.
