# Poetic Fingerprint Expansion Stage 3 Validation

Date: 2026-07-23

## What this stage validates

Stage 3 is an optional, local SUBTLEX-US Zipf-frequency module. Automated and
synthetic checks cover:

- read-only workbook loading, pinned hash, worksheet and column contracts,
  expected counts, duplicate keys, numeric relationships, source `#N/A`
  fields, and malformed-source refusal;
- exact observed-form priority over lemma fallback, configurable lemma
  disabling, conservative apostrophe/possessive fallbacks, and missing
  unmatched values;
- default proper-name exclusion and configurable inclusion;
- the non-default content-word scope using exactly `NOUN`, `VERB`, `ADJ`, and
  `ADV`, with auxiliaries and function-word tags excluded;
- Unicode normalization, repetition, all-common vocabulary, empty input,
  wholly unmatched input, low coverage, invalid thresholds, and deterministic
  output;
- token/type coverage, token-weighted median and other descriptive statistics,
  bands, structural/POS summaries, term rankings, warnings, and provenance;
  and
- frequency-only and mixed runs, Streamlit presentation, seven export files,
  and JSON/CSV round trips.

No private poem or licensed source row is embedded in the test fixtures.

## Hand-calculated synthetic example

Run:

```powershell
.\.venv\Scripts\python.exe -m versevad.frequency_validation
```

The generated temporary workbook gives the invented forms these Zipf values:
`rareword = 2`, `stone = 4`, `ordinary = 5`, and `common = 6`. The invented
text contains exact forms, a lemma-derived plural, and one unmatched token.
The expected result is:

- 6 eligible lexical tokens;
- 5 matched lexical tokens;
- 83.3% token coverage;
- token-weighted median Zipf 4.0;
- token-weighted mean Zipf 3.4;
- exact, lemma, and unmatched audit rows;
- no numeric value for the unmatched token; and
- a restricted-scope check in which only model-tagged `NOUN`, `VERB`, `ADJ`,
  and `ADV` tokens remain eligible.

The command verifies those values and confirms that the temporary workbook's
checksum is unchanged.

## Installed-source contract

The official workbook was downloaded from the Ghent University SUBTLEX-US
resource page and inspected without modification:

- workbook:
  `resources/subtlex-us/SUBTLEX-US frequency list with PoS and Zipf information.xlsx`;
- workbook SHA-256:
  `3a8cb93a4e28988c2ce722a63f6b8d394acdc42ebe2ab6e1f0e484ee0d4167a7`;
- preserved archive: `resources/subtlexus1.zip`;
- archive SHA-256:
  `458128f90a28c4f396cb2a5b23ac93c56f745ee8cfca9be2afedad4091d15090`;
- worksheet `out1g`;
- 74,286 usable rows and normalized lookup keys;
- 74,286 populated Zipf values;
- observed Zipf range 1.5928641378084412 to 7.621173840455432; and
- no blank or duplicate normalized word forms.

The original Brysbaert and New (2009) methodological paper was inspected from
the official Ghent University repository. It documents a roughly 51-million
word American subtitle corpus drawn from 8,388 films, word-form frequency,
contextual diversity, name-frequency concerns, and register dependence. The
paper is cited by DOI in the module and documentation; no incomplete local
download is retained.

## Beginner-friendly interface check

Use invented text:

1. Confirm the exact workbook path above exists. Do not rename or edit it.
2. Double-click `start_versevad.bat`.
3. Open **One Poem**.
4. Enter the title `Stage 3 invented check`.
5. Paste:

   ```text
   The stone moves slowly under Alice.
   A bright bird can sing, and the sky opens.

   Stone, stone, quorvax.
   ```

6. Under **Choose Evidence**, enable **Frequency & rarity profile
   (SUBTLEX-US Zipf)**. It may run alone or with other evidence sources.
7. Keep **Content words only** off for the first run and click **Analyze this
   text**.
8. Open **Frequency & Rarity**. Confirm the median is visually primary and the
   tab also shows mean, IQR, coverage, bands, warnings, line/stanza/POS
   summaries, lowest/highest terms, rare tail, token audit, and provenance.
9. Confirm `quorvax` is unmatched with a blank Zipf value rather than zero.
10. Confirm the exact observed form is preferred whenever both it and a lemma
    could match. Check the **Match method** and **Reason** audit fields.
11. Open **Advanced methodology settings**, enable **Content words only**, and
    analyze again.
12. Confirm only tokens model-tagged `NOUN`, `VERB`, `ADJ`, or `ADV` are
    eligible for frequency. `DET`, `ADP`, `CCONJ`, `SCONJ`, `PRON`, `AUX`,
    punctuation, and default-excluded `PROPN` rows must be ineligible. Because
    POS is model-generated, inspect the assigned tags rather than assuming how
    every poetic form was classified.
13. Confirm the page displays the restricted scope and its changed
    denominator. Turn the setting off and reanalyze to restore the default.
14. Download the full audit ZIP and confirm all seven `frequency_*` files are
    present.
15. Open `frequency_token_audit.csv` and confirm eligibility, POS, exact,
    lemma, fallback, unmatched, source row, source counts, and missing values
    remain explicit.

Expected interpretation: the result describes corpus-relative lexical
frequency evidence for represented vocabulary in SUBTLEX-US. It does not
declare the poem easy, difficult, sophisticated, accessible, or high quality.

## Completion checks

The completion run executes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.demo
.\.venv\Scripts\python.exe -m versevad.phase2_demo
.\.venv\Scripts\python.exe -m versevad.concreteness_validation
.\.venv\Scripts\python.exe -m versevad.frequency_validation
.\.venv\Scripts\versevad-diagnose.exe
.\.venv\Scripts\python.exe scripts\inspect_lexicons.py
uv lock --check --offline
```

The 2026-07-23 completion run passed:

- `159 passed in 34.40s`;
- the Phase 1 and Phase 2 demonstrations;
- the Stage 2 concreteness validation;
- the Stage 3 frequency validation, including the non-default
  `NOUN`/`VERB`/`ADJ`/`ADV` scope;
- all 11 local diagnostics;
- the five-source read-only lexicon inspection;
- `uv lock --check --offline`;
- confirmation that the database schema remains version 3; and
- a dependency-file search confirming that neither `pyproject.toml` nor
  `uv.lock` contains `wordfreq`.

The official SUBTLEX-US archive and workbook retained SHA-256 values
`458128f90a28c4f396cb2a5b23ac93c56f745ee8cfca9be2afedad4091d15090`
and
`3a8cb93a4e28988c2ce722a63f6b8d394acdc42ebe2ab6e1f0e484ee0d4167a7`.
The previously installed concreteness workbook and paper likewise retained
their recorded SHA-256 values
`1673ead761e28833a40e82c0d20f10782955ced9366d600eafeefee0f2254545`
and
`7bafeef31b771965dbbbe2dea0227e210c8f4d054461343505f829ecfa036b63`.

The rebuilt 30-page User Manual and 23-page Values and Terminology Guide were
rendered through Microsoft Word and inspected page by page. No clipped,
overlapping, broken, or missing content was found.

## Installation and privacy

Use this exact analysis-time path:

```text
resources/
  subtlex-us/
    SUBTLEX-US frequency list with PoS and Zipf information.xlsx
```

The optional preserved archive may remain at
`resources/subtlexus1.zip`. Do not rename, edit, redistribute, or upload these
files. The module reads the workbook locally. Exports contain the poem and its
result evidence but not the full frequency source; treat the ZIP as research
data.

## Limitations

- SUBTLEX-US describes an American subtitle corpus, not poetry or a universal
  English language.
- Zipf values are logarithmic and corpus-relative. The default bands are
  VerseVAD orientation aids.
- Word-form frequency takes priority. Lemma fallback is separately labeled and
  can be disabled.
- Proper-name exclusion and content-word scope depend on model tags that can
  be uncertain in poetry.
- The content-word option is off by default and excludes `AUX`, even though
  the broad Language Profile groups `VERB` and `AUX` under **Verb**.
- Unmatched forms remain missing; no `wordfreq` or alternate source is
  substituted.
- Stage 3 is currently a one-poem in-memory module. Corpus persistence and
  schema-4 module-result storage remain later work.
