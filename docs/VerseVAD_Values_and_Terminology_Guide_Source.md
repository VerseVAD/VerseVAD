# VerseVAD Values and Terminology Guide

## Plain-language definitions, formulas, examples, and interpretation

**Software version:** {{VERSION}}  
**Guide updated:** {{DATE}}  
**Intended reader:** A first-time user with no linguistics or statistics background

> THE CENTRAL RULE: VerseVAD describes affective lexical evidence found in published word-rating resources. It does not discover the emotion of a poem, diagnose a speaker, recover an author's intention, or measure what an individual reader feels.

[[PAGEBREAK]]

# Contents at a Glance

1. The one-minute mental model
2. A safe reading order
3. Valence, arousal, and dominance
4. Original and normalized scales
5. Tokens, types, phrases, lemmas, and matches
6. Part-of-speech profiles
7. Coverage and unmatched vocabulary
8. Stopwords and the two VAD views
9. Token-weighted and type-weighted statistics
10. Means, medians, and dispersion
11. Stopword sensitivity
12. Cumulative normative lexical load
13. Top contributors
14. Emotion, sentiment, and emotion intensity
15. Corpus weighting and long works
16. Review decisions and scenarios
17. Worked examples
18. How to report a result
19. Quick-reference glossary

# 1. The One-Minute Mental Model

VerseVAD performs a documented lookup-and-summary procedure:

1. You provide a literary text.
2. VerseVAD preserves that text exactly.
3. It makes a separate processing representation containing tokens, normalized lookup forms, proposed lemmas, and phrase candidates.
4. It looks for those candidates in one or more installed lexicons.
5. A match inherits the value or association published for that lexicon entry.
6. VerseVAD summarizes only included matches and records everything needed to audit the calculation.
7. You interpret those lexical patterns alongside the original text.

A **lexicon** is a structured list of words or phrases with source-supplied ratings or category associations. A lexicon score belongs to the listed lexical entry under the conditions of the source study. It is not a contextual score freshly measured from your poem.

> EXAMPLE: If `storm` has high normative arousal in a selected lexicon, VerseVAD can report high-arousal lexical evidence when `storm` matches. It cannot determine whether the storm is literal, metaphorical, remembered, negated, mocked, or emotionally calming in this particular poem.

# 2. A Safe Reading Order

For every analysis, read the results in this order:

1. **Confirm the text and lexicons.** Make sure you analyzed the intended version and sources.
2. **Read coverage.** Determine how much eligible vocabulary was represented.
3. **Read warnings.** Note sparse evidence, lemma reliance, review exclusions, or other methodological cautions.
4. **Choose one construct.** VAD ratings, emotion associations, sentiment associations, and emotion intensities are different kinds of evidence.
5. **Choose one analysis view.** Compare all matched observations with stopwords excluded; do not merge them.
6. **Choose one weighting.** Token weighting answers a repetition-sensitive question; type weighting answers a vocabulary-sensitive question.
7. **Inspect dispersion and contributors.** A mean alone can conceal mixed ratings or one repeated influential word.
8. **Inspect the match evidence.** Verify surprising entries, phrases, lemmas, mappings, and unmatched forms in context.
9. **If analyzing a corpus, compare token- and work-weighted collection profiles.**
10. **Report the denominator and method with the result.**

> NEVER REPORT A BARE NUMBER: A result such as `valence = 0.62` is incomplete without the lexicon, scale, analysis view, weighting, matched count, coverage, and unit of analysis.

# 3. Valence, Arousal, and Dominance

Valence, arousal, and dominance are often abbreviated **VAD**. They are three separate dimensions. None is a synonym for “emotion.”

## Valence

**Valence** is normative pleasantness versus unpleasantness associated with a lexical item.

| Normalized location | Plain-language orientation |
|---|---|
| Near 0 | More unpleasant in the source norms |
| Near 0.5 | Near the documented scale midpoint |
| Near 1 | More pleasant in the source norms |

Possible interpretation: “The matched vocabulary has above-midpoint mean normative valence.”

Avoid: “The poem is happy.” A poem can use pleasant words ironically, quote them, negate them, or place them in a disturbing context.

## Arousal

**Arousal** is normative activation, alertness, energy, or intensity associated with a lexical item.

| Normalized location | Plain-language orientation |
|---|---|
| Near 0 | Calmer, quieter, or less activated in the source norms |
| Near 0.5 | Near the documented scale midpoint |
| Near 1 | More activated or energetic in the source norms |

Arousal is not the same as positive feeling. A pleasant word and an unpleasant word can both have high arousal.

Possible interpretation: “The included matched tokens have relatively high mean normative arousal.”

Avoid: “The reader becomes excited.” VerseVAD does not measure a reader.

## Dominance

**Dominance** is normative control, power, agency, or being-in-command associated with a lexical item.

| Normalized location | Plain-language orientation |
|---|---|
| Near 0 | Less control, power, or agency in the source norms |
| Near 0.5 | Near the documented scale midpoint |
| Near 1 | Greater control, power, or agency in the source norms |

Dominance does not identify who controls whom in a poem. Syntax, voice, narrative position, and context still require close reading.

Possible interpretation: “The matched vocabulary trends below the dominance midpoint.”

Avoid: “The speaker is powerless.”

## What a VAD Mean Actually Summarizes

A work-level VAD mean is the arithmetic mean of included lexicon ratings under a declared matching policy, analysis view, and weighting. It describes the center of those matched ratings. It does not summarize words that did not match, and it does not assign unmatched words a neutral value.

# 4. Original and Normalized Scales

The installed VAD lexicons use different original scales.

| Source | Original scale | VerseVAD normalized formula |
|---|---|---|
| Warriner VAD 2013 | 1 to 9 | `x_normalized = (x_original - 1) / 8` |
| NRC VAD v1 | 0 to 1 | `x_normalized = x_original` |
| NRC VAD v2.1 | -1 to 1 | `x_normalized = (x_original + 1) / 2` |

Normalization maps each documented minimum to 0, midpoint to 0.5, and maximum to 1. This lets VerseVAD display scales in a common numeric range.

Normalization does **not** prove that two sources are interchangeable. Lexicons may differ in vocabulary, participants, data-collection method, date, wording, and sample. VerseVAD therefore:

- preserves the original source value;
- displays the exact normalization formula;
- reports each lexicon separately;
- does not create a default cross-lexicon consensus score.

NRC VAD v1 and NRC VAD v2.1 are versions of one lexicon family, not fully independent replications.

# 5. Tokens, Types, Phrases, Lemmas, and Matches

## Token

A **token** is one occurrence in the text. In `dark dark night`, there are three lexical token occurrences: two occurrences of `dark` and one of `night`.

## Type

A **type** is one distinct matched lexicon entry within the declared unit of analysis. If both occurrences of `dark` match the same entry, `dark` contributes two tokens but one type.

## Surface Form

The **surface form** is what appears in the preserved text, such as `burning`.

## Normalized Form

The **normalized form** is a separate lookup representation produced by documented rules. It never replaces the original text.

## Lemma

A **lemma** is a model-proposed base form conditioned on part of speech, such as `burning -> burn`. VerseVAD tries a lemma only after the eligible exact candidates fail. A lemma-derived match is labeled because the proposal may be wrong for poetic, historical, ambiguous, or unusual language.

## Phrase

A **phrase match** links a multi-token span such as `broken heart` to one source entry. Under the recommended longest-phrase policy, the phrase contributes one observation and covered component candidates are suppressed but retained in the audit.

## Exact, Lemma-Derived, and Approved-Mapping Matches

| Match method | Meaning |
|---|---|
| Exact word | The normalized surface form directly matched a source entry |
| Exact phrase | The accepted multiword span directly matched a source entry |
| Possessive or apostrophe normalization | A conservative documented normalization matched |
| Lemma-derived | The model-proposed lemma matched only after exact candidates failed |
| Approved user mapping | A scenario-pinned review decision mapped the form to a verified exact source entry |

An approved mapping is not a published claim that the two forms are equivalent. It is a scholar-authored methodological decision, recorded with scope, rationale, revision, and scenario version.

# 6. Part-of-Speech Profiles

A **part of speech** is a grammatical category such as noun, verb, adjective, or adverb. VerseVAD uses the installed English linguistic model's universal POS labels.

The **Language Profile** is deliberately independent of the affective lexicons. Its denominator is every eligible lexical token, not only tokens that found a VAD or emotion entry.

VerseVAD reports two defensible levels:

- **Broad Categories** provide the readable quantity/share profile requested
  for interpretation.
- **Detailed Model Tags** preserve the installed model's Universal
  Dependencies distinctions and their separate counts and shares.

The broad and detailed shares each sum to 100 percent apart from rounding.
They are two aggregations of the same token occurrences and must not be added
together.

`POS_share_c = token occurrences assigned to category c / all eligible lexical token occurrences`

For each category, VerseVAD reports:

- the source POS tag or merged source tags;
- a plain-language category label;
- token count;
- share of all eligible lexical tokens;
- number of unique normalized types;
- example forms;
- the lexical-token denominator.

Common tags include:

| Source tag(s) | Plain-language category |
|---|---|
| NOUN + PROPN | Noun; common and proper nouns are combined |
| VERB + AUX | Verb; main, auxiliary, and copular uses are combined |
| ADJ | Adjective |
| ADV | Adverb |
| PRON | Pronoun |
| DET | Determiner |
| ADP | Preposition |
| CCONJ | Coordinating conjunction |
| SCONJ | Subordinating conjunction |
| PART | Particle |
| INTJ | Interjection |
| NUM | Numeral |
| X | Other or uncertain |

In a one-poem result, shares use that poem's lexical-token count. In the corpus **All Works Combined** profile, counts are pooled across current work versions, so longer works contribute more. The work-by-work table uses each work's own denominator and is usually better for comparing relative grammatical composition across differently sized works.

Part-of-speech assignments are model-generated rather than lexicon-published. Poetic syntax, fragments, archaisms, unusual capitalization, and deliberate ambiguity can cause errors. Inspect token evidence when a category distinction matters to the argument.

VerseVAD intentionally merges the model's `NOUN` and `PROPN` tags into one
displayed **Noun** category. Capitalization is unusually variable in poetry,
and the common/proper distinction is not necessary for the requested
quantity/share profile. The original source tag remains available in
the detailed model-tag table, token-level evidence, and audit data.

VerseVAD also merges `VERB` and `AUX` into one displayed **Verb** category.
Forms of `be`, such as `was`, may receive `AUX` when they function as an
auxiliary or copula; they are still verbs in the beginner-facing quantity/share
profile. The original tag remains in token evidence.
The detailed model-tag table still reports `VERB` and `AUX` separately.

# 7. Coverage and Unmatched Vocabulary

**Coverage** asks how much eligible vocabulary was represented by the selected lexicon under the declared policy.

`coverage = matched eligible lexical token positions / eligible lexical token positions`

Coverage is not:

- an accuracy score;
- the proportion of the poem that is emotional;
- the proportion of words the software understands;
- evidence that a high-coverage lexicon is universally better.

Report both the percentage and its counts. `80% coverage (80 of 100 eligible lexical token positions)` is more informative than `80%`.

## Unmatched

An **unmatched** token received no accepted entry. Its rating remains missing. VerseVAD never gives it 0, 0.5, the work mean, or an automatically guessed synonym.

Unmatched vocabulary is a quality-control resource. It can reveal:

- spelling or OCR problems;
- contractions and archaic forms;
- names and places;
- specialist vocabulary;
- poetic compounds;
- inflections missed by lemmatization;
- genuine limits in source coverage.

## Review Exclusions and Coverage

A review exclusion says that a published candidate should not contribute to a chosen scenario. The candidate remains auditable. Primary coverage can still identify it as published lexical evidence while separately reporting that the review scenario excluded it from aggregation. Always read coverage together with review-exclusion counts.

# 8. Stopwords and the Two VAD Views

## Stopword

A **stopword** is a common function word selected for exclusion from the secondary content-focused aggregate under the active policy. Examples in general-purpose lists can include articles, prepositions, pronouns, auxiliaries, and conjunctions.

“Stopword” does not mean meaningless. Function words can be central to rhythm, voice, negation, syntax, deixis, and style. That is why VerseVAD preserves:

- **All Matched Observations:** every included lexicon match.
- **Stopwords Excluded:** the same matches after the recorded stopword policy removes selected observations from the secondary aggregate.

The all-matched result is never destroyed.

## Protected Words

VerseVAD protects a documented set of negations, modals, comparatives, and intensifiers from default exclusion. Examples include `not`, `never`, `no`, `without`, `might`, `more`, `most`, `too`, and `very`.

## Custom Stopword

A **custom stopword** is a word the user deliberately adds to the active stopword list for a specific analytical purpose. For example, adding `raven` would make matches to `raven` absent from the stopword-excluded aggregate while preserving them in the all-matched result and audit.

This is a methodological decision, not a declaration that the word is universally unimportant.

## Content-Focused Coverage

`content_coverage = matched eligible non-stopword token positions / eligible non-stopword token positions`

Content-focused coverage belongs to the stopword-excluded view. It should not be substituted silently for ordinary coverage.

# 9. Token-Weighted and Type-Weighted Statistics

## Token-Weighted

In a **token-weighted** statistic, every included occurrence contributes.

`mean_token = sum(x_i) / N`

where `x_i` is the rating of included occurrence `i` and `N` is the number of included matched observations.

Question answered: “What affective ratings does a reader encounter across the matched words and accepted phrases, including repetition?”

Use token weighting when repetition and textual exposure matter.

## Type-Weighted

In a **type-weighted** statistic, every distinct matched lexicon entry contributes once.

`mean_type = sum(x_t) / T`

where `x_t` is the rating for distinct matched entry `t` and `T` is the number of distinct included matched entries.

Question answered: “What is the profile of the distinct matched vocabulary inventory if repeated entries count only once?”

Use type weighting to reduce the influence of repetition.

## Interpreting Their Difference

If token- and type-weighted means are close, repetition changes the reported center little. If they diverge, repeated entries shift the token-weighted profile away from the distinct-vocabulary profile.

Neither weighting is automatically superior. They answer different questions and should be named explicitly.

# 10. Means, Medians, and Dispersion

## Mean

The **mean** is the arithmetic average of the included values.

`mean = sum(values) / number_of_values`

A mean identifies a center. It does not show whether the values cluster tightly or contain strong values on both sides.

## Median

The **median** is the middle value after sorting. For an even number of values, it is the mean of the two middle values. It is less sensitive than the mean to a small number of extreme values.

## Dispersion of Matched Ratings

**Dispersion** describes how spread out the included matched ratings are around their center.

VerseVAD reports **population standard deviation** for the complete selected matched set:

`SD_population = sqrt(sum((x_i - mean)^2) / N)`

A standard deviation near 0 means the included ratings are tightly clustered. A larger standard deviation means they are more dispersed.

On the normalized 0-to-1 scale, possible population SD values are bounded, but there is no universal literary threshold for “small” or “large.” Compare like with like: same construct, lexicon, scale, view, weighting, and unit of analysis.

## What Dispersion Does Not Mean

Work-level dispersion is not:

- the uncertainty of the work mean;
- a confidence interval;
- statistical significance;
- disagreement among lexicon raters;
- ambiguity in the poem.

Lexicon Explorer may show a **source-provided standard deviation** for one Warriner entry. That value describes participant variation around that entry's source mean. It is a different quantity from dispersion across the matched entries in one poem.

# 11. Stopword Sensitivity

**Stopword sensitivity** reports how much a statistic changes when moving from all matched observations to the stopword-excluded view.

`sensitivity = stopwords_excluded_value - all_matched_value`

| Sign | Meaning |
|---|---|
| Positive | The stopword-excluded statistic is higher |
| Negative | The stopword-excluded statistic is lower |
| Near zero | That statistic changes little under this policy |

Use the signed result, its absolute size, the active stopword policy, and both underlying values.

There is no universal threshold at which a difference becomes “robust,” “significant,” or “important.” Stopword sensitivity is a descriptive comparison, not an inferential test.

# 12. Cumulative Normative Lexical Load

**Cumulative normative lexical load** is VerseVAD's length- and repetition-sensitive family of sums over included normalized ratings. Longer works and repeated matches can accumulate larger totals.

The word **load** here means an accumulated numeric total. It does not mean experimentally measured cognitive load, emotional burden, or effect on a reader.

Let `x_i` be an included normalized rating and let the normalized midpoint be 0.5.

## Rating Total

`rating_total = sum(x_i)`

The rating total adds the normalized source ratings. It grows with the number of included matches and their rating levels. Because its zero is the bottom of the normalized scale rather than the midpoint, it is usually less interpretable than the midpoint-centered loads.

## Above-Midpoint Load

`above = sum(max(x_i - 0.5, 0))`

This adds only distances above the midpoint. Values at or below 0.5 contribute zero.

For valence, it summarizes accumulated above-midpoint pleasantness ratings. For arousal, it summarizes accumulated above-midpoint activation ratings. For dominance, it summarizes accumulated above-midpoint control or agency ratings.

## Below-Midpoint Load

`below = sum(max(0.5 - x_i, 0))`

This adds only distances below the midpoint and reports the amount as a positive magnitude. Values at or above 0.5 contribute zero.

For valence, it summarizes accumulated below-midpoint unpleasantness distance. For arousal, it summarizes accumulated below-midpoint calmness or lower activation distance. For dominance, it summarizes accumulated below-midpoint lower control or agency distance.

## Net Midpoint Load

`net = above - below = sum(x_i - 0.5)`

Positive net load means above-midpoint distances outweigh below-midpoint distances. Negative net load means below-midpoint distances outweigh above-midpoint distances. A value near zero can mean ratings cluster near 0.5, or that strong positive and negative distances cancel. Read it with absolute load and dispersion.

## Absolute Midpoint Load

`absolute = above + below = sum(abs(x_i - 0.5))`

Absolute load adds distance from the midpoint regardless of direction. A larger value means more accumulated off-midpoint lexical evidence, produced by text length, repetition, stronger distances, or some combination.

## How to Compare Cumulative Loads

Use cumulative loads when length and repetition are part of the research question. For works of radically different lengths:

- report matched observations or lexical-token count;
- do not treat a larger load as automatically more intense;
- compare means alongside cumulative totals;
- consider a per-token statistic if the question requires length adjustment;
- compare the same lexicon, dimension, view, and matching policy.

# 13. Top Contributors

Top contributors identify distinct matched entries that pull a token-weighted mean above or below the normalized midpoint.

`contribution_t = frequency_t * (rating_t - 0.5)`

| Contribution | Meaning |
|---|---|
| Positive | The entry contributes above the midpoint |
| Negative | The entry contributes below the midpoint |
| Larger absolute value | Greater combination of repetition and midpoint distance |

A contributor can rank highly because it is repeated, because its rating is far from 0.5, or both.

VerseVAD also retains a leave-one-type-out effect:

`effect_t = mean_token - mean_without_all_occurrences_of_t`

This describes how much the reported token mean changes if every occurrence of that matched type is omitted. It is descriptive and is not a causal effect.

# 14. Emotion, Sentiment, and Emotion Intensity

## Eight Emotion Associations

NRC Emotion provides binary associations for:

- anger;
- anticipation;
- disgust;
- fear;
- joy;
- sadness;
- surprise;
- trust.

An association means the source marks the entry as associated with that category. It is not a probability, intensity, or contextual diagnosis.

`emotion_rate = associated token occurrences / eligible lexical tokens`

One entry can carry several associations, so the eight rates do not need to sum to 100 percent.

## Positive and Negative Sentiment Associations

Positive and negative are broad **sentiment** labels in NRC Emotion. VerseVAD reports them in a separate section from the eight emotion categories.

They use the same occurrence-counting logic:

`sentiment_rate = associated token occurrences / eligible lexical tokens`

Positive and negative are not endpoints of the VAD valence scale, and they are not replacements for the eight emotions. A source entry can have multiple labels; rates need not sum to 100 percent.

## Emotion Intensity

NRC Emotion Intensity provides numeric values only for particular word-emotion pairs.

**Prevalence** asks how often supplied pairs occur:

`prevalence = matched pair occurrences / eligible lexical tokens`

**Token-weighted mean intensity** averages the supplied values across matched occurrences:

`intensity_mean_token = sum(pair intensity for each occurrence) / matched pair occurrences`

**Type-weighted mean intensity** averages distinct entry-category pairs once:

`intensity_mean_type = sum(distinct supplied pair intensities) / distinct matched pairs`

An absent word-emotion pair is missing. VerseVAD does not turn absence into zero intensity.

# 15. Corpus Weighting and Long Works

Corpus collections can contain radically different work lengths. VerseVAD therefore reports two collection profiles.

## Token-Weighted Collection Profile

Every included matched observation receives equal weight. Long works contribute more because they contain more of the analyzed volume.

For eligible work `i`, let `m_i` be its token-weighted mean and `n_i` its included matched count:

`mean_collection_token = sum(m_i * n_i) / sum(n_i)`

Question answered: “What matched affective vocabulary does a reader encounter across all included observations in this collection?”

## Work-Weighted Collection Profile

Every eligible work-level token mean receives equal weight:

`mean_collection_work = sum(m_i) / K`

where `K` is the number of works with a nonmissing eligible score.

Question answered: “What is the average work-level profile when each work contributes equally?”

## Divergence

`divergence = mean_collection_work - mean_collection_token`

A divergence shows that work length changes the collection-level result. Report both profiles for mixed-length collections. Works without an eligible score remain missing and are counted; they are never assigned 0.5.

# 16. Review Decisions and Scenarios

Phase 5 review tools let a scholar document and test explicit alternatives without overwriting the baseline.

## Flag

A **flag** marks an occurrence or form for attention. It does not change matching or scores.

## Exclude

An **exclude** decision preserves the candidate in the audit but prevents it from contributing to the selected scenario's aggregate.

## Map

A **map** decision maps a source form to a verified exact entry in one installed lexicon. Mapping occurs only after exact, possessive/apostrophe, and lemma candidates fail. It is labeled `approved_user_mapping`.

## Scope

| Scope | Where the decision applies |
|---|---|
| Occurrence | One recorded token position in one preserved text version |
| Work | Eligible occurrences in the selected preserved work |
| Project | Eligible occurrences across works in the selected project |
| Global within scenario use | Eligible occurrences wherever that scenario is evaluated |

Broader scope carries greater methodological risk. Use the narrowest defensible scope.

## Scenario

A **review scenario** is a named, versioned set of decision revisions. A scenario version is pinned to an analysis run. Editing, revoking, restoring, or restoring an older snapshot creates a new version; it does not rewrite a completed run.

## Safe Review Workflow

1. Run an unreviewed baseline.
2. Open **Review & Scenarios**.
3. Create a clearly named scenario.
4. Inspect the evidence, context, match method, lexicon, and candidate risk.
5. Choose flag, exclude, or map.
6. Use the narrowest defensible scope.
7. Write a rationale another scholar could evaluate.
8. Rerun the corpus with that exact scenario version.
9. Compare the new immutable batch with the baseline.
10. Export the workbook and retain the **Review Decisions** sheet and methodology.

An unmatched-note proposal is documentation only. Only an active, scenario-pinned mapping decision changes an analysis.

# 17. Worked Examples

## Example A: Token and Type Weighting

Suppose a text has these included normalized valence matches:

`bright = 0.8, bright = 0.8, dark = 0.2`

Token-weighted mean:

`(0.8 + 0.8 + 0.2) / 3 = 0.6`

Type-weighted mean:

`(0.8 + 0.2) / 2 = 0.5`

Interpretation: repetition of `bright` shifts the occurrence-sensitive token mean above the distinct-vocabulary mean.

## Example B: Dispersion

For the token values `0.8, 0.8, 0.2`, the token mean is `0.6`.

`SD = sqrt(((0.8 - 0.6)^2 + (0.8 - 0.6)^2 + (0.2 - 0.6)^2) / 3)`

`SD = sqrt((0.04 + 0.04 + 0.16) / 3) = sqrt(0.08) = approximately 0.283`

Interpretation: the matched values are meaningfully spread around the mean in this small synthetic example. Do not treat `0.283` as an uncertainty estimate.

## Example C: Cumulative Load

For `0.8, 0.8, 0.2`:

`rating_total = 1.8`

`above = (0.8 - 0.5) + (0.8 - 0.5) = 0.6`

`below = (0.5 - 0.2) = 0.3`

`net = 0.6 - 0.3 = 0.3`

`absolute = 0.6 + 0.3 = 0.9`

Interpretation: above-midpoint distance outweighs below-midpoint distance by 0.3, while total off-midpoint distance is 0.9. The numbers are lexical sums, not a measured reader response.

## Example D: Stopword Sensitivity

Suppose all-matched token-weighted arousal is `0.48` and stopwords-excluded arousal is `0.54`.

`sensitivity = 0.54 - 0.48 = +0.06`

Interpretation: under this recorded stopword policy, the content-focused arousal mean is 0.06 higher on the normalized scale. The calculation alone does not establish whether that difference is substantively important.

## Example E: Corpus Weighting

One long work has 100 included matches and mean valence `0.70`. One short work has 10 included matches and mean valence `0.30`.

`token-weighted collection mean = ((100 * 0.70) + (10 * 0.30)) / 110 = approximately 0.664`

`work-weighted collection mean = (0.70 + 0.30) / 2 = 0.50`

Interpretation: the long work dominates the token-weighted profile. The work-weighted profile gives both works one vote. The difference is part of the finding.

## Example F: What a Complete Interpretation Looks Like

Better report:

“Using NRC VAD v2.1 on the normalized 0-to-1 scale, the all-matched token-weighted mean normative valence was 0.61 across 84 included observations, with 78% lexical-token coverage. The type-weighted mean was 0.54, indicating that repetition shifted the occurrence-sensitive profile upward. Population SD was 0.19. The largest above-midpoint contributors were `bright` and `love`; the strongest below-midpoint contributor was `death`. These are normative lexical patterns rather than a determination of the poem's emotional state.”

Incomplete report:

“The poem's valence is 0.61, so it is positive.”

# 18. How to Report a Result

Include these elements for every numeric claim:

- text, work, or collection being analyzed;
- exact lexicon and version;
- original or normalized scale;
- construct: VAD, emotion association, sentiment association, or emotion intensity;
- analysis view: all matched or stopwords excluded;
- weighting: token, type, token-weighted collection, or work-weighted collection;
- phrase policy when relevant;
- matched observations or relevant denominator;
- coverage;
- scenario name and exact scenario version if reviewed;
- statistic and value;
- dispersion when relevant;
- influential contributors or unmatched limitations;
- a lexical-evidence caution.

## Reporting Template

“Using **[lexicon and version]**, **[text or collection]** had **[statistic] = [value]** for **[construct/dimension]** on the **[scale]**, using **[analysis view]** and **[weighting]** across **[matched count/denominator]**, with **[coverage]** coverage. **[Dispersion, contributors, sensitivity, or corpus divergence]**. The result describes matched normative lexical evidence and is interpreted alongside the text.”

# 19. Quick-Reference Glossary

| Term | Plain-language meaning in VerseVAD |
|---|---|
| Affective lexicon | A source list connecting words or phrases to ratings or associations |
| Analysis run | One immutable calculation tied to exact inputs and methods |
| Analysis view | All matched observations or stopwords excluded |
| Arousal | Normative activation or energy associated with a lexical item |
| Association | Binary source label linking an entry to an emotion or sentiment |
| Coverage | Share of eligible lexical token positions represented by matches |
| Cumulative normative lexical load | Length- and repetition-sensitive sums of normalized ratings or midpoint distances |
| Dominance | Normative control, power, or agency associated with a lexical item |
| Eligible token | Lexical token allowed into the denominator under the declared recipe |
| Exclude decision | Scenario decision that retains evidence but omits it from aggregation |
| Flag decision | Scenario note that does not alter a score |
| Lemma | Model-proposed base form conditioned on part of speech |
| Map decision | Scenario decision linking a form to a verified exact source entry |
| Match observation | One included token occurrence or accepted phrase span |
| Mean | Arithmetic average |
| Median | Middle sorted value |
| Normalized VAD | Documented linear transformation to the common 0-to-1 display range |
| Part-of-speech profile | Model-assigned grammatical counts and shares over all eligible lexical tokens |
| Phrase match | Multi-token span linked to one source entry |
| Population standard deviation | Spread of the complete selected value set around its mean |
| Review scenario | Named, versioned set of scholar-authored decision revisions |
| Sentiment | Broad positive or negative source association, reported separately from eight emotions |
| Source value | Original value published by one lexicon |
| Stopword | Common function word selected for exclusion from the secondary aggregate |
| Stopword sensitivity | Stopwords-excluded result minus all-matched result |
| Surface form | Exact form in the preserved text |
| Token | One occurrence in the text |
| Token-weighted | Every included occurrence contributes |
| Type | One distinct matched lexicon entry in the declared unit |
| Type-weighted | Every distinct matched entry contributes once |
| Unmatched | No accepted entry; value remains missing |
| Source POS tag(s) | Model-generated grammatical tag; displayed Noun merges NOUN/PROPN and Verb merges VERB/AUX |
| Valence | Normative pleasantness or unpleasantness associated with a lexical item |
| Work-weighted | Every eligible work-level mean contributes equally |

> FINAL CHECK: If you cannot identify the lexicon, scale, view, weighting, denominator, coverage, and scenario behind a number, return to the result or export before interpreting it.
