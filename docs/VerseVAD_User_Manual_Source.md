# VerseVAD User Manual

## Local, auditable affective-lexicon analysis for literary texts

**Software version:** {{VERSION}}  
**Manual updated:** {{DATE}}  
**Intended reader:** A first-time user who needs no programming, linguistics, or statistics background

> IMPORTANT: VerseVAD describes affective **lexical evidence**: normative ratings and associations attached to matched words and phrases. It does not determine the emotion of a poem, speaker, author, or reader, and it does not replace contextual close reading.

[[PAGEBREAK]]

# Contents at a glance

1. Purpose, privacy, and scholarly scope
2. Installation, startup, and shutdown
3. Five-minute first analysis
4. The installed lexicons
5. How text becomes auditable matches
6. Dual VAD reporting and stopwords
7. How to interpret every result
8. One Poem workspace
9. Projects & Corpus workspace
10. Lexicon Explorer
11. Downloads, CSV files, JSON, and Excel
12. Mathematical formulas
13. Glossary
14. Troubleshooting and limitations
15. Reproducibility and updating this manual

> QUICK ORIENTATION: Read **Overview** first, then **VAD Profile**, then inspect **Evidence**. Download the readable summary for ordinary review and the full audit bundle when you need reproducibility. If a term is unfamiliar, use the separate `VerseVAD_Values_and_Terminology_Guide.docx`, which includes plain-language definitions, formulas, worked examples, and reporting templates.

# 1. Purpose, privacy, and scholarly scope

## What VerseVAD does

VerseVAD compares words and accepted phrases in a literary text with locally installed affective lexicons. Depending on the selected source, it can report:

- normative valence, arousal, and dominance ratings;
- binary emotion and sentiment associations;
- numeric word-emotion intensity ratings;
- token- and type-weighted summaries;
- part-of-speech counts and relative shares over all eligible lexical tokens;
- all-matched and stopword-excluded VAD views;
- coverage and unmatched vocabulary;
- cumulative, length-sensitive normative lexical totals;
- the largest midpoint-centered lexical contributors;
- work-level and collection-level corpus comparisons;
- named, versioned review scenarios for flags, exclusions, and approved mappings;
- source provenance and uncertainty fields in Lexicon Explorer.

## What VerseVAD does not do

VerseVAD does not infer an author's intention, diagnose a speaker, identify a poem's true emotion, or measure an individual reader's response. It does not resolve irony, metaphor, polysemy, historical sense, narrative distance, quotation, or negation compositionally. It provides inspectable lexical evidence for a scholar to interpret in context.

## Privacy and offline use

Ordinary use runs locally on this computer at `http://127.0.0.1:8501`. VerseVAD does not send literary texts, lexicons, projects, or results to ChatGPT, OpenAI, or another external service. Once the local environment is installed, ordinary analysis does not require a ChatGPT subscription.

The supplied lexicons remain under `source_lexicons/` and must not be renamed, edited, merged, or redistributed. VerseVAD reads them in place, records SHA-256 checksums, and stores derived project data separately.

# 2. Installation, startup, and shutdown

## First-time setup

1. Open the `ANEW VAD Study` folder.
2. Double-click `setup_windows.bat`.
3. Allow the setup window to finish. The first setup can use the internet to obtain the pinned local runtime and packages.
4. Confirm that the diagnostic lines end in `PASS` and the setup reports that all checks passed.
5. Press a key if the setup window asks you to do so.

Setup is project-local. It does not require administrator access or a system-wide Python installation.

## Start VerseVAD

1. Double-click `start_versevad.bat`.
2. Keep the visible launcher window open while using VerseVAD.
3. Your default browser should open `http://127.0.0.1:8501`.
4. If the browser does not open automatically, type that address into a browser on the same computer.

The workspace selector appears as three tabs across the top:

- **One Poem**
- **Projects & Corpus**
- **Lexicon Explorer**

## Stop VerseVAD

Close the browser tab, then close the visible launcher window. One-poem results exist only in the current application session unless downloaded. Corpus projects persist in the local SQLite database.

# 3. Five-minute first analysis

1. Open **One Poem**.
2. Enter a title or working label.
3. Paste a short poem, or upload a UTF-8 `.txt` file.
4. Keep the selected lexicons and default methodology for the first run.
5. Keep both reporting views enabled.
6. Click **Analyze this text**.
7. In **Overview**, inspect coverage and warnings.
8. In **VAD Profile**, compare all matched observations with stopwords excluded.
9. In **Language Profile**, inspect the independent grammatical profile when it is relevant to your question.
10. In **Evidence**, inspect exactly which surface forms, lemmas, or phrases matched.
11. In **Downloads**, save the readable summary or full audit bundle.

> SAFE PRACTICE: A high or low mean is not self-interpreting. Always read it with the lexicon name, analysis view, weighting, matched count, coverage, and evidence table.

# 4. The installed lexicons

| VerseVAD source | What it supplies | Original scale | Derived comparison |
|---|---|---|---|
| Warriner VAD 2013 | Valence, arousal, dominance; standard deviations and rater counts | 1 to 9 | `(x - 1) / 8` |
| NRC VAD v1 | Valence, arousal, dominance; words and 132 activated whitespace entries | 0 to 1 | `x` |
| NRC VAD v2.1 | Valence, arousal, dominance; unigrams and multiword expressions | -1 to 1 | `(x + 1) / 2` |
| NRC Emotion v0.92 | Eight emotion associations plus positive and negative sentiment | Binary 0 or 1 | Not normalized into VAD |
| NRC Emotion Intensity v1 | Numeric intensity for supplied word-emotion pairs | 0 to 1 | Retained on its own scale |

## Valence, arousal, and dominance

**Valence** is the normative pleasantness or unpleasantness associated with a lexical item. Higher normalized values indicate more pleasant norms; lower values indicate more unpleasant norms.

**Arousal** is the normative activation or intensity associated with a lexical item. Higher normalized values indicate more activated or energetic norms; lower values indicate calmer or less activated norms.

**Dominance** is the normative sense of control, power, or agency associated with a lexical item. Higher normalized values indicate greater control or power in the source ratings; lower values indicate less.

These are ratings gathered from participants for lexical items. They are not direct measurements of the present poem, context, or reader.

## Why original and normalized values both matter

Original values preserve what the source publishes. Derived normalized values align the documented minimum, midpoint, and maximum of each VAD scale to 0, 0.5, and 1. This makes visual comparison possible, but it does not make different lexicons interchangeable. Their vocabularies, participants, procedures, dates, and versions still differ. VerseVAD does not create a default consensus score.

NRC VAD v1 and NRC VAD v2.1 are versions of the same lexicon family, not independent replications.

## Phrase coverage

NRC VAD v2.1 explicitly contains multiword expressions. VerseVAD also activates the 102 whitespace-containing rows in the local Warriner source and the 132 whitespace-containing rows in NRC VAD v1 as exact, auditable phrase candidates at the user's request. This is a declared processing choice and does not claim that Warriner or NRC VAD v1 supplied a separate phrase-specific validation study.

# 5. How text becomes auditable matches

## Preserved original and processing representation

VerseVAD preserves the supplied text exactly, including line and stanza breaks. Normalization happens in a separate processing representation. The original text is never silently rewritten.

## Main matching order

1. Preserve the original text and structural positions.
2. Create normalized processing forms.
3. Exclude punctuation from numeric summaries while retaining it in the audit.
4. Search for the longest accepted exact phrase without crossing a line or punctuation boundary.
5. Attempt an exact normalized surface-form match.
6. Apply conservative apostrophe and possessive normalization.
7. Attempt POS-sensitive lemma fallback only when exact matching fails.
8. Leave unresolved or unmatched items missing.

An exact surface match is never silently replaced by a lemma match. Lemma matching is explicitly labeled because model-proposed lemmas can be wrong for poetic, historical, or unusual language.

## Phrase-policy choices

| Policy | Behavior | Interpretive consequence |
|---|---|---|
| Prefer the longest phrase | An accepted phrase contributes one observation; covered component candidates are suppressed but audited | Recommended default |
| Unigrams only | Phrase entries are ignored; individual words can match | Useful sensitivity view |
| Phrase and components | Phrase and independently matched components both contribute | Exploratory and intentionally double-counts the span |

Accepted phrases never cross poetic line or punctuation boundaries. Shorter overlapping phrases and covered components remain visible in the audit.

## Match and audit statuses

An audit row can be included, unmatched, ineligible, suppressed as a phrase component, or suppressed by a longer overlapping phrase. Included matches record the source term, original and normalized values, matching method, token or span location, stopword status, and inclusion in both VAD views.

Unmatched tokens never receive 0, 0.5, a corpus mean, or another invented value.

# 6. Dual VAD reporting and stopwords

## The two result views

Every VAD analysis preserves:

- **All matched observations:** every included lexicon match under the declared phrase policy.
- **Stopwords excluded:** a secondary aggregate derived from the same matches after applying the recorded stopword policy.

The second view changes aggregate inclusion only. It does not retokenize the text, alter source ratings, or change exact-versus-lemma matching priority.

## Standard stopword policy

The standard policy is based on the pinned spaCy English `STOP_WORDS` list. VerseVAD records:

- stopword source and installed library version;
- VerseVAD list-policy version;
- standard and active word counts;
- SHA-256 hashes of the standard and active lists;
- protected words;
- custom additions and removals;
- surface or lemma evidence for each decision.

## Protected terms

VerseVAD protects meaning-changing negations, modals, comparatives, and intensifiers from default exclusion. The current protected set is:

`against, could, least, less, may, might, more, most, must, neither, never, no, nor, not, should, too, very, without`

A protected word remains in both result views unless the scholar deliberately changes the protected list.

## Custom stopwords

In **Stopword settings**, choose **Use custom stopword list** to:

- add one normalized word per line;
- remove a word from the standard list;
- import a UTF-8 plain-text list;
- export the exact active list;
- restore VerseVAD defaults.

A custom addition is a methodological choice, not a claim that the word is universally meaningless. For example, adding `raven` during a test proves that custom exclusion works; `raven` is not a VerseVAD default stopword.

Phrase entries remain intact. VerseVAD does not break a published phrase and remove one component merely because that component appears on the stopword list.

## Content-focused coverage

Ordinary coverage uses all eligible lexical tokens as its denominator. Content-focused coverage uses eligible non-stopword tokens under the active policy. VerseVAD also reports how many matched observations and types were excluded from the secondary view.

# 7. How to interpret every result

## Part-of-speech profile

The **Language Profile** is independent of affective-lexicon matching. It uses all eligible lexical token occurrences and reports the model-assigned universal part-of-speech category, token count, share of lexical tokens, unique normalized types, and example forms.

`POS share = token occurrences assigned to one POS / all eligible lexical token occurrences`

Counts answer “how many occurrences received this label?” Shares answer “what proportion of the text's eligible lexical tokens received this label?” The shares sum to 100 percent apart from display rounding.

These labels are generated by the installed English linguistic model. Poetic syntax, fragments, archaisms, unusual capitalization, and deliberate ambiguity can produce uncertain assignments. Treat the profile as descriptive and inspect the token evidence when a grammatical distinction matters.

## Coverage

Coverage answers: “How much eligible vocabulary was represented by this source under this matching policy?” It is not an accuracy score.

Always inspect:

- eligible token count;
- matched token count;
- unmatched token count;
- lexical-token coverage;
- matched observation count;
- unique matched entry count;
- lemma reliance and warnings;
- content-focused coverage for the stopword-excluded view.

Different lexicons can have legitimately different coverage. A broad mean with poor coverage may describe only a narrow subset of the text.

## Token-weighted and type-weighted means

**Token-weighted mean:** every included occurrence contributes. Repetition matters.

**Type-weighted mean:** every distinct matched lexicon entry contributes once within the analyzed work. Repetition does not increase that entry's weight.

The difference between these views can reveal whether repeated vocabulary shifts the profile away from the vocabulary inventory considered once each.

## Population standard deviation

VerseVAD reports population standard deviation for the complete selected matched set. A larger value means the source ratings included in that result are more dispersed around their mean. It does not measure rating uncertainty in the lexicon and is not a confidence interval.

Warriner's source-provided rating standard deviations in Lexicon Explorer are different: they describe participant variation for one lexical entry.

## Stopword sensitivity

Stopword sensitivity is:

`stopwords-excluded statistic - all-matched statistic`

A positive value means the filtered view is higher; a negative value means it is lower. A small difference indicates that this particular statistic changes little under the policy. It is descriptive and is not a universal robustness threshold.

## Cumulative normative lexical load

Cumulative totals are intentionally sensitive to text length and repetition. VerseVAD reports:

- rating total;
- above-midpoint load;
- below-midpoint load;
- net midpoint load;
- absolute midpoint load.

These quantities summarize encountered matched lexical ratings. They are not direct measurements of cognitive load or affective impact on a reader.

## Top contributors

For each dimension and result view, VerseVAD ranks matched entries by signed midpoint-centered contribution:

`frequency * (normalized rating - 0.5)`

Positive values contribute above the normalized midpoint; negative values contribute below it. Frequency makes repetition visible. The table also retains the change in the token mean when all occurrences of that type are removed.

## Eight emotion associations

NRC Emotion values are binary, multi-label associations. VerseVAD reports the eight emotions—anger, anticipation, disgust, fear, joy, sadness, surprise, and trust—in their own section. An entry can be associated with several categories, so percentages do not need to total 100 percent. Read the labeled denominator.

“Fear-associated vocabulary” is appropriate wording. “The poem is afraid” is not.

## Positive and negative sentiment associations

Positive and negative are broad sentiment labels in NRC Emotion. VerseVAD analyzes them with the same documented occurrence-counting logic but reports them separately from the eight emotions. They are not endpoints of the VAD valence scale, and their rates need not sum to 100 percent.

## Emotion intensity

NRC Emotion Intensity supplies numeric values only for particular word-emotion pairs. VerseVAD keeps:

- prevalence of matched pairs;
- token-weighted mean intensity among supplied pairs;
- type-weighted mean intensity among supplied pairs.

An absent word-emotion pair is missing, not an intensity of zero.

# 8. One Poem Workspace

## Add a poem

Paste text or upload one UTF-8 `.txt` file up to 5 MB. Enter a title or working label. The optional workspace name labels the temporary session but does not create a persistent corpus project.

## Choose evidence

Select one or more lexicons. VAD, categorical association, and intensity resources answer different questions and remain separate.

Under **Advanced methodology settings**, choose:

- phrase policy;
- minimum matched observations for sparse-result warnings;
- whether to display all-matched results;
- whether to display stopword-excluded results.

Under **Stopword settings**, inspect or change the secondary-view policy. The all-matched result is always preserved even when only one view is displayed.

## Overview tab

Read coverage before means. The tab shows ordinary and content-focused coverage, matched counts, active methodology, excluded stopword counts, interpretive framing, and warnings.

## Language Profile tab

This tab reports part-of-speech counts and relative shares for all eligible lexical tokens, independently of lexicon coverage. It also shows unique normalized types and example forms. The denominator is displayed, and a caution explains that the labels are model-generated.

## VAD Profile tab

This tab contains:

- parallel normalized VAD charts;
- definitions of valence, arousal, and dominance;
- token- and type-weighted values for each analysis view;
- plain-language midpoint interpretations;
- population dispersion;
- stopword-sensitivity differences;
- cumulative normalized totals;
- top midpoint-centered contributors;
- original source scales and normalization formulas.

## Emotion Profile tab

The eight emotion associations, positive/negative sentiment associations, and numeric emotion intensities appear in three separate sections. Do not compare their values as though they were alternate VAD scales.

## Evidence tab

Filter by lexicon, match status, or stopword status. The excluded-only control isolates matched observations omitted from the stopword-excluded view. Inspect normalized form, lemma, match method, matched entry, source values, and the exact stopword reason.

The unmatched-vocabulary table supports quality control. It does not silently guess replacements.

## Downloads tab

Download:

- a readable scholar summary CSV;
- the CSV reading guide;
- the full audit ZIP.

One-poem results are temporary, so download anything you need before closing the application.

## How to Read tab

Use this tab as an in-application reminder of the recommended reading order, terminology, and scholarly limits.

# 9. Projects & Corpus Workspace

## Create a project

Open **Projects & Corpus**, expand **Create a research project**, and enter a title. Description and researcher fields are optional. Projects persist locally in `projects/versevad.sqlite3` unless an alternate database path is configured.

## Import a folder

1. Put each work in a separate UTF-8 `.txt` file.
2. Choose the folder under **Works & Metadata**.
3. VerseVAD imports each file as a separate work and retains relative subfolder paths.
4. Reimporting changed content creates a new preserved text version rather than rewriting the version used by earlier analyses.

Never use `source_lexicons/` as a corpus folder.

## Edit metadata

Select one work and edit the available fields:

- title;
- author;
- collection;
- date label;
- genre;
- notes;
- custom JSON metadata.

Metadata filters affect presentation and grouping, not lexical scores.

## Run a corpus batch

Under **Analyze & Compare**:

1. Select the works.
2. Select the lexicons.
3. Choose phrase and sparse-result settings.
4. Choose the stopword policy.
5. Choose **Unreviewed baseline** or an exact named review-scenario version.
6. Click **Analyze selected works**.

VerseVAD analyzes every work separately. The new comparison is published only after the entire selected batch completes. Pending or failed batches never replace the latest complete comparison.

## Filter and compare

Filter the completed batch by collection, author, or genre. Select one or both analysis views. Compare work-level token- or type-weighted means without mixing those weightings silently.

## Long and short works

VerseVAD reports two collection profiles:

- **Token-weighted volume profile:** every included matched observation receives equal weight. Longer works contribute more because they contain more of the volume.
- **Work-weighted volume profile:** every eligible work-level token mean receives equal weight, regardless of length.

Neither is universally correct. Their difference can itself be important evidence.

## Cumulative corpus results

Length-sensitive cumulative totals remain separate from means. Use them when the number and repetition of matched ratings across a work or volume is substantively relevant, while retaining the warning that they are normative lexical totals rather than measured reader impact.

## Corpus Language Profile

The **Language Profile** tab reports:

- **All Works Combined:** pooled POS token counts and shares, in which long works contribute more because they contain more tokens.
- **Work-by-Work Comparison:** each work's POS count, within-work share, unique normalized types, examples, and denominator.

This profile is calculated from the current preserved version of every work and does not depend on which affective lexicon was selected. Use within-work shares when comparing works of different lengths; retain raw counts when quantity itself matters.

## Review decisions and named scenarios

Phase 5 lets you test explicit scholarly decisions without rewriting an earlier result. Start with an unreviewed baseline, then open **Review & Scenarios** and create a named scenario.

The available actions are:

- **Flag:** records a concern or interpretive note without changing a score.
- **Exclude:** preserves the published candidate in the audit but omits it from that scenario's aggregates.
- **Map:** after exact, possessive/apostrophe, and lemma candidates fail, maps a form to a verified exact entry in one selected lexicon. The method is labeled `approved_user_mapping`.

Choose the narrowest defensible scope:

- **Occurrence:** one token position in one preserved text version.
- **Work:** eligible occurrences in one selected work.
- **Project:** eligible occurrences across the project.
- **Global within scenario use:** eligible occurrences wherever that scenario is evaluated.

Every decision requires a rationale and becomes an append-only revision. Revoking, restoring, or restoring an older snapshot creates a new scenario version. Completed batches stay pinned to the exact scenario version and decision revisions used at calculation time.

### Beginner-safe review workflow

1. Run and retain an unreviewed baseline.
2. Create a clearly named scenario.
3. Inspect one candidate's text context, lexicon, match method, and risk label.
4. Choose flag, exclude, or map.
5. Select the narrowest scope that fits the evidence.
6. Write a rationale another scholar could evaluate.
7. Return to **Analyze & Compare**, select that scenario version, and rerun.
8. Compare the reviewed batch with the baseline under **Compare Two Immutable Analysis Batches**.
9. Inspect coverage changes, VAD deltas, match evidence, and unmatched vocabulary.
10. Export the workbook and preserve its methodology and **Review Decisions** sheet.

Conflicting same-scope mappings are rejected. A mapping target must exist as an exact entry in the selected installed lexicon. A proposed mapping in the older unmatched-note form remains documentation only; it does not change a calculation unless converted into an active scenario decision.

## Unmatched quality-control notes

The legacy unmatched-quality-control panel remains available beneath **Review & Scenarios**. It stores status, research note, and possible mapping text locally. These notes support research bookkeeping but do not alter completed or future analyses by themselves.

## Compare immutable batches

Under **Analyze & Compare**, choose two completed batches to see like-for-like coverage and VAD deltas. Because each batch remains tied to its exact text versions, lexicons, recipe, stopword policy, software version, scenario version, and decision revisions, this comparison can show how an explicit review scenario changed the result without erasing the baseline.

## Excel Export

After a complete batch, download the corpus workbook. It includes a reading guide, both collection weighting views, both stopword views, work-level data, cumulative totals, coverage, separately labeled emotion/sentiment/intensity constructs, unmatched notes, text/version provenance, review decisions when applicable, and the recorded methodology.

## Delete a project

1. Select the project.
2. Open **Project Settings**.
3. Read the permanent-deletion warning.
4. Type the project title exactly, including capitalization.
5. Click **Delete this project**.

The button remains unavailable until the title matches exactly. Deletion removes only that project's local works, versions, batches, analyses, metrics, and notes. It does not affect other projects or source lexicons. This deletion is permanent unless you have a separate backup.

# 10. Lexicon Explorer

## Basic lookup

1. Open **Lexicon Explorer**.
2. Enter one word or phrase.
3. Optionally enter a user-supplied mapping.
4. Click **Search installed lexicons**.

## Match labels

The Explorer distinguishes:

- exact entry;
- exact published phrase;
- lemma-derived entry;
- user-mapped entry;
- VerseVAD-derived component average;
- suggestion only;
- no match.

It never substitutes a merely similar word automatically.

## Display modes

Use original values to see the source's published scale. Use normalized values for the separately derived 0-1 comparison. Keeping both visible is recommended.

## Cross-lexicon spread

For entries found in multiple VAD sources, VerseVAD reports the range of normalized ratings and a descriptive agreement label. This is a VerseVAD orientation heuristic, not a source-provided reliability statistic or inferential test.

## Rating uncertainty and provenance

Where Warriner supplies them, the Explorer shows dimension-specific standard deviations and rater counts. A high source standard deviation indicates greater participant disagreement around that entry's mean.

The provenance panel identifies the lexicon, version, source scale, adapter, imported file, checksum, and source details. Empty uncertainty fields mean the source did not provide those values.

## Phrase and component behavior

An exact phrase entry is shown as published lexical evidence. If no phrase entry exists but all component words have exact VAD entries in one source, VerseVAD may show their arithmetic mean as a clearly labeled **derived component average**. It never presents that calculation as a published phrase rating.

## User mapping

A mapping such as `o'er -> over` is lookup-only. It lets you inspect the mapped entry while preserving the distinction between queried and mapped forms. It does not change poem or corpus analysis.

# 11. Downloads, CSV files, JSON, and Excel

## One-poem downloads

| File | Best use |
|---|---|
| Scholar summary CSV | Readable overview with plain labels |
| CSV reading guide | Meaning and recommended use of each detailed file |
| Full audit ZIP | Reproducibility, inspection, and machine-readable records |

The ZIP begins with `START_HERE.txt` and contains the summary, guide, and the following detailed files.

| Audit file | Contents |
|---|---|
| `phase2_match_audit.csv` | Token/span positions, forms, lemmas, match methods, source values, inclusion/suppression, and stopword decisions |
| `phase2_coverage.csv` | Ordinary and content-focused denominators, counts, and rates |
| `phase2_vad_summary.csv` | Original and normalized VAD statistics for both views and both weightings |
| `phase2_emotion_associations.csv` | Eight-emotion and positive/negative source associations, retained as labeled categories for audit |
| `phase2_emotion_intensity.csv` | Pair prevalence and matched-pair intensity statistics |
| `phase2_cross_lexicon_comparison.csv` | Source-specific metrics placed side by side without a consensus score |
| `phase2_manifest.csv` | Software, source hashes, adapters, recipe, scenario, stopword policy, and inclusion metadata |
| `phase2_results.json` | Complete structured analysis result for machine-readable reuse |

CSV files use UTF-8 with a byte-order mark for compatibility with current Excel versions. The JSON file is the most complete structured representation; the scholar summary is the easiest reading aid.

## Corpus Excel workbook

| Sheet | Contents |
|---|---|
| START HERE | Reading order, weighting distinctions, and cautions |
| Corpus Profiles | Token-weighted and equal-work-weighted collection VAD profiles by analysis view |
| Work VAD | Work-level means and population standard deviations, token/type weighting, source/normalized scale |
| Cumulative Load | Length-sensitive totals by work and analysis view |
| Coverage and Emotion | Coverage plus a `Construct` field separating emotion associations, sentiment associations, and supplied emotion-intensity metrics |
| Part of Speech | Combined-project and work-level universal POS counts, lexical-token shares, unique types, examples, denominator, and model |
| Unmatched QC | Persistent review statuses, notes, and proposed mappings |
| Review Decisions | Active decision revisions pinned to the exported scenario; present for reviewed runs |
| Text Metadata | Work IDs, text-version IDs, metadata, paths, and hashes |
| Methodology | Selected lexicons, phrase policy, stopword source/version/hash, protected terms, and custom changes |

Excel is a derived report, not the authoritative database. The workbook does not duplicate the complete literary texts.

# 12. Mathematical formulas

Let `x_i` be the normalized VAD value for included matched observation `i`, `N` the number of included observations, `x_t` the value for distinct matched entry `t`, `T` the number of distinct matched entries, and `f_t` the frequency of entry `t`.

## Normalization

| Source scale | Formula |
|---|---|
| Warriner 1 to 9 | `x_normalized = (x_original - 1) / 8` |
| NRC VAD v1 0 to 1 | `x_normalized = x_original` |
| NRC VAD v2.1 -1 to 1 | `x_normalized = (x_original + 1) / 2` |

## Work-level means and dispersion

**Token-weighted mean**

`mean_token = sum(x_i) / N`

**Type-weighted mean**

`mean_type = sum(x_t) / T`

**Population standard deviation**

`SD_population = sqrt(sum((x_i - mean_token)^2) / N)`

The type-weighted dispersion uses the analogous formula over distinct entries.

## Coverage

**Ordinary lexical-token coverage**

`coverage = matched eligible lexical token occurrences / eligible lexical token occurrences`

**Content-focused coverage**

`content_coverage = matched eligible non-stopword token occurrences / eligible non-stopword token occurrences`

Phrase coverage counts unique covered token positions, so exploratory phrase-and-component double counting does not inflate the coverage numerator.

## Part-of-speech share

`POS_share_c = token occurrences assigned to category c / all eligible lexical token occurrences`

The combined corpus profile pools occurrences from all current works. A work-level profile uses only that work's denominator.

## Stopword sensitivity

`sensitivity = stopwords_excluded_value - all_matched_value`

## Cumulative normalized totals

**Rating total**

`rating_total = sum(x_i)`

**Above-midpoint load**

`above = sum(max(x_i - 0.5, 0))`

**Below-midpoint load**

`below = sum(max(0.5 - x_i, 0))`

**Net midpoint load**

`net = above - below = sum(x_i - 0.5)`

**Absolute midpoint load**

`absolute = above + below = sum(abs(x_i - 0.5))`

## Midpoint-centered contribution

`contribution_t = f_t * (x_t - 0.5)`

The leave-one-type-out mean change retained in the audit is:

`effect_t = mean_token - mean_token_without_all_occurrences_of_t`

## Corpus weighting

For eligible work `i`, let `m_i` be its token-weighted mean and `n_i` its included matched-observation count.

**Token-weighted volume profile**

`mean_volume_token = sum(m_i * n_i) / sum(n_i)`

**Equal-work-weighted volume profile**

`mean_volume_work = sum(m_i) / K`

where `K` is the number of eligible works with a nonmissing score.

**Reported divergence**

`divergence = mean_volume_work - mean_volume_token`

Works with no eligible score are omitted and counted; they are not assigned a neutral value.

## Emotion and sentiment association rates

For one category:

`rate_all_lexical = associated token occurrences / all eligible lexical tokens`

`rate_bearing = associated token occurrences / tokens bearing at least one positive association`

Because one token can belong to several categories, category rates need not sum to 100 percent. The eight emotions and positive/negative sentiment use the same formula but remain separately labeled constructs.

## Emotion intensity means

`intensity_mean_token = sum(supplied pair intensity for each matched occurrence) / matched pair occurrences`

`intensity_mean_type = sum(supplied pair intensity for distinct entry-category pairs) / distinct matched pairs`

Missing pairs do not enter either numerator or denominator.

## Worked synthetic example

Suppose normalized valence matches are `bright = 0.875` repeated ten times in one work and `dark = 0.250` once in a second work.

`token-weighted volume mean = (10 * 0.875 + 1 * 0.250) / 11 = 0.818181...`

`equal-work-weighted volume mean = (0.875 + 0.250) / 2 = 0.5625`

The divergence is substantial because the long work dominates the token-weighted view but receives only one work-level vote in the equal-work view.

# 13. Glossary

| Term | Meaning in VerseVAD |
|---|---|
| Affect match | A documented link between a token occurrence or phrase span and one lexicon entry |
| Analysis run | One immutable calculation with declared text version, lexicons, recipe, scenario, and software version |
| Analysis view | `all_matched` or `stopwords_excluded` |
| Arousal | Normative activation associated with a lexical item |
| Association | Binary lexicon membership for an emotion or sentiment category |
| Approved user mapping | Scenario-pinned link from a form to a verified exact source entry, applied only after ordinary matching fails |
| Coverage | Proportion of eligible token positions represented by included matches |
| Cumulative load | Length-sensitive sum of normalized lexical ratings or midpoint distances |
| Dominance | Normative control, power, or agency associated with a lexical item |
| Eligible token | A lexical token allowed into the matching denominator under the declared recipe |
| Exact match | Direct match from normalized surface form to a source entry |
| Exclude decision | Scenario decision that retains the candidate in the audit but omits it from that scenario's aggregates |
| Flag decision | Scenario decision that records concern without changing matching or scores |
| Lemma | Model-proposed base form conditioned on part of speech |
| Lemma-derived match | Match obtained from the lemma only after exact candidates fail |
| Lexicon entry | A word or phrase and its source-supplied value or association |
| Match observation | One included matched token occurrence or accepted phrase span |
| Normalized form | Separate processing form used for lookup; it does not replace the original text |
| Normalized VAD | Documented linear transformation to the common 0-1 display range |
| Phrase match | One accepted multi-token span linked to one source entry |
| Part-of-speech profile | Model-assigned grammatical counts and shares over all eligible lexical tokens, independent of lexicon coverage |
| Population SD | Dispersion of the complete selected matched set around its mean |
| Protected word | A word retained despite appearing in the underlying standard stopword list |
| Source value | The original value published by the lexicon |
| Review scenario | Named, versioned set of append-only decision revisions pinned to an analysis |
| Sentiment association | Broad positive or negative NRC Emotion label, reported separately from eight emotion categories |
| Stopword | A common function word selected for exclusion from the secondary aggregate under the active policy |
| Surface form | The exact form appearing in the preserved text |
| Token | One occurrence in the text |
| Token-weighted | Every included occurrence contributes |
| Universal POS tag | Coarse grammatical label such as NOUN, VERB, ADJ, or ADV generated by the installed model |
| Type | One distinct matched lexicon entry within the declared unit |
| Type-weighted | Every distinct matched entry contributes once |
| Unmatched | No accepted lexicon entry was assigned; the value remains missing |
| Valence | Normative pleasantness or unpleasantness associated with a lexical item |
| Work-weighted | Every eligible work-level mean contributes equally |

# 14. Troubleshooting and limitations

## Run the self-test

Under **Installation Check**, click **Run self-test** in the sidebar. A healthy installation reports `11/11 checks passed`. You can also double-click `diagnose_windows.bat`.

## Browser page shows old-code errors

Close older VerseVAD launcher windows and browser tabs, then restart with `start_versevad.bat`. A forced browser refresh or fresh private/incognito tab can clear stale page state. The application also contains a runtime revision guard for known stale-module problems.

## No matches or very sparse results

Confirm that the intended lexicon is selected, inspect unmatched vocabulary, and review phrase/matching methods. Do not interpret a missing result as neutral. Sparse warnings are prompts for caution, not automatic invalidation.

## File will not import

Confirm that it is a plain-text `.txt` file encoded as UTF-8 and within the displayed size limit. Word documents, PDFs, and rich-text files are not one-poem imports.

## Corpus comparison did not update

Only a complete batch becomes the latest comparison. Read the error, correct the input or configuration, and rerun the selected batch. An interrupted or failed batch does not overwrite the prior complete result.

## Lexicon Explorer returns no exact entry

Inspect separately labeled lemma, mapping, component, and suggestion sections. Similarity is not equivalence, and VerseVAD will not silently substitute a nearby word.

## Core methodological limitations

- Lexical norms are not contextual interpretations.
- Negation is flagged or protected but is not compositionally inverted.
- Irony, metaphor, voice, quotation, polysemy, and historical sense require close reading.
- Cross-lexicon normalization aligns scales but not study populations or procedures.
- Cumulative totals are not measured psychological load.
- Coverage is not accuracy.
- Descriptive agreement labels are not inferential reliability tests.
- Part-of-speech labels are model-generated and may be uncertain for poetic or historical language.
- Current corpus comparisons are descriptive and do not provide confidence intervals or hypothesis tests.
- Review mappings are scholar-authored scenario decisions, not source-published equivalences.
- Broad project or global review scopes require extra caution; prefer the narrowest defensible scope.

# 15. Reproducibility and updating this manual

Every analysis should retain the active lexicon, source checksum, adapter version, software version, preprocessing recipe, phrase policy, stopword policy, scenario, and inclusion decisions. Completed corpus runs remain linked to preserved text versions.

The companion definitions guide is maintained from:

`docs/VerseVAD_Values_and_Terminology_Guide_Source.md`

and generated as:

`docs/VerseVAD_Values_and_Terminology_Guide.docx`

This manual is maintained from:

`docs/VerseVAD_User_Manual_Source.md`

Rebuild it with:

`<bundled Python> scripts/build_user_manual.py`

The generated file is:

`docs/VerseVAD_User_Manual.docx`

When VerseVAD gains or changes a feature, update the Markdown source and rebuild, render, and visually inspect the Word file before treating the manual as current.

> FINAL READING RULE: Report the lexicon, result view, weighting, matched count, coverage, and relevant evidence with every numeric claim. Describe lexical norms and associations; reserve claims about meaning and experience for contextual scholarly argument.
