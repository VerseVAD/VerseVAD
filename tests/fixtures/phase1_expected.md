# Phase 1 hand-calculated expectations

The fixture and every rating below are invented for VerseVAD validation.

| Entry | Valence | Arousal | Dominance |
|---|---:|---:|---:|
| bright | 8 | 6 | 7 |
| stone | 3 | 4 | 5 |
| mountain | 6 | 5 | 7 |
| cry | 2 | 7 | 3 |
| broken | 1 | 8 | 2 |
| break | 4 | 6 | 5 |

The nine lexical occurrences are `Bright`, `stone`, `bright`, `stone`,
`Mountains`, `cried`, `Broken`, `arms`, and `rest`.

- Seven occurrences match; `arms` and `rest` do not.
- Five matches are exact.
- `Mountains` -> `mountain` and `cried` -> `cry` are lemma fallbacks.
- `Broken` matches the direct `broken` entry, not its lemma `break`.
- Lexical-token coverage is 7/9, or approximately 77.78%.
- Surface-type coverage is 5/7, or approximately 71.43%.

Token-weighted source-scale means:

- valence: `(8 + 3 + 8 + 3 + 6 + 2 + 1) / 7 = 31/7`
- arousal: `(6 + 4 + 6 + 4 + 5 + 7 + 8) / 7 = 40/7`
- dominance: `(7 + 5 + 7 + 5 + 7 + 3 + 2) / 7 = 36/7`

Type-weighted source-scale means count the five unique matched entries once:

- valence: `(8 + 3 + 6 + 2 + 1) / 5 = 4.0`
- arousal: `(6 + 4 + 5 + 7 + 8) / 5 = 6.0`
- dominance: `(7 + 5 + 7 + 3 + 2) / 5 = 4.8`
