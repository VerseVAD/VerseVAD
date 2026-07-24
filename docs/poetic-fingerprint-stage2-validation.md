# Poetic Fingerprint Expansion Stage 2 Validation

Date: 2026-07-23

## What this stage validates

Stage 2 is an optional, local concreteness module. Its automated and synthetic
checks cover:

- read-only workbook loading, exact headers, hashes, row structure, numeric
  ranges, duplicates, and malformed-source refusal;
- exact surface priority over lemma fallback;
- exact two-word expressions within physical-line boundaries and auditable
  phrase-to-token rating assignment;
- conservative apostrophe/possessive fallback and explicit unmatched values;
- default proper-name exclusion and configurable inclusion;
- repetition, Unicode normalization, empty input, wholly unmatched input,
  sparse results, low coverage, invalid thresholds, and deterministic output;
- token/type coverage, descriptive statistics, structural/POS summaries, term
  rankings, warnings, and provenance; and
- standalone concreteness runs, mixed affective/concreteness runs, Streamlit
  rendering, six export files, and machine-readable round trips.

No private poem or licensed source row is embedded in the fixtures.

## Hand-calculated synthetic example

Run:

```powershell
.\.venv\Scripts\python.exe -m versevad.concreteness_validation
```

The generated temporary workbook rates `dark night` at 4.5, `stone` at 5.0,
and `idea` at 1.0. The invented text includes the exact phrase, exact forms,
the lemma-derived plural `stones`, and one unmatched token. The expected
token-weighted values are:

- 6 eligible lexical tokens;
- 5 rated lexical tokens;
- 83.3% token coverage;
- mean normative lexical concreteness 4.0 on the 1-5 source scale;
- one exact two-word expression occurrence;
- two exact-phrase token assignments, two exact-token matches, one lemma
  match, and one unmatched token; and
- no numeric rating on the unmatched token.

The command verifies those values and verifies that the temporary workbook's
checksum is unchanged.

## Installed-source contract

The optional local-source test validates the supplied workbook in place. The
expected result is:

- SHA-256
  `1673ead761e28833a40e82c0d20f10782955ced9366d600eafeefee0f2254545`;
- 39,954 usable rows;
- 37,058 single-word entries;
- 2,896 source-flagged two-word expressions;
- no normalized lookup collisions; and
- all ratings within the source 1-5 range.

The paper is separately retained at SHA-256
`7bafeef31b771965dbbbe2dea0227e210c8f4d054461343505f829ecfa036b63`.
Neither file is modified or transmitted.

## Beginner-friendly interface check

Use invented text:

1. Confirm both supplied files are directly inside `resources/` with the exact
   filenames recorded in the installation section below.
2. Double-click `start_versevad.bat`.
3. Open **One Poem**.
4. Enter the title `Stage 2 invented check`.
5. Paste:

   ```text
   A stone in the dark night
   carries an idea home.

   Stone, stone, unknownword.
   ```

6. Under **Choose Evidence**, enable **Normative lexical concreteness**. Keep
   the default thresholds and policies.
7. Keep an affective lexicon selected for a mixed run, or clear all affective
   lexicons to test a concreteness-only run.
8. Click **Analyze this text**.
9. Open **Concreteness Profile** and confirm that the 1-5 source scale,
   token/type coverage, thresholds, warnings, physical lines, stanzas, POS
   groups, most concrete/abstract terms, token audit, and provenance appear.
10. Confirm `unknownword` has a missing rating rather than zero or neutral.
11. Confirm repeated `stone` occurrences contribute repeatedly to the
    token-weighted statistics.
12. Download the full audit ZIP and confirm the six `concreteness_*` files are
    present.
13. Open `concreteness_token_audit.csv` and confirm exact, lemma, phrase,
    unmatched, and ineligible decisions remain explicit.
14. Return to the affective tabs and confirm their existing results still
    load when an affective lexicon was selected.

Expected interpretation: the result describes normative lexical concreteness
evidence among represented vocabulary. It does not say that the poem itself is
concrete or abstract and does not assess imagery quality.

## Completion checks

The completion run executes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.demo
.\.venv\Scripts\python.exe -m versevad.phase2_demo
.\.venv\Scripts\python.exe -m versevad.concreteness_validation
.\.venv\Scripts\versevad-diagnose.exe
.\.venv\Scripts\python.exe scripts\inspect_lexicons.py
uv lock --check --offline
```

Completion results on 2026-07-23:

- the complete automated suite passed: `143 passed in 24.61s`;
- the Phase 1, Phase 2, and Stage 2 hand-calculated demonstrations passed;
- all 11 local diagnostics passed;
- all five installed affective source files retained their expected hashes and
  entry counts under the read-only source inspection;
- `uv lock --check --offline` resolved all 81 packages successfully;
- the Stage 2 workbook retained SHA-256
  `1673EAD761E28833A40E82C0D20F10782955CED9366D600EAFEEFEE0F2254545`;
- the supplied paper retained SHA-256
  `7BAFEEF31B771965DBBBE2DEA0227E210C8F4D054461343505F829ECFA036B63`;
- all 28 pages of the rendered user manual and all 21 pages of the rendered
  Values and Terminology Guide were inspected with no clipped, overlapping, or
  broken content; and
- the manual builder's OOXML list ordering and numbered-list restart behavior
  were corrected and covered by regression tests.

## Installation and privacy

Use these exact paths:

```text
resources/
  brysbaert_warriner_kuperman_concreteness_DATA.xlsx
  brysbaert_warriner_kuperman_concreteness_PAPER.pdf
```

Do not rename, edit, or redistribute the supplied files. The module needs the
workbook; the paper remains beside it for local methodological reference. All
analysis is local, and exports contain the poem and result evidence but not the
full ratings source. Treat the ZIP as research data.

## Limitations

- The 1-5 values are decontextualized lexical norms, not contextual judgments.
- The default 2.0 and 4.0 bands are VerseVAD orientation aids, not source-paper
  categories.
- Phrase ratings are deliberately assigned to both covered token positions for
  token-weighted summaries and are explicitly grouped in the audit.
- Proper-noun exclusion depends on a model tag that can be uncertain in poetry.
- Lemmas, POS labels, line summaries, and stanza summaries require inspection
  when language is archaic, fragmented, dialectal, or unusually capitalized.
- Stage 2 is currently a one-poem in-memory module. Corpus persistence and
  schema-4 module-result storage remain later work.
