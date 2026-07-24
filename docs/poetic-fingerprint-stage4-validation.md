# Poetic Fingerprint Expansion Stage 4 Validation

Date: 2026-07-23

## What this stage validates

Stage 4 is an optional, local Kuperman retrospective Age of Acquisition module.
Automated and synthetic checks cover:

- read-only workbook loading, pinned hash, sheet/header contract, expected
  counts, duplicate keys, response relationships, source `NA` and `#N/A`
  values, and malformed-source refusal;
- exact observed-form priority over lemma fallback, configurable lemma
  disabling, conservative apostrophe/possessive fallbacks, source-unrated
  evidence, and missing unmatched values;
- default proper-name exclusion and configurable inclusion;
- the non-default contextual content-word scope using exactly `NOUN`, `VERB`,
  `ADJ`, and `ADV`, even though the source paper describes a content-word
  sampling rule;
- Unicode normalization, repetition, empty input, wholly unmatched input, low
  coverage, invalid thresholds, sparse relationships, and deterministic output;
- token/type coverage, token-weighted descriptive statistics, bands,
  structural/POS summaries, term rankings, source response evidence, warnings,
  and provenance;
- optional type-level Spearman relationships with enabled SUBTLEX-US frequency
  and concreteness results; and
- AoA-only and mixed runs, Streamlit presentation, eight export files, and
  JSON/CSV round trips.

All ordinary unit fixtures are invented. No private poem or licensed source
row is embedded in the public test fixtures.

## Hand-calculated synthetic example

Run:

```powershell
.\.venv\Scripts\python.exe -m versevad.aoa_validation
```

The temporary source gives `early = 3`, `middle = 8`, and `later = 14` years.
The invented text is:

```text
early early
middle middles
later quorvax
```

`middles` uses an explicitly audited lemma fallback to `middle`; `quorvax`
remains unmatched. The expected result is:

- 6 eligible lexical tokens;
- 5 matched lexical tokens;
- 83.3% token coverage;
- mean normative AoA 7.2 years;
- median normative AoA 8.0 years;
- 2 early-band, 2 middle-band, and 1 later-band occurrences;
- 4 exact, 1 lemma, and 1 unmatched audit rows;
- 2 represented token occurrences whose source mean has fewer than five
  numeric responses;
- no numeric value for the unmatched token; and
- a separate restricted-scope check with only model-tagged `NOUN`, `VERB`,
  `ADJ`, and `ADV` eligible.

The command checks all values and confirms that the temporary workbook hash is
unchanged.

## Installed-source contract

The analysis-time source is:

`resources/kuperman_2013_erratum_ESM1_official.xlsx`

Its SHA-256 is:

`3f69a1332359de1cd4a7ccd3c4c3c2e39b388eeb171d6e90544709c3dc1a8a6e`

The contract check confirms:

- exact `Sheet1` and seven-column header;
- 31,124 nonblank unique normalized word rows;
- 31,105 numeric mean ratings;
- 19 rows with unavailable numeric means;
- source mean ages from 1.58 through 25.0 years;
- coherent `OccurTotal`, `OccurNum`, and `Dunno` relationships;
- no blank source terms or duplicate normalized keys; and
- common polyfunctional spellings such as `the`, `and`, `he`, `of`, and `to`
  have numeric source ratings.

The locally retained paper has SHA-256
`fa72b2dd7980707de710b4dcb346d0368d5e2c21d657824a935ea4b8b8b80e1a`.
All 13 pages were rendered and inspected. The title, authors, DOI, method,
rating instructions, response filtering, 25-year outlier rule, response-count
caution, availability description, figures, tables, and references are
legible with no broken or missing pages.

## Beginner-friendly interface check

1. Confirm both exact Stage 4 filenames in
   `resources/README.md` exist. Do not rename or edit them.
2. Double-click `start_versevad.bat`.
3. Open **One Poem**.
4. Enter the title `Stage 4 invented check`.
5. Paste:

   ```text
   The stone and slowly bending grass
   remember a distant instrument.

   She walks under quorvax skies.
   ```

6. Clear the affective lexicon list if you want an AoA-only run.
7. Enable **Age of Acquisition profile (Kuperman et al. ratings)**.
8. Keep **AoA content words only** off and click **Analyze this text**.
9. Open **Age of Acquisition**. Confirm mean, median, coverage, configured
   bands, response evidence, line/stanza/POS summaries, term rankings, audit,
   non-diagnostic warning, and provenance are visible.
10. Confirm `quorvax` is unmatched and its numeric value is blank, not zero.
11. In the audit, confirm exact form wins before lemma; lemma use remains
    separately labeled.
12. Note that source-rated function spellings such as `the`, `and`, `she`, and
    `under` can contribute in the default all-lexical-token scope.
13. Open **Advanced methodology settings**, enable **AoA content words only**,
    and analyze again.
14. Confirm only model-tagged `NOUN`, `VERB`, `ADJ`, and `ADV` occurrences are
    eligible. `DET`, `ADP`, `CCONJ`, `SCONJ`, `PRON`, `AUX`, punctuation, and
    default-excluded `PROPN` rows must be ineligible.
15. Inspect the model tags rather than assuming how every poetic form was
    classified.
16. Optionally enable Frequency and Concreteness too. Confirm the AoA tab shows
    descriptive type-level relationships and paired-type counts.
17. Download the full audit ZIP and confirm all eight `aoa_*` files are present.
18. Open `aoa_token_audit.csv` and verify eligibility, POS, exact/lemma/fallback
    method, source row, source mean, source SD, response counts, source-unrated
    evidence, unmatched values, and reason.

Expected interpretation: the result describes matched retrospective normative
lexical AoA evidence. It does not declare the text appropriate for a grade,
difficult, familiar, intellectually simple or complex, or diagnostic of
cognitive impairment.

## Completion checks

The final completion run executes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.demo
.\.venv\Scripts\python.exe -m versevad.phase2_demo
.\.venv\Scripts\python.exe -m versevad.concreteness_validation
.\.venv\Scripts\python.exe -m versevad.frequency_validation
.\.venv\Scripts\python.exe -m versevad.aoa_validation
.\.venv\Scripts\versevad-diagnose.exe
.\.venv\Scripts\python.exe scripts\inspect_lexicons.py
uv lock --check --offline
```

The complete automated suite passed `172 passed` on 2026-07-23. The AoA
synthetic validation also passed with the expected 5/6 coverage, 7.2-year
mean, and 8.0-year median. Both earlier demonstrations, the Concreteness and
Frequency validations, and the AoA validation passed. Local diagnostics
reported `11/11` checks passed, the five affective source hashes and structures
passed the read-only inspection, and `uv lock --check --offline` resolved all
81 locked packages without changes.

Both Word guides were rebuilt at software version `0.10.0.dev0`. Their
OOXML/content tests passed `2 passed`, including required AoA content, package
structure, US Letter geometry, one-inch margins, fixed table widths, cell/grid
alignment, and real bullet/decimal numbering. The resulting files are 70,669
bytes for the User Manual and 61,498 bytes for the Values and Terminology
Guide.

Final visual inspection of the Word guides remains the one incomplete
completion check. Microsoft Word opened each rebuilt guide read-only, but both
`ExportAsFixedFormat` and PDF `SaveAs2` stalled before producing a file.
Only the hidden Word processes started for this QA attempt were closed, and
all temporary render files were removed. No guide or source resource was
modified by the failed render. Open both guides in Word and visually inspect
every page before changing the two `[~]` render items in `PLANS.md` to `[x]`.

## Privacy, installation, and current corpus boundary

Ordinary analysis remains local. The source workbook, paper, poems, projects,
and exports are not uploaded. The source workbook and paper are ignored by
source control, and the full ratings list is not copied into result exports.

Stage 4 is currently a one-poem module. Concreteness, Frequency, and AoA are
not yet batched or persisted in **Projects & Corpus**. The stable metric IDs,
configuration, coverage, and provenance are longitudinal-ready inputs for the
planned schema-4 corpus module store; career-period aggregation is not claimed
as implemented.

## Limitations

- Kuperman values are retrospective adult estimates rather than directly
  observed acquisition dates.
- Source list sampling and a poem occurrence's contextual model tag are
  separate evidence.
- Proper-name, POS, and lemma decisions can be uncertain in poetic language.
- Source `Rating.SD` and response counts describe source evidence; they are not
  the poem's distribution.
- Configurable early/later bands are not source-paper categories.
- Type-level relationships require at least three paired types, exclude
  multiword concreteness assignments, and do not establish causation.
- The module cannot support cognitive, medical, or diagnostic conclusions.
