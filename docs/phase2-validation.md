# Phase 2 Validation Report

Date: 2026-07-22

## Outcome

All five supplied lexicons now have read-only adapters and work through one
auditable analysis interface. The Phase 2 demonstration reproduces invented
hand calculations, validates the five inspected source hashes, analyzes one
short invented text independently with each lexicon, and writes seven CSV
files plus one structured JSON result. No source lexicon is modified or added
to Git, and no consensus score is created.

## Implemented behavior

- NRC VAD v1 retains its original 0-1 values and uses identity normalization;
- NRC VAD v2.1 retains original -1-1 values and separately derives 0-1 values
  with `(original + 1) / 2`;
- NRC Emotion values remain binary, multi-label categorical associations;
- NRC Emotion Intensity values remain supplied word-emotion pairs on 0-1;
- longest-first, non-overlapping exact phrase matching for NRC VAD v2.1;
- phrase-preferred, unigram-only, and phrase-and-component exploratory modes;
- included, unmatched, ineligible, suppressed-component, and
  suppressed-overlap records;
- VAD, categorical, and intensity results with explicit counts and denominators;
- line and stanza distributions plus contributing terms for emotion results;
- independent cross-lexicon metrics with source family/version labels;
- atomic UTF-8 CSV files with hashes, versions, source-load timestamp, recipe,
  model, policy, and warnings.

## Hand-calculated checks

The phrase fixture is:

```text
Very dark night glows.
Bright night glows.
```

The longest candidate `very dark night` is selected; the overlapping
`dark night` candidate and the three component candidates remain visible but
suppressed under the default policy. All seven lexical tokens receive coverage.
The five included VAD observations have valence values `1, 7, 8, 4, 7`, so the
token-weighted source-scale mean is `27 / 5 = 5.4`.

For `Joy joy fear stone.`, the invented categorical fixture produces two
joy-associated occurrences. The joy rate is `2 / 4 = 0.5` per all lexical
tokens and `2 / 3` among tokens carrying at least one positive association.
The `stone` entry demonstrates that source-lexicon coverage is distinct from
positive emotion association.

For `Rage rage fear stone.`, the invented anger intensities are `0.8, 0.8,
0.2`. The token-weighted mean is `0.6`; the distinct-type mean is `(0.8 + 0.2)
/ 2 = 0.5`. The absent stone-anger pair remains missing rather than becoming
zero.

## Local five-lexicon result

The fixed invented demonstration text currently produces:

| Lexicon | Matched lexical tokens | Coverage |
|---|---:|---:|
| Warriner VAD | 9/14 | 64.3% |
| NRC VAD v1 | 9/14 | 64.3% |
| NRC VAD v2.1 | 12/14 | 85.7% |
| NRC Emotion v0.92 | 7/14 | 50.0% |
| NRC Emotion Intensity v1 | 6/14 | 42.9% |

NRC VAD v2.1 selects `a bit` and `dark night` as exact phrases in this test.
The percentages describe coverage under the active policy, not the emotion of
the text.

## Automated validation

The complete Phase 0-2 suite has 49 passing tests. Phase 2 specifically covers
all four new source adapters, hashes and counts, scaling, multi-label category
terms, missing intensity pairs, source-error refusal, all phrase policies,
longest-first overlap, poetic line boundaries, categorical denominators,
intensity prevalence and descriptive statistics, source-specific comparison,
UTF-8 export, and safe export replacement.

## How to test it

1. Open the `ANEW VAD Study` folder in File Explorer.
2. Double-click `test_phase2.bat`.
3. Wait several seconds while the private source files are read locally.
4. Look for these lines:

   ```text
   VerseVAD Phase 2 validation passed.
   All five private source files matched their inspected SHA-256 checksums.
   Independent results (no consensus score):
   ```

5. Confirm that five separate lexicon coverage lines appear.
6. Press any key after reading the result.
7. Open `phase2_demo_output`. It should contain:

   - `phase2_match_audit.csv`;
   - `phase2_coverage.csv`;
   - `phase2_vad_summary.csv`;
   - `phase2_emotion_associations.csv`;
   - `phase2_emotion_intensity.csv`;
   - `phase2_cross_lexicon_comparison.csv`;
   - `phase2_manifest.csv`;
   - `phase2_results.json`.

In `phase2_match_audit.csv`, filter `match_method` to `exact_phrase` and confirm
that `a bit` and `dark night` are included for `nrc_vad_v2_1`. In
`phase2_cross_lexicon_comparison.csv`, confirm that each row names one lexicon
and that there is no `consensus_score` column.

If the window reports a failure, photograph or copy all visible text. The test
does not alter source lexicons or literary texts.

To reverse the test, delete only `phase2_demo_output`; the runner recreates it.

## Known Phase 2 limitations

This section records the historical Phase 2 state. Later updates added the
graphical corpus workflow and activated Warriner and NRC VAD v1 whitespace
entries as exact phrase candidates; see `phase4-validation.md` for current
behavior.

- There is no graphical interface or ordinary user-text import yet.
- Phrase matching is exact, line-bounded, and punctuation-bounded; lemma-based
  phrase matching and cross-line phrases are not inferred.
- At the historical Phase 2 checkpoint, older Warriner and NRC VAD v1
  whitespace entries were inactive. Current VerseVAD activates both sets under
  the selected phrase policy.
- Reviewed mappings, compounds, exclusions, stopword sensitivity, negation
  flags, semantic-risk decisions, and alternative persistent scenarios remain
  later work.
- Structural aggregation beyond the exported line/stanza emotion distributions
  is not yet implemented.
- There is no project database, corpus workflow, graphical comparison view, or
  Excel export.
- spaCy may mis-tag poetic, historical, dialectal, or unusual syntax; surface,
  POS, lemma, and provenance remain auditable.
