# Phase 3 Validation Report

Date: 2026-07-22

## Outcome

Phase 3 is complete. VerseVAD now provides a local graphical, temporary
one-poem workspace. Paste input and UTF-8 `.txt` import both preserve the
original string separately from processing. Any selection of the five supplied
sources can be analyzed through the tested Phase 2 engine. The result provides
a readable overview and profiles before exposing match-level and CSV audit
detail.

The full automated suite reports `62 passed`. The in-app diagnostic reports
`11/11 checks passed`, including the package, pinned linguistic model,
hand-calculated engine checks, and all five private source hashes. A live local
browser pass completed paste, five-source analysis, normalized VAD review, and
the self-test without an application error.

## What to test as a beginner

### 1. Start and check the installation

1. If this is the first graphical run, double-click `setup_windows.bat` and let
   it finish.
2. Double-click `start_versevad.bat`.
3. Keep the launcher window open and confirm that a browser opens VerseVAD.
4. In the left sidebar, click **Run self-test**.

Expected: the sidebar says `11/11 checks passed`. The page says that analysis
stays on this computer and that the workspace is temporary.

### 2. Test pasted-text analysis

Enter `Phase 3 test poem` as the title and paste these three invented lines:

```text
Bright morning opens the quiet door.
Dark rain remembers fear and joy.
Love returns, calm and alive.
```

Leave all five lexicons selected and click **Analyze this text**.

Expected:

- a green completion message appears;
- Overview reports 17 lexical tokens, five lexicons, and three preserved lines;
- the coverage table has one source-specific row for each selected lexicon;
- warnings, if present, are plain-language cautions rather than failures.

### 3. Check the scale comparison

1. Open **VAD profile**.
2. Confirm that Warriner, NRC VAD v1, and NRC VAD v2.1 have separate rows.
3. Confirm that every displayed comparison mean lies between 0 and 1.
4. Open **Original scales, formulas, and token/type comparison**.

Expected formulas:

- Warriner 1-9 uses `(x - 1) / 8`;
- NRC VAD v1 0-1 uses identity;
- NRC VAD v2.1 -1 to 1 uses `(x + 1) / 2`.

The original-scale table remains visible under the derived comparison. There is
no consensus score. This normalization aligns scale endpoints; it does not erase
differences in vocabulary, source family, or coverage.

### 4. Check the readable interpretation

1. Open **Emotion profile**.
2. Confirm that binary category associations and numeric intensity results are
   in separate sections with their denominators stated.
3. Open **Evidence**, try a filter, and inspect match method, source entry, and
   included/suppressed status.
4. Inspect unmatched vocabulary.
5. Open **How to read**.

Expected: the interface consistently describes normative lexical evidence. It
does not declare an emotion for the poem or speaker. Association percentages
are allowed to overlap, and a missing intensity pair is not displayed as zero.

### 5. Check downloads

Under **Downloads**, save:

1. the scholar summary CSV;
2. the CSV reading guide;
3. the full audit ZIP.

Open the scholar summary first. It should have a compact `section`, `metric`,
`value`, and explanation-oriented structure rather than hundreds of token
columns. The ZIP should contain `START_HERE.txt`, both friendly files, and the
complete match, coverage, VAD, association, intensity, comparison, and manifest
audit CSVs.

### 6. Test text-version awareness

After analysis, add one word to the pasted poem without rerunning.

Expected: VerseVAD warns that the text or selection changed. Click **Analyze
this text** again and confirm the warning disappears when the result matches the
current inputs.

### 7. Test local `.txt` import

1. Create a small text file in Notepad and save it as UTF-8 with two lines and a
   blank line between them.
2. In a fresh workspace, click **Upload** and choose that file.
3. Confirm that the contents and line break appear in the text box; edit them if
   desired, then analyze.

Expected: a blank title is filled from the filename, the text remains editable,
and the result reports the preserved line structure. A non-`.txt` file, invalid
UTF-8, or a file larger than 5 MB receives a plain-language refusal.

## How to interpret the CSVs

Use three levels:

1. the file ending in `_scholar_summary.csv` for the compact scholarly overview;
2. `versevad_csv_reading_guide.csv` to decide which detailed table answers the
   next question;
3. the full audit files only for verification, reproducibility, or close
   inspection of contributors.

Always read a score with its lexicon, matched count, coverage, weighting, and
denominator. Compare VAD only on the labeled derived scale and retain the
source-specific rows. Do not compare a category association rate numerically as
if it were an intensity or a VAD mean.

## Current limitations

- The workspace is temporary; Phase 3 does not save a project database.
- Import supports paste and one UTF-8 `.txt` file, not Word, PDF, spreadsheet,
  or batch/corpus import.
- The app analyzes one text at a time and does not yet provide corpus grouping,
  persistent metadata, or Excel workbooks.
- Scholar-reviewed mappings, exclusions, alternative scenarios, and reversible
  review decisions arrive in Phase 5.
- The linguistic model can misread poetic syntax, archaisms, unusual spelling,
  names, and historical senses. Use Evidence and unmatched vocabulary for
  contextual review.
- Normalization places VAD source scales on common endpoints but does not make
  their designs or estimates statistically identical.
