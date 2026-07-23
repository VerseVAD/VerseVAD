# VerseVAD User Guide

## What is available now

VerseVAD provides three local workspaces: **One Poem**, **Projects & Corpus**,
and **Lexicon Explorer**. One-poem analyses remain temporary unless downloaded.
Corpus projects, preserved text versions, metadata, completed results, and
versioned review scenarios persist in the local `projects` database.

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

The installed app has no ChatGPT or OpenAI API dependency. It remains usable if
you cancel a ChatGPT subscription. Internet access is needed only if you later
reinstall dependencies or deliberately update the software.

## Analyze a poem

1. Under **Add a Poem**, either paste the text or click **Upload** and choose a
   UTF-8 `.txt` file no larger than 5 MB. A chosen file fills the editable text
   box; VerseVAD preserves that string and its line breaks as the original.
2. Enter a poem title or working label.
3. Leave all five lexicons selected for a broad first look, or remove sources
   that are outside the current question.
4. Leave **Advanced methodology settings** closed for the default
   phrase-preferred and standard stopword analysis. Open it when you
   deliberately want a different phrase policy, sparse-result threshold, or
   custom stopword additions/removals.
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
2. **Language Profile** — inspect the shared poetry-preserving processing
   record, then compare model-assigned part-of-speech counts and relative
   shares across all eligible lexical tokens. This profile is independent of
   affective-lexicon matching.
3. **VAD Profile** — compare normative valence, arousal, and dominance ratings
   among matched observations. Definitions, interpretations, token/type
   weighting, cumulative loads, and top contributors appear beneath the
   derived 0-1 comparison chart.
4. **Emotion Profile** — read the eight emotion associations, positive/negative
   sentiment associations, and numeric intensities as three separately labeled
   kinds of evidence.
5. **Evidence** — inspect which surface forms, phrases, lemmas, exclusions, or
   approved mappings contributed;
   filter the table when a result needs explanation. Review unmatched
   vocabulary for coverage gaps and historically or poetically unusual words.
6. **Downloads** — start with the friendly scholar summary. Use the full audit
   ZIP when reproducing or closely reviewing the calculation.
7. **How to Read** — return here for definitions and a reminder of the intended
   scholarly language.

### Coverage

Coverage is the number of eligible lexical token occurrences covered by an
included match divided by all eligible lexical token occurrences. It is not an
accuracy score. Different lexicons legitimately cover different vocabularies.

### Part-of-speech profile

The **Shared Processing Record** at the top of Language Profile reports stanza,
physical-line, model-sentence, total-token, and lexical-token counts; recipe
and configuration IDs; the model pipeline; dependency coverage; named-entity
recognition status; and processing cautions. Poetic lines/stanzas and model
sentences are separate layers, so their boundaries can disagree without either
being discarded.

VerseVAD creates this shared record once and reuses the same token sequence for
every selected lexicon. Original text, capitalization, punctuation, blank
lines, and line endings remain preserved. Normalized forms, lemmas, POS,
morphology, sentences, dependencies, and optional named entities are separate
model-assisted fields and may be uncertain for poetic or historical language.

The Language Profile counts all eligible lexical token occurrences by the
installed model's universal part-of-speech tag and divides each count by the
text's full lexical-token count. It also reports unique normalized types and
example forms. Shares sum to 100% apart from display rounding.

The main chart uses broad categories. **Detailed Model-Tag Breakdown** then
reports the unmerged Universal Dependencies tags with their own counts and
shares. These are two views of the same tokens, so do not add them together.

Part-of-speech labels are model-generated. Poetic syntax, fragments, archaic
forms, and deliberate ambiguity can produce uncertain assignments. Inspect
token evidence before making an argument that depends on a fine grammatical
distinction.

VerseVAD combines common-noun (`NOUN`) and proper-noun (`PROPN`) model tags
into the single displayed category **Noun**. Original token tags remain in the
detailed table and evidence/audit data. The `ADP` tag is displayed as
**Preposition**; an adverb is a different category.

It also combines main-verb (`VERB`) and auxiliary/copular (`AUX`) tags into
**Verb**. Thus `was` is counted as a verb even when the model uses `AUX` for
its grammatical role.

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

NRC VAD v1's 132 whitespace-containing source entries participate as exact,
longest-first phrase candidates under the selected phrase policy, just as
Warriner's 102 activated whitespace entries do. This preserves source entries
without claiming a separate phrase-specific validation methodology.

Higher normalized valence, arousal, or dominance means a higher mean normative
rating for the matched lexical observations on that dimension. It does not mean
that the poem, speaker, author, or reader has "more emotion."

### Token/type means and cumulative load

A token-weighted mean counts every included occurrence, so repetition matters.
A type-weighted mean counts each distinct matched lexicon entry once within the
work, so it describes the matched vocabulary rather than repetition. VerseVAD
shows valence, arousal, and dominance for both.

Cumulative normative lexical load is intentionally length-sensitive. The
rating total sums normalized ratings. Above- and below-midpoint loads sum
distance on either side of 0.5; net load permits cancellation; absolute load
sums distance in either direction. These are totals of encountered matched
lexical ratings, not measurements of cognitive or emotional load on a reader.

Top contributors use a leave-one-matched-type-out calculation: VerseVAD removes
all occurrences of one matched entry and reports the change in the token mean.
The primary ranking uses `frequency × (normalized rating - 0.5)`, so repetition
and distance from the normalized midpoint remain visible. This makes rating and
repetition effects inspectable without claiming a causal effect on
interpretation.

### All matched versus stopwords excluded

The VAD page shows both views by default:

- **All matched observations** retains every included lexicon match.
- **Stopwords excluded** removes entries recognized by the declared stopword
  policy while retaining protected terms such as `not`, `never`, and `without`.

The second view uses a content-focused coverage denominator containing eligible
non-stopword tokens. Published phrase entries stay intact. Open the methodology
settings to see the pinned list source, version, active count, and hash; select
custom mode to add or remove words, import a plain-text list, or download the
active list. Every exclusion and its surface/lemma reason remains visible under
**Evidence** and in the audit exports.

### Associations versus intensity

NRC Emotion associations are binary and multi-label. VerseVAD reports anger,
anticipation, disgust, fear, joy, sadness, surprise, and trust in **Eight
Emotion Associations**. It reports positive and negative separately under
**Positive and Negative Sentiment Associations**. One occurrence may
contribute to several categories, so percentages need not total 100%. Always
read the labeled denominator.

NRC Emotion Intensity supplies numeric ratings for particular word-emotion
pairs. VerseVAD keeps prevalence separate from the mean rating among supplied
matched pairs. A missing pair is not counted as an intensity of zero. Neither
of these constructs is normalized into, pooled with, or averaged into VAD.

## Build and compare a corpus

1. Choose **Projects & Corpus** in the workspace tabs across the top.
2. Create a project. It is stored in `projects/versevad.sqlite3` by default.
3. Under **Works & Metadata**, choose a folder containing UTF-8 `.txt` files.
   Each file is a separate work and subfolder paths are retained. Re-importing
   changed content creates a new preserved version under the same work ID.
4. Edit author, collection, date label, genre, notes, or custom JSON metadata.
5. Use **Language Profile** to compare part-of-speech count and relative share
   in the combined project and work by work.
6. Under **Analyze & Compare**, select works and lexicons, choose an unreviewed
   baseline or exact scenario version, then click **Analyze selected works**.
   VerseVAD processes one work at a time and publishes the dashboard only when
   the entire selected batch completes.
7. Filter a completed comparison by collection, author, or genre.
8. Under **Review & Scenarios**, create a named scenario and record reversible,
   versioned flags, exclusions, or mappings with a rationale and explicit
   occurrence/work/project/global scope.
9. Rerun with that scenario and compare the new immutable batch with the
   unreviewed baseline.
10. Download the Excel workbook under **Excel Export**.

To delete a project, open **Project Settings**, read the warning, and type the
project title exactly—including capitalization—before clicking **Delete this
project**. This permanently removes only that project and its locally stored
works, versions, analyses, and notes. Other projects and source lexicons are
not touched.

### Long and short works in one collection

VerseVAD reports two collection VAD views:

- **Token-weighted volume profile:** pools included matched observations. Long
  poems contribute more because they contain more of the volume's vocabulary.
- **Work-weighted volume profile:** averages eligible work-level token means.
  Every poem contributes one score regardless of length.

Neither is the universally correct view; they answer different questions. The
dashboard and Excel workbook show their signed difference. A divergence may be
an important result. A work with no eligible score is reported as omitted and
never assigned a neutral value.

### Corpus part-of-speech views

**All Works Combined** pools lexical-token occurrences, so longer works
contribute more to the combined grammatical profile. **Work-by-Work
Comparison** reports each work's count and within-work share separately. Use
the latter when comparing relative grammatical composition across differently
sized works. Broad and detailed profile levels are both available. The Excel
workbook includes the same rows and a **Profile Level** field in **Part of
Speech**.

### Review scenarios

A **flag** records a concern without changing scores. An **exclude** decision
keeps the candidate in the audit but omits it from that scenario's aggregates.
A **map** decision links a form to a verified exact entry in one installed
lexicon only after exact, apostrophe/possessive, and lemma candidates fail.

Use the narrowest defensible scope and provide a scholarly rationale. Every
change, revoke, restore, or restored snapshot creates a new append-only
scenario version. Completed corpus batches stay linked to the exact scenario
version and decision revisions used, so the baseline is never overwritten.

## Use Lexicon Explorer

1. Choose **Lexicon Explorer** in the workspace tabs across the top.
2. Enter one word or phrase. VerseVAD searches every installed source.
3. Read **How it matched** before reading values: exact entry, exact phrase,
   lemma-derived entry, or user-supplied mapped lookup are distinct.
4. Leave **Original and normalized** selected to retain source ratings and the
   separate derived 0-1 comparison together.
5. Expand variation/provenance panels when investigating a surprising entry.

Warriner standard deviations and rater counts appear where supplied. Empty
uncertainty cells mean the source did not provide those fields. Cross-lexicon
"agreement" is a labeled VerseVAD range heuristic, not a source reliability
statistic. A component average appears only when a phrase has no published VAD
entry in that source and all component words do; it is clearly labeled as a
derived value. Similar-word suggestions are never substituted automatically.

An optional user mapping can display, for example, `o'er → over`, but it is a
lookup-only fallback and does not alter poem or corpus analysis. Persistent,
scenario-controlled mappings are created separately under **Review &
Scenarios**.

## Downloads and the audit bundle

The easiest download has a filename ending in `_scholar_summary.csv`. It
contains compact part-of-speech, coverage, normalized VAD,
emotion-association, sentiment-association, and intensity rows with plain
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
- `phase2_results.json` — the structured analysis result, including the complete
  stopword policy and both VAD views, for machine-readable reuse.
- `poem_document.json` — exact original text, stanza/line and model-sentence
  structure, shared tokens and annotations, orthographic spans, processing
  configuration/provenance, coverage, and warnings.

CSV files use UTF-8 with a byte-order mark so current versions of Excel usually
open them correctly. Both JSON files are local machine-readable records.
`poem_document.json` contains the original text, so protect it as research
material. The full ZIP is the reproducibility record; the friendly summary is
the reading aid.

## Diagnostics and troubleshooting

Under **Installation Check**, click **Run self-test** in the app sidebar at any
time. A healthy installation shows `11/11 checks passed`. You can also
double-click `diagnose_windows.bat`.

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
The part-of-speech profile is model-generated grammatical evidence and can
also require correction through close inspection.

## Older validation demonstrations

`test_phase1.bat` and `test_phase2.bat` remain available as invented,
hand-calculated engine demonstrations. Their generated `phase1_demo_output` and
`phase2_demo_output` folders can be deleted safely and recreated by rerunning
the corresponding demonstration.
