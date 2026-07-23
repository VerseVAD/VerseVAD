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
helpers.

Phase 3.1 and Phase 4 bring the full suite to 78 passing tests. The added tests
cover VAD definitions and interpretation, leave-one-type-out contributors,
hand-calculated cumulative midpoint loads, Warriner exact phrase activation and
uncertainty fields, folder decoding, SQLite migrations and closed connections,
text version preservation, extensible metadata, immutable batch publication,
persistent unmatched notes, mixed-length token/work collection means, an
end-to-end two-work corpus run, Excel workbook structure, Lexicon Explorer
exact/phrase/lemma/mapped/component behavior, and all three Streamlit workspace
entry paths.

Phase 4.1 brings the full suite to 87 passing tests. The added coverage verifies
dual all-matched/stopword-excluded aggregation; pinned, protected, and custom
stopword behavior; exact phrase retention; midpoint-centered contribution
formulas; both result views in CSV/JSON/SQLite/Excel; schema-version-2
migration; exact-confirmation project deletion; top workspace tabs; stale
Explorer recovery; and the comprehensive Word manual's package structure,
required content, page geometry, real numbering, and fixed-DXA table geometry.

Phase 4.2 brings the full suite to 89 passing tests. The two added tests verify
that NRC VAD v1's 132 source-supplied whitespace entries are active, that the
former inactive-entry caution is absent, and that both a synthetic phrase
fixture and the locally supplied `alarm clock` entry follow exact,
longest-first phrase matching with auditable component suppression.

Phase 5 brings the full suite to 100 passing tests. The added coverage verifies
schema-2-to-3 migration with a verified non-overwriting backup; named review
scenarios and immutable versions; append-only flag, exclude, map, revoke,
restore, and restored-snapshot revisions; occurrence/work/project/global
scope resolution; exact-target mapping after ordinary matching fails;
review-excluded aggregation; semantic-risk candidates; pinned immutable corpus
batches; baseline-versus-reviewed deltas; real-source end-to-end mapping;
separate emotion and sentiment presentation; universal part-of-speech counts
and lexical-token shares; workbook construct/POS/review sheets; title-case
interface navigation; and structural/content validation for both Word guides.
The final POS cases verify that the broad Noun category merges `NOUN`/`PROPN`,
the broad Verb category merges `VERB`/`AUX`, and the detailed view retains all
four source tags as separately countable evidence.

Poetic Fingerprint expansion Stage 0 brings the full suite to 115 passing
tests. Its 15 tests cover the common framework-independent module protocol,
immutable metrics/coverage/warnings/provenance/results, structural metric
identity, missing denominators, invalid counts and checksums, read-only resource
hashing, missing/malformed/unsupported resource states, configured-root path
containment, deterministic validation order, and refusal to publish unavailable
resources as completed provenance.

Both hand-calculated demonstrations and all 11 local diagnostics were rerun
after Stage 0. See
[`poetic-fingerprint-stage0-validation.md`](poetic-fingerprint-stage0-validation.md)
for results, limitations, and exact beginner steps.

Poetic Fingerprint expansion Stage 1 brings the full suite to 129 passing
tests. Its added coverage verifies exact source reconstruction from section,
stanza, and physical-line records; `CRLF`, indentation, blank separators,
model sentences/dependencies across poetic lines, em dashes, Unicode
normalization separation, apostrophes, contractions, hyphenated expressions,
content/function classifications, capitalization, one-word and
punctuation-free lines, archaic forms, repeated refrains, NER disabled by
default and explicitly enabled, missing small-model OOV coverage, empty and
deterministic documents, immutable module-input integration, invalid
configuration/coverage refusal, one preprocessing pass across multiple
lexicons, the audit JSON, and the visible Shared Processing Record.

The completion suite passed `129 passed` on 2026-07-23. Both hand-calculated
demonstrations, all 11 diagnostics, and the rendered Word-manual inspection are
recorded in
[`poetic-fingerprint-stage1-validation.md`](poetic-fingerprint-stage1-validation.md).

The full suite passes with:

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

The Phase 4 browser pass verified clean navigation between all three workspaces,
a five-source `blood` lookup with provenance and normalized spread, a complete
one-poem analysis with definitions/token-type/cumulative/contributor sections,
all three download controls, and the absence of the former inactive-Warriner-
phrase warning. A real two-work NRC VAD corpus pipeline generated an Excel
workbook; it was re-imported, key ranges inspected, and the collection-profile
sheet rendered for visual review using the spreadsheet validation tooling.

The Phase 4.1 browser pass used an isolated temporary database and verified the
top workspace tab bar, a complete five-source one-poem analysis, both VAD
views, definitions, stopword sensitivity, cumulative totals, midpoint-centered
contributors, the excluded-match evidence filter, a fresh `kiss` Lexicon
Explorer lookup, and exact-case project deletion with a visible success
confirmation. The temporary database was removed afterward.
