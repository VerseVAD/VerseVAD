# Poetic Fingerprint Stage 10 Validation

## Hand-calculated example

The local validation command uses:

```text
red blue red
green blue

yellow red
```

There are 7 lexical tokens and 4 normalized observed surface types:

```text
TTR = 4 / 7
```

With a MATTR window of 3, the five overlapping-window TTRs are:

```text
2/3, 1, 1, 1, 1
MATTR = 14/15 = approximately 0.933333
```

For HD-D with sample size 3, the type frequencies are `red=3`, `blue=2`,
`green=1`, and `yellow=1`. The expected distinct-type proportion is:

```text
HD-D = 86/105 = approximately 0.819048
```

Alphabetic-character lengths are `3, 4, 3, 5, 4, 6, 3`, so the mean and median
are both 4. The physical-line word counts are `3, 2, 0, 2`; the stanza word
counts are `5, 2`.

An independent MTLD fixture, `a b a b a b a b`, crosses the default 0.72
threshold after each three-token `a b a` or `b a b` segment in both
directions, giving MTLD 4.

Run:

```powershell
.venv\Scripts\python.exe -m versevad.lexical_style_validation
```

Success ends with:

```text
VerseVAD lexical style validation passed.
```

## Automated coverage

Tests cover:

- hand-calculated MATTR, HD-D, and MTLD;
- unavailable short-window/sample and all-unique MTLD values remaining
  missing;
- invalid configuration rejection;
- normalized surface forms without lemma substitution;
- Unicode alphabetic-character lengths;
- punctuation and numeric-token exclusion;
- blank physical lines retained with zero word count;
- line and stanza counts summing to the document count;
- resource-free module-contract behavior;
- all six CSV/JSON exports;
- application summary and ZIP integration; and
- the live Streamlit checkbox, tab, metrics, and structural tables.

## Final verification

Completed on 2026-07-24:

- full automated suite: `225 passed`;
- all nine direct synthetic demonstrations from Phase 1 through narrowed
  Stage 10: passed;
- all 11 local diagnostics: passed;
- the five supplied affective lexicons: read-only inspection passed;
- installed concreteness, SUBTLEX-US, Kuperman AoA, and three-file CMUdict
  resource contracts: available with recorded SHA-256 checksums;
- dependency lock: 86 packages resolved in offline check mode;
- `git diff --check`: passed;
- both rebuilt Word guides: structural/content tests passed, zero
  high-severity accessibility findings, and successful read-only Microsoft
  Word pagination at 44 and 30 pages.

The required page-image renderer was attempted for both Word guides but could
not run because LibreOffice is not installed. Microsoft Word opened and
repaginated both files successfully; PDF export was not retried because the
same local exporter stalled in the preceding completed stage.

## Beginner-friendly interface check

1. Double-click `start_versevad.bat`.
2. Open **One Poem**.
3. Enter a title and paste the synthetic poem above.
4. Clear the affective-lexicon selection if you want to test only this module.
5. Enable **Lexical diversity, word length & structural word counts**.
6. Expand **Advanced methodology settings** only if you want to change the
   default MATTR window, HD-D sample, MTLD threshold, or short-text caution.
7. Click **Analyze this text**.
8. Open **Lexical Style**.
9. Confirm token/type totals, word-length data, line counts `3, 2, 0, 2`, and
   stanza counts `5, 2`. With the defaults, MATTR and HD-D remain missing
   because the synthetic text is shorter than 50 and 42 tokens. Set both
   parameters to 3 to reproduce the hand calculations above.
10. Download the full audit bundle and confirm the six `lexical_style_*` files.

## Limitations verified

- No value is fabricated when a configured denominator is too long.
- Blank lines are structural zero-count observations, not missing data.
- Missing character lengths remain missing rather than zero.
- The module performs no resource lookup and modifies no source lexicon.
- The broader skipped visible-structure and syntax/lineation analyses are not
  present.
- Projects & Corpus persistence and aggregation remain later work.
