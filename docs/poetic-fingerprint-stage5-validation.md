# Poetic Fingerprint Expansion Stage 5 Validation

Date: 2026-07-24

## What this stage validates

Stage 5 automated and synthetic checks cover:

- exact pinned hashes, read-only loading, source counts, CMUdict alternative
  suffixes, ARPAbet inventories, vowel stress, duplicate and malformed rows,
  comments, vowelless entries, and invalid-source refusal;
- exact observed-form matching, Unicode/apostrophe normalization, proper
  names, possessive non-substitution, unique pronunciation, prosodically
  agreeing alternatives, materially ambiguous alternatives, unmatched forms,
  and missing unresolved values;
- validated poem-specific overrides, required rationale, unknown-symbol
  refusal, stable configuration identity, and retained dictionary candidates;
- syllables per resolved word, complete-line totals, lexical-stress sequences,
  stress counts/density, token/type/line coverage, sparse and source warnings;
- repeated words, empty input, incomplete lines, deterministic output, the
  framework-independent module result, UI, and CSV/JSON/ZIP exports; and
- unchanged existing affective, concreteness, frequency, AoA, database,
  corpus, and review behavior.

All ordinary unit fixtures are invented. No literary corpus or complete
research resource is embedded in tracked tests.

## Hand-calculated synthetic example

Run:

```powershell
.\.venv\Scripts\python.exe -m versevad.pronunciation_validation
```

The temporary dictionary defines:

- `stone` with one one-syllable `1`-stress pronunciation;
- `wind` with two different phone strings that both have one syllable and
  stress `1`;
- `permit` with two two-syllable alternatives, stress `01` and `12`; and
- `rings` with one one-syllable `1`-stress pronunciation.

The invented text is:

```text
stone wind
permit rings
```

Before an override, the expected result is:

- 4 eligible lexical tokens;
- 3 resolved tokens and 75% coverage;
- `stone` = unique dictionary evidence;
- `wind` = prosodic consensus with both phone strings retained;
- `permit` = materially ambiguous with no resolved syllable or stress value;
- first line complete with 2 syllables and lexical stress `1 | 1`; and
- second line incomplete with missing total and stress sequence.

The command then applies:

```text
permit = P ER0 M IH1 T | noun reading in the invented validation line
```

The expected result becomes:

- 4 resolved tokens and 100% coverage;
- 2 complete lines;
- second line = 3 syllables and lexical stress `01 | 1`; and
- the override remains distinct from both retained dictionary candidates.

The command verifies every value and confirms that all three temporary source
hashes remain unchanged.

## Installed-source contract

Run:

```powershell
.\.venv\Scripts\python.exe -c "from versevad.prosody import PronunciationModule; print(PronunciationModule('resources').validate_resources())"
```

The installed source must match official repository commit
`74790861f652b15e4ac49015a90074ad62a27690` and these contract totals:

- 135,166 dictionary rows;
- 126,052 unique normalized terms;
- 8,447 terms with more than one source pronunciation;
- maximum 4 source pronunciations for one term;
- 39 phone inventory rows;
- 84 symbol rows;
- 8 vowelless source pronunciations; and
- 2 repeated phone sequences retained as alternative source rows.

## Beginner-friendly interface check

1. Double-click `start_versevad.bat`.
2. Open **One Poem**.
3. Enter a title and paste:

   ```text
   The permit rings.
   Stone.
   ```

4. Clear the affective lexicon selection if you want a pronunciation-only run.
5. Select **Pronunciation & prosody foundation (CMUdict)**.
6. Open **Advanced methodology settings**.
7. Enter:

   ```text
   the = DH AH0 | unstressed article in this reading
   permit = P ER0 M IH1 T | noun reading
   ```

8. Click **Analyze this text**.
9. Open **Pronunciation & Prosody**.
10. Confirm 100% resolved coverage, complete line totals, candidate evidence,
    stress digits, and the North American/source warning.
11. Remove both overrides and analyze again. Confirm `the` and `permit` remain
    visibly ambiguous rather than being assigned a silent candidate, and that
    their line total/stress sequence remains missing.
12. Download the full audit ZIP and open all five `pronunciation_*` files.

## Full local checks

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.phase2_demo
.\.venv\Scripts\python.exe -m versevad.concreteness_validation
.\.venv\Scripts\python.exe -m versevad.frequency_validation
.\.venv\Scripts\python.exe -m versevad.aoa_validation
.\.venv\Scripts\python.exe -m versevad.pronunciation_validation
.\.venv\Scripts\python.exe -m versevad.diagnostics
.\.tools\uv\uv.exe --offline --cache-dir .uv-cache lock --check
```

Rebuild and visually inspect both Word guides with the document workflow
before closing the Stage 4 render carryover and Stage 5.

## Completion results

The final completion pass on 2026-07-24 produced:

- `185 passed` in the complete automated suite;
- passing Phase 1, Phase 2, Concreteness, SUBTLEX-US Frequency, Kuperman AoA,
  and Stage 5 pronunciation synthetic demonstrations;
- all 11 local diagnostics passing;
- all three installed CMUdict resources available with the expected hashes;
- the offline lock-file check passing with 86 resolved packages;
- `git diff --check` passing; and
- the source files and locally installed research resources remaining
  unchanged and excluded from source control.

Both Word guides were rebuilt at version `0.11.0.dev0`. Their structural and
content tests passed. Installed Microsoft Word exported the read-only DOCX
files to PDF for visual QA; all 37 User Manual pages and all 26 Values and
Terminology Guide pages were rasterized and inspected. One literal Markdown
fence was found around the pronunciation-override example, so the shared
builder gained fenced-code-block support, both guides were regenerated, and
all pages were rechecked with no clipped, overlapping, truncated, or broken
content. This review also closes the deferred Stage 4 Word-render carryover.
