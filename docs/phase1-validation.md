# Phase 1 Validation Report

Date: 2026-07-22

## Outcome

The minimum VAD engine is implemented and passes its hand-calculated example,
automated tests, and local Warriner source-file contract. No source lexicon was
modified or added to Git.

## Implemented behavior

- immutable original-text checksum and text-version identity;
- token positions, character offsets, line and stanza numbers, sentence
  positions, surface forms, normalized forms, POS, lemmas, morphology, flags,
  context, and preprocessing warnings;
- exact normalized surface-form matching before any fallback;
- conservative English possessive normalization;
- POS-sensitive lemma fallback using `en_core_web_sm` 3.8.0;
- explicit unmatched and ineligible token records;
- token and lexical-token coverage, surface-type coverage, and coverage by
  match method;
- token- and type-weighted VAD descriptive statistics on both the original
  source scale and a separately retained normalized 0–1 scale;
- matched counts, mean, median, population standard deviation, minimum,
  inclusive quartiles, and maximum;
- sparse and no-match warnings;
- UTF-8 CSV exports for token audit, coverage, VAD summary, and reproducibility
  metadata;
- source hashes, adapter/model/recipe/scenario versions, and match provenance.

## Hand-calculated example

The invented example has nine lexical token occurrences. Seven match: five
exactly and two by lemma fallback. The direct `broken` entry takes priority over
the lemma `break`.

Expected source-scale means:

| Weighting | Valence | Arousal | Dominance |
|---|---:|---:|---:|
| token | 31/7 = 4.428571… | 40/7 = 5.714286… | 36/7 = 5.142857… |
| type | 4.0 | 6.0 | 4.8 |

Lexical-token coverage is 7/9 (approximately 77.78%). Surface-type coverage is
5/7 (approximately 71.43%). The complete worksheet is in
`tests/fixtures/phase1_expected.md`.

## Warriner adapter result

The adapter reads all 13,915 source rows, preserves original 1–9 values, and
creates separate derived 0–1 values using `(original - 1) / 8`. It verifies the
known source checksum, required columns, numeric parsing, range, blank terms,
duplicate exact keys, and phrase-like entries.

Ten differently rated capitalization pairs collide under the default
case-insensitive key. Both source entries are retained. Exact source
capitalization may resolve a pair; an all-uppercase or otherwise ambiguous
form is left unmatched with an audit explanation. No average or arbitrary
first entry is substituted.

## Automated validation

Thirty-two tests currently cover:

- source-file inspection and case-collision reporting;
- Unicode and apostrophe normalization;
- line and stanza preservation;
- pinned spaCy POS-sensitive lemmas;
- the same surface form used with different parts of speech and lemmas;
- exact-first, possessive, and lemma matching;
- repeated words and token/type weighting;
- empty, no-match, one-match, and sparse cases;
- descriptive statistics and missing values;
- adapter columns, encoding, malformed values, duplicates, range, hashes, and
  source integration;
- ambiguous case-collision behavior;
- CSV completeness and traceability;
- the beginner-facing demonstration command.

## How to test it

1. Open the `ANEW VAD Study` folder in File Explorer.
2. Double-click `test_phase1.bat`.
3. A black console window will appear. Wait for the calculations to finish.
4. Success looks like this:

   ```text
   VerseVAD Phase 1 validation passed.
   Matched lexical tokens: 7/9 (77.8% coverage).
   Mean normative valence of matched tokens: 4.428571 on the 1-9 scale.
   ```

5. Press any key after reading the message.
6. Open the new `phase1_demo_output` folder. It should contain
   `token_audit.csv`, `coverage.csv`, `vad_summary.csv`, and
   `analysis_manifest.csv`.

If the window reports a failure, photograph or copy all visible text. No
source lexicon or literary text is changed by this test.

To reverse the test, delete only the `phase1_demo_output` folder. To remove the
entire project-local development runtime later, close VerseVAD and delete
`.venv`, `.runtime`, and `.tools`; this does not uninstall or change a
computer-wide Python installation.

## Known Phase 1 limitations

- Only the Warriner source adapter is implemented.
- Phrase matching is not implemented; whitespace-containing source entries are
  retained but cannot contribute yet.
- There is no project database or graphical interface.
- Reviewed mappings, exclusions, compounds, negation flags, semantic-risk
  decisions, and alternative scenarios are not implemented.
- Confidence intervals are not reported yet. Phase 1 reports transparent
  descriptive statistics only.
- spaCy can mis-tag poetic, archaic, dialectal, or syntactically unusual text;
  its POS and lemma remain visible in the token audit.
- The CSV demonstration uses invented text and ratings, not the supplied
  Warriner values.
