# VerseVAD User Guide

## What is available now

Phase 3 provides a local graphical workspace for one poem at a time. You can
paste a poem or choose a UTF-8 `.txt` file, analyze it with any of the five
supplied lexicons, read a guided result, inspect individual matches, and
download both a friendly summary and the complete audit data.

The workspace lasts only while the app is open. Persistent projects and corpus
work arrive in Phase 4, so download anything you want to retain before closing.

Do not rename or edit anything in `source_lexicons`. VerseVAD reads those files
in place and verifies their SHA-256 checksums.

## First-time setup

1. Open the `ANEW VAD Study` folder.
2. Double-click `setup_windows.bat`.
3. Allow the setup window to finish. The first setup may take several minutes
   and needs internet access to obtain the pinned local runtime and packages.
4. Look for eleven lines marked `PASS`, followed by `All checks passed.`
5. Press a key to close the setup window.

Setup does not need administrator access and does not install Python system
wide. VerseVAD keeps its runtime, environment, and package cache inside ignored
folders in this project.

## Start and stop VerseVAD

1. Double-click `start_versevad.bat`.
2. Keep the launcher window open. Your browser should open
   `http://127.0.0.1:8501` automatically.
3. If the browser does not open, type that exact address into a browser on this
   computer.
4. When finished, download the results you want to keep, then close the browser
   tab and the launcher window.

Ordinary startup is offline. The `127.0.0.1` address means the app is running
on this computer, not on a public website.

## Analyze a poem

1. Under **Add a poem**, either paste the text or click **Upload** and choose a
   UTF-8 `.txt` file no larger than 5 MB. A chosen file fills the editable text
   box; VerseVAD preserves that string and its line breaks as the original.
2. Enter a poem title or working label.
3. Leave all five lexicons selected for a broad first look, or remove sources
   that are outside the current question.
4. Leave **Advanced methodology settings** closed for the default
   phrase-preferred analysis. Open it only when you deliberately want a
   different phrase policy or sparse-result threshold.
5. Click **Analyze this text**. Wait for the green completion message.
6. If you edit the text or change the lexicons afterward, click **Analyze this
   text** again before using the displayed result.

The app never assigns an unmatched token a neutral score. It attempts an exact
normalized surface match before a POS-sensitive lemma fallback and records the
method used.

## Read the result without drowning in CSVs

Use this order:

1. **Overview** — check coverage and matched counts first. A mean based on only
   a few matched observations should be treated cautiously. The displayed 60%
   and 80% coverage bands are orientation aids, not universal scholarly rules.
2. **VAD profile** — compare normative valence, arousal, and dominance ratings
   among matched observations. The side-by-side chart uses a derived 0-1 scale.
3. **Emotion profile** — read categorical associations and numeric intensities
   as separate kinds of evidence.
4. **Evidence** — inspect which surface forms, phrases, or lemmas contributed;
   filter the table when a result needs explanation. Review unmatched
   vocabulary for coverage gaps and historically or poetically unusual words.
5. **Downloads** — start with the friendly scholar summary. Use the full audit
   ZIP when reproducing or closely reviewing the calculation.
6. **How to read** — return here for definitions and a reminder of the intended
   scholarly language.

### Coverage

Coverage is the number of eligible lexical token occurrences covered by an
included match divided by all eligible lexical token occurrences. It is not an
accuracy score. Different lexicons legitimately cover different vocabularies.

### Comparing the three VAD scales

VerseVAD retains every original source rating and creates a separate derived
0-1 value for comparison:

- Warriner VAD, source scale 1-9: `(x - 1) / 8`;
- NRC VAD v1, source scale 0-1: identity, so the derived value equals `x`;
- NRC VAD v2.1, source scale -1 to 1: `(x + 1) / 2`.

This aligns endpoints and midpoints; it does not prove that the lexicons are
interchangeable. Vocabulary coverage, collection methods, versions, and source
families still differ. NRC VAD v1 and v2.1 are versions of one family, not two
independent replications. VerseVAD therefore shows separate rows and creates no
default consensus score.

Higher normalized valence, arousal, or dominance means a higher mean normative
rating for the matched lexical observations on that dimension. It does not mean
that the poem, speaker, author, or reader has "more emotion."

### Associations versus intensity

NRC Emotion associations are binary, multi-label categories. One occurrence
may contribute to several categories, so percentages need not total 100%.
Always read the labeled denominator.

NRC Emotion Intensity supplies numeric ratings for particular word-emotion
pairs. VerseVAD keeps prevalence separate from the mean rating among supplied
matched pairs. A missing pair is not counted as an intensity of zero. Neither
of these constructs is normalized into, pooled with, or averaged into VAD.

## Downloads and the seven audit CSVs

The easiest download has a filename ending in `_scholar_summary.csv`. It contains compact
coverage, normalized VAD, emotion-association, and intensity rows with plain
labels and denominator notes. `VerseVAD_CSV_reading_guide.csv` explains what
each detailed file is for.

The full audit ZIP begins with `START_HERE.txt` and includes those two friendly
files plus:

- `phase2_match_audit.csv` — token/span structure, surface and processing forms,
  POS, lemma, plus included, unmatched, ineligible, and suppressed match
  decisions with source values and provenance;
- `phase2_coverage.csv` — eligible, matched, and unmatched counts and rates;
- `phase2_vad_summary.csv` — source-scale and derived VAD statistics;
- `phase2_emotion_associations.csv` — category counts, rates, denominators, and
  contributors;
- `phase2_emotion_intensity.csv` — prevalence and matched-pair intensity
  summaries;
- `phase2_cross_lexicon_comparison.csv` — source-specific metrics placed side by
  side, with no consensus score;
- `phase2_manifest.csv` — software, source hashes, adapter and recipe details,
  inclusion decisions, and other reproducibility metadata.

CSV files use UTF-8 with a byte-order mark so current versions of Excel usually
open them correctly. The full ZIP is the reproducibility record; the friendly
summary is the reading aid.

## Diagnostics and troubleshooting

Click **Run self-test** in the app sidebar at any time. A healthy installation
shows `11/11 checks passed`. You can also double-click `diagnose_windows.bat`.

If startup fails:

1. close any earlier VerseVAD launcher window;
2. run `diagnose_windows.bat` and note any `FAIL` line;
3. rerun `setup_windows.bat` if the local environment is missing;
4. copy or photograph the complete plain-language error for support.

Invalid encoding, non-text files, blank text, missing titles, and missing
lexicon selections produce a plain-language message without analyzing anything.

## Core terms and limitations

**Token** means one occurrence. **Type** means a unique matched lexical entry.
**Surface form** is the form in context. **Lemma** is a model-proposed base form
and can be wrong for poetic, historical, or unusual language. **Exact match**
links the normalized surface directly to a source entry and takes priority over
lemma fallback.

VerseVAD describes lexical evidence. It does not resolve negation, irony,
metaphor, voice, authorial intention, historical sense, or reader response.
Those remain matters for contextual inspection and scholarly interpretation.

## Older validation demonstrations

`test_phase1.bat` and `test_phase2.bat` remain available as invented,
hand-calculated engine demonstrations. Their generated `phase1_demo_output` and
`phase2_demo_output` folders can be deleted safely and recreated by rerunning
the corresponding demonstration.
