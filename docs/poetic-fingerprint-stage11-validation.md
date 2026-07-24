# Poetic Fingerprint Stage 11 Validation

Validation date: 2026-07-24.

## Automated examples

The Stage 11 synthetic corpus contains two tiny works:

- `red blue red`
- `green blue`

It runs an optional-module-only lexical-style batch and verifies:

- schema 4 initialization;
- exact batch module selection and configuration persistence;
- two immutable work-level module results;
- document and line metrics;
- coverage and warnings;
- checksummed CSV/JSON artifacts and deterministic ZIP reconstruction;
- five pooled lexical tokens and three normalized surface types;
- pooled TTR `3 / 5 = 0.6`;
- pooled MATTR with a window of 2 equal to `1.0`; and
- pooled HD-D with a sample of 2 equal to `0.9`.

A second hand-calculated aggregation fixture verifies that work-level
concreteness means `4.0` over 9 observations and `2.0` over 1 observation
produce:

- equal-work mean `(4 + 2) / 2 = 3.0`; and
- observation-weighted mean `(4*9 + 2*1) / 10 = 3.8`.

The same fixture verifies that work-level MATTR values receive an equal-work
descriptive mean but no naive observation-weighted mean.

Synthetic Explorer fixtures verify concreteness, SUBTLEX-US Zipf and auxiliary
fields, AoA response evidence, CMUdict phones/syllables/stress, explicit
unmatched status, and explicit unavailable-resource status.

## Beginner test steps

1. Start VerseVAD and open **Projects & Corpus**.
2. Create or select a project containing at least two short `.txt` works.
3. Under **Analyze & Compare**, leave affective lexicons selected and add one
   or more **Additional analysis modules**.
4. For Frequency or AoA, optionally enable the non-default content-word-only
   setting under **Advanced batch methodology**.
5. Run the batch. Confirm **Additional Module Results** shows work metrics,
   compatible collection summaries, coverage, warnings, and an audit ZIP.
6. Open **Excel Export**. Confirm the workbook contains the seven `Module ...`
   sheets and that configurations and denominators are visible.
7. Open **Lexicon Explorer** and search a familiar word such as `stone`.
   Confirm each installed supplementary resource reports its own status and
   fields, and expand **Source provenance**.
8. Search an invented form. Confirm available resources say **Unmatched** and
   that no zero or neutral rating appears.

## Interpretive limits

- Collection summaries are descriptive, not inferential tests.
- Work boundaries remain visible.
- Missing values remain missing.
- Meter and rhyme evidence remain candidates and dictionary/text-based
  observations.
- Pooled lexical-diversity values depend on work order and matching
  parameters; their aggregation method is recorded.
- Explorer values are decontextualized source evidence, not contextual
  interpretation.

## Completion commands

The Stage 11 completion pass produced:

- `230 passed` in the complete pytest suite;
- all nine direct synthetic demonstrations passed;
- a temporary real-resource optional-module-only corpus batch completed all
  seven modules and persisted 7 module results, 130 scoped metrics, 13 coverage
  rows, and 21 explicit warnings;
- all 11 local diagnostics passed;
- all five affective source files passed read-only checksum inspection;
- concreteness, SUBTLEX-US, AoA, and all three CMUdict resource contracts were
  available with recorded SHA-256 values;
- the 86-package offline lock check passed;
- `git diff --check` passed;
- both rebuilt Word guides passed structural tests and accessibility audit
  with no high-severity findings; and
- the required canonical page-image renderer was attempted for both guides but
  could not start because LibreOffice/`soffice` is not installed. The documents
  therefore receive structural rather than rendered visual QA, as allowed by
  the document workflow's explicit fallback.
