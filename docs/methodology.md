# Methodological Commitments

## What VerseVAD measures

VerseVAD will describe the distribution of text tokens and phrases that match
entries in selected affective lexicons. Depending on the resource, an entry may
carry normative valence, arousal, and dominance ratings; categorical emotion or
sentiment associations; or emotion-intensity ratings.

These measurements describe lexical associations under a documented matching
policy. They do not establish the emotion of a poem, the state of a speaker,
the experience of a reader, or an author's intention.

## Units that must remain distinct

- The preserved original is the text supplied by the scholar.
- A text version is one immutable state of that original.
- A token occurrence has a position, structure, context, and surface form.
- A normalized form is a separate processing representation.
- A lemma is a model-assisted base form conditioned on part of speech.
- A lexicon entry is an independently sourced word or phrase with source data.
- A match links an occurrence or span to an entry and records how it matched.
- An aggregate summarizes included matches for a declared analysis scenario.
- Literary interpretation remains a scholarly act outside the numeric score.

## Provisional default recipe

The default recipe for implementation and testing is:

1. preserve the original text and its line and stanza boundaries;
2. create a Unicode-normalized processing representation without overwriting
   the original;
3. retain capitalization but perform case-insensitive lexicon lookup;
4. exclude punctuation from numeric summaries while keeping it in the audit;
5. attempt exact normalized surface-form matches first;
6. apply conservative apostrophe and possessive normalization;
7. prefer the longest exact phrase when the selected adapter supports phrases;
8. use POS-sensitive lemma fallback only after exact candidates fail;
9. use reviewed mappings only when their scope and approval allow it;
10. do not stem, guess historical substitutions, or infer coined-word meanings;
11. do not automatically invert scores near negation;
12. retain all matched observations as the complete lexical-evidence view;
13. also calculate a separately labeled, auditable stopword-excluded view;
14. report token- and type-weighted summaries separately;
15. show matched counts and coverage with every aggregate;
16. preserve all candidate, suppression, exclusion, and match provenance.

This recipe will be versioned. Changes create new analyses rather than altering
completed results.

## Shared poetry-preserving processing

The one-poem workspace creates one immutable `PoemDocument` and reuses its
exact token records for every selected lexicon. This prevents source-specific
analyses in one request from drifting because of repeated tokenization or
model processing.

The shared representation retains two distinct structural layers:

- an exact section, physical lines, and stanza groupings derived from preserved
  characters, blank lines, indentation, and line endings; and
- model sentence and dependency structures, including flags when they cross a
  poetic line or stanza boundary.

Neither layer overwrites the other. NFC normalization is used only for the
separate lookup representation. Original capitalization and punctuation stay
in source/token audit fields. Lemma, part of speech, morphological features,
sentence boundaries, dependencies, and optional named entities remain
model-generated proposals that can be uncertain for poetic, historical,
dialectal, fragmented, or ambiguous language.

The configuration explicitly groups POS tags as content, function, other, or
non-lexical and records hyphenated expressions, contractions, and apostrophe
forms as exact spans over their retained token components. Named-entity
recognition is disabled by default; enabling it changes the configuration
identity.

Processing coverage is separate from affective-lexicon or other research-
resource coverage. The pinned small English model has no usable vector
vocabulary, so its model-OOV count and rate remain missing. This does not make
tokens neutral and does not say whether they match a lexicon or the planned
local SUBTLEX-US frequency resource. Dependency confidence also remains
missing because the pipeline does not provide a calibrated per-edge value.

## VAD summaries

Token-weighted summaries count every included occurrence. Type-weighted
summaries count each unique matched lexicon entry once within the declared unit.
Unmatched tokens are absent from the numeric mean; they are not assigned 0,
0.5, or another neutral value.

Cross-scale comparison may use a separate normalized score when the adapter's
source scale supports a documented linear transformation. Original scores and
source limits always remain available.

Phase 3 implements these derived transformations:

- Warriner VAD 1-9: `(x - 1) / 8`;
- NRC VAD v1 0-1: identity (`x`);
- NRC VAD v2.1 -1 to 1: `(x + 1) / 2`.

They align each documented minimum, midpoint, and maximum to a common 0-1
display range. They do not make the source vocabularies, sampling designs, or
lexicon versions interchangeable. Comparisons therefore remain source-specific
and appear with coverage and matched counts. Original values are retained, and
VerseVAD creates no pooled or consensus VAD score.

Categorical emotion associations and numeric word-emotion intensities are not
alternate scales for VAD. They retain their own value kinds and denominators
and are never normalized into or averaged with the VAD dimensions.

## Normative lexical concreteness

The optional Stage 2 module reads the user-supplied Brysbaert, Warriner, and
Kuperman (2014) workbook in place and retains its original 1-5 ratings. It uses
the same shared token and poetic-structure record as the affective analysis but
remains a separate construct and result.

Eligible lexical tokens are matched longest exact two-word expression first,
then exact normalized surface form, lemma, and a documented conservative
apostrophe/possessive fallback. Exact surface evidence always precedes lemma
evidence. Punctuation remains auditable but ineligible. Model-tagged proper
nouns are excluded by default, with an explicit configurable policy.

For a source-supplied two-word expression, VerseVAD assigns the expression's
rating to each covered token position for the declared token-weighted
statistics. The token rows share one group identity so this assignment remains
visible. Repetition contributes repeatedly.

The module reports the mean, median, inclusive quartiles, interquartile range,
and population standard deviation among rated tokens, plus token and unique
normalized-surface-type coverage. Empty denominators remain missing. Wholly
unmatched eligible texts have zero coverage and missing rating aggregates.

The default lower band at 2.0 and upper band at 4.0 are configurable VerseVAD
orientation aids. They are not source-published diagnostic categories. Results
must be described as normative lexical concreteness evidence, not imagery
quality, readability, cognition, or a declaration that a poem is concrete or
abstract. See
[`poetic-fingerprint-stage2.md`](poetic-fingerprint-stage2.md).

## Corpus-relative lexical frequency and rarity

The optional Stage 3 module reads the pinned official SUBTLEX-US workbook in
place and retains its published word-form counts, contextual-diversity fields,
and Zipf values. It remains separate from affective ratings and concreteness.
No `wordfreq` or alternate corpus value is substituted.

By default, every lexical token is eligible except model-tagged proper nouns.
Punctuation, numbers, and other non-lexical tokens remain in the audit but
outside the denominator. The optional, non-default **Content words only**
scope restricts eligibility to exact model tags `NOUN`, `VERB`, `ADJ`, and
`ADV`. It excludes determiners (`DET`), adpositions/prepositions (`ADP`),
coordinating and subordinating conjunctions (`CCONJ`, `SCONJ`), pronouns
(`PRON`), auxiliaries (`AUX`), punctuation, and every other tag. `PROPN`
remains excluded under the default proper-name policy.

This strict scope must not be confused with the broad Language Profile:
the latter groups `VERB` and `AUX` together under **Verb** for a readable
quantity/share view, whereas the frequency restriction deliberately excludes
`AUX`. Both rely on model-generated POS tags that can be uncertain in poetry.

Matching uses exact normalized observed word form first, then an explicitly
enabled normalized lemma only when the observed form is absent, followed by
documented conservative apostrophe or possessive fallbacks. An exact form is
never replaced by a lemma. Unmatched and ineligible tokens have missing
frequency values rather than zero.

The token-weighted median Zipf value is the primary summary. The module also
reports the mean, population standard deviation, inclusive quartiles, IQR,
range, configurable bands, token and unique observed-form-type coverage,
physical-line/stanza/POS summaries, term rankings, and a complete audit.
Repetition contributes repeatedly. Empty denominators remain missing.

Zipf is logarithmic: about one point represents a tenfold corpus-frequency
difference. The default rare-to-very-common bands are configurable VerseVAD
orientation aids, not source-published literary categories. Results must be
described as corpus-relative lexical frequency evidence from an American
subtitle corpus, not difficulty, sophistication, accessibility, intelligence,
literary quality, or reader response. See
[`poetic-fingerprint-stage3.md`](poetic-fingerprint-stage3.md).

## Retrospective normative lexical Age of Acquisition

The optional Stage 4 module reads the pinned official Kuperman,
Stadthagen-Gonzalez, and Brysbaert supplement in place. Its numeric values are
adult retrospective estimates of the age, in years, at which a source
respondent believed they had learned a word well enough to understand it.
They remain separate from affect, concreteness, frequency, difficulty, grade
level, familiarity, comprehension, intelligence, and reader response.

By default, every lexical token is eligible except model-tagged proper nouns.
The optional, non-default **AoA content words only** scope restricts
eligibility to exact contextual model tags `NOUN`, `VERB`, `ADJ`, and `ADV`.
The paper describes its target selection as base forms used most frequently
as nouns, verbs, or adjectives, but the official supplement also contains
numeric ratings for polyfunctional spellings such as `the`, `and`, `he`, `of`,
and `to`. Source-list construction and the contextual use of a spelling in a
poem are therefore kept distinct.

Matching uses exact normalized observed form first, then an explicitly enabled
model lemma only when no exact form exists, followed by documented conservative
apostrophe or possessive fallbacks. A source row whose mean is `NA` remains
auditable but missing, as does every unmatched or ineligible token. No missing
value becomes age zero or a neutral age.

The module reports token-weighted mean, median, population standard deviation,
inclusive quartiles, IQR, range, configurable early/middle/later orientation
bands, token and unique observed-form-type coverage, physical-line/stanza/POS
summaries, represented-term rankings, source-response evidence, and a complete
audit. The default early-at-or-below-5 and later-at-or-above-12 thresholds are
VerseVAD orientation aids, not source-published categories.

When Frequency or Concreteness is enabled in the same One Poem run, the module
may report a descriptive Spearman relationship after collapsing repeated
occurrences to unique normalized surface types. It requires at least three
paired types and excludes multiword concreteness assignments. The coefficient
does not establish causation or a reader effect.

Results must be described as retrospective normative lexical AoA evidence
among matched tokens. They are not diagnostic of cognitive impairment or
decline. See
[`poetic-fingerprint-stage4.md`](poetic-fingerprint-stage4.md).

## Part-of-speech profile

The linguistic profile is independent of lexicon matching. It counts every
eligible lexical token assigned to each universal part-of-speech category by
the pinned English model:

`POS share = category token occurrences / all eligible lexical token occurrences`

One-poem shares use that text's denominator. The combined corpus profile pools
occurrences from current work versions, while the work-by-work table uses each
work's own denominator. Counts, shares, unique normalized types, examples,
model name, and model version remain visible. These model-generated labels can
be uncertain for poetic syntax, archaisms, fragments, and ambiguity.

Two aggregations are reported from the same token records. The broad profile
merges selected tags for readable description. The detailed profile preserves
the model's individual Universal Dependencies tags, counts, and shares. Both
use the same lexical-token denominator and each separately sums to one apart
from display rounding.

For the displayed quantity/share profile, VerseVAD merges source tags `NOUN`
and `PROPN` into one **Noun** category. The original token tag remains in the
audit. Source tag `ADP` is labeled **Preposition** in beginner-facing output;
it remains distinct from `ADV` (**Adverb**).

Source tags `VERB` and `AUX` are likewise merged into **Verb**. This retains
forms of `be` and other auxiliary/copular uses in the broad verb quantity
requested by the user while preserving their original tags in token evidence.

## Dual VAD reporting and stopword policy

VerseVAD does not treat stopword removal as neutral preprocessing. Every VAD
analysis keeps the complete **all matched observations** result and derives a
second **stopwords excluded** result from the same audited matches. The second
view changes aggregate inclusion only; it does not change tokenization,
lexicon lookup, exact-versus-lemma priority, or source ratings.

The standard list is spaCy English `STOP_WORDS`, pinned to the installed spaCy
version and identified by its full active-list SHA-256 hash. VerseVAD protects
meaning-changing negations, modals, comparatives, and intensifiers—including
`no`, `not`, `never`, `without`, `may`, `might`, `must`, `more`, `most`, `too`,
and `very`—from default exclusion. A scholar may add or remove normalized forms
in custom mode; the full resulting list and the changes are recorded with the
analysis.

Recognition may use the normalized surface form or lemma and records which
evidence caused exclusion. This does not silently turn a lemma into a lexicon
match. An activated exact published phrase remains one match and is retained
intact rather than being split because one component is a stopword.

Full-view coverage keeps the ordinary eligible lexical-token denominator.
Content-focused coverage uses eligible non-stopword tokens as its denominator
and reports excluded matched observations separately. Stopword sensitivity is
the stopwords-excluded statistic minus the corresponding all-matched statistic;
it is descriptive rather than a robustness threshold.

Top-contributor tables remain separate by view. A matched entry's signed
midpoint contribution for one dimension is:

`frequency × (normalized rating - 0.5)`

Positive values raise the cumulative midpoint-centered total; negative values
lower it. The ranking is an accounting of normative lexical evidence, not a
claim about causal reader response.

## Emotion and sentiment association summaries

NRC Emotion Lexicon values are binary associations, not intensities. A term may
belong to multiple categories, so category percentages need not total 100%.
Every percentage will state its denominator.

VerseVAD reports the eight emotion categories—anger, anticipation, disgust,
fear, joy, sadness, surprise, and trust—separately from the source's broad
positive and negative sentiment labels. Both constructs use the same documented
association-counting calculations, but the interface and readable summary keep
their headings distinct.

Phase 2 reports, for every association, occurrence count, unique matched entry
count, rate per all lexical tokens, rate among tokens bearing at least one
positive association, rate per unique lexical surface type, line and stanza
distributions, and frequent contributing terms. A source term present in the
word-level lexicon but carrying no positive category association can count as a
lexicon match for coverage but not as an emotion-bearing token.

## Emotion intensity summaries

Prevalence and intensity answer different questions and remain separate:

- prevalence describes how often matched emotion-associated vocabulary occurs;
- mean intensity summarizes source intensities only among entries matched for
  that emotion.

A token without a score for an emotion is not an intensity-zero observation in
the primary mean.

Phase 2 defines a matched word-emotion pair as one distinct matched lexicon
entry and category. Matched token occurrences repeat when the same entry occurs
more than once. The token-weighted intensity mean repeats those occurrences;
the type-weighted mean uses each matched entry-category pair once. Prevalence is
the category's matched occurrences divided by all lexical tokens or by tokens
matched anywhere in the intensity lexicon, as labeled.

## Phrase policies

NRC VAD v2.1 explicitly supplies unigrams and multiword expressions. Phase 2
normalizes exact surface tokens, constructs candidates within a single poetic
line without crossing punctuation, orders candidates by descending token length
and then textual position, and greedily selects non-overlapping spans.

The three policies are:

- `phrase_preferred`: selected phrases contribute one summary observation;
  component candidates remain visible but suppressed;
- `unigram_only`: phrase entries are ignored and unigram matching proceeds as in
  Phase 1;
- `phrase_and_component_exploratory`: selected phrases and independently matched
  components both contribute, with a warning that this intentionally
  double-counts the span.

Shorter or equal-length phrase candidates that overlap selected spans remain in
the audit as suppressed overlaps. Coverage counts unique lexical token
occurrences covered by included records, so exploratory double-counting does
not inflate the matched-token numerator. A selected phrase contributes one VAD
observation even when it covers multiple tokens.

The local policy activates Warriner's 102 and NRC VAD v1's 132
whitespace-containing source rows as exact phrase candidates at the user's
request. They use the same longest-first selection and visible suppression
records as NRC VAD v2.1. This is a declared VerseVAD processing policy; it does
not claim that either source separately validated these entries under a
phrase-specific rating methodology.

## Cumulative VAD totals

For every VAD dimension, VerseVAD separately reports these length-sensitive
token totals on the derived 0-1 display scale:

- rating total: `sum(x)`;
- above-midpoint load: `sum(max(x - 0.5, 0))`;
- below-midpoint load: `sum(max(0.5 - x, 0))`;
- net midpoint load: above minus below, equivalent to `sum(x - 0.5)`;
- absolute midpoint load: above plus below, equivalent to
  `sum(abs(x - 0.5))`.

Each included matched occurrence contributes once; an activated phrase is one
matched observation under the declared phrase policy. Unmatched tokens are
absent and never receive zero or 0.5. These statistics are called cumulative
normative lexical load because they grow with encountered matched vocabulary.
They are not a direct measure of cognitive load or affective impact on a reader.

## Corpus weighting and long works

Every work is analyzed separately before collection aggregation. For a given
lexicon and normalized VAD dimension, let `m_i` be work `i`'s token-weighted
mean and `n_i` its number of included matched observations.

The token-weighted volume profile pools observations:

`sum(m_i * n_i) / sum(n_i)`

The work-weighted volume profile gives every eligible work one score:

`sum(m_i) / number of eligible works`

Long works therefore contribute more to the first view but not the second.
VerseVAD reports both plus their signed difference. Work scores that are
missing because no observations matched remain missing; they are counted as
omitted and do not become neutral values. This collection-level distinction is
separate from the within-work token/type distinction: type-weighted work means
give each distinct matched lexicon entry one contribution.

Corpus comparisons use one completed batch. A pending or failed batch can
contain individually complete work runs for recovery and audit, but it never
replaces the latest complete comparison view.

## Versioned review scenarios

The unreviewed baseline remains distinct from every reviewed analysis. A named
scenario contains append-only decision revisions and produces immutable
scenario versions.

- A **flag** records a concern without changing matching or aggregates.
- An **exclusion** retains the published candidate in the audit but omits it
  from that scenario's aggregate.
- An **approved mapping** may map a source form to a verified exact entry in one
  selected lexicon only after exact, apostrophe/possessive, and lemma candidates
  fail.

Decisions use explicit occurrence, work, project, or global-within-scenario-use
scope. The narrowest defensible scope is preferred. Conflicting mappings at the
same applicable scope are rejected rather than guessed. Each decision records
the source form, target when applicable, lexicon, preserved text/version and
token location when applicable, semantic-risk category, rationale, revision,
and active/revoked state.

Creating, revising, revoking, restoring, or restoring an older scenario
snapshot appends a new version. Every completed run records the exact scenario
version and active decision revisions. Batch comparison therefore shows
before-and-after coverage and VAD deltas without rewriting the baseline.
Mapping and exclusion counts remain visible; unmatched-note proposals do not
affect scores unless converted into active scenario decisions.

## Lexicon Explorer derivations

Lexicon Explorer resolves an exact normalized entry or phrase before displaying
an explicitly labeled POS-sensitive lemma-derived entry. A user-supplied mapped
lookup is display-only and never changes poem/corpus matching. Similar terms are
suggestions only. If a phrase has no source entry and every component has an
exact VAD entry in one source, the interface may show their arithmetic mean as
a **VerseVAD-derived component average**, never as a published phrase rating.

Cross-lexicon spread is the range of normalized ratings for the displayed
entries. The interface labels ranges up to 0.10 "high" agreement, up to 0.25
"moderate," and larger ranges "low." This is an orientation heuristic, not a
source-provided reliability statistic or inferential test. Warriner standard
deviations and dimension-specific rater counts are displayed from their source
columns; missing uncertainty fields in other resources remain blank.

## Cross-lexicon comparison

Each lexicon is analyzed independently. Numeric VAD means may be displayed on a
separate normalized 0-1 scale alongside source-scale results. NRC VAD v1 and
v2.1 remain labeled as versions of the same family, not independent
replications. Categorical association rates and intensity prevalence/means keep
their different value kinds and denominators. Phase 2 creates no consensus
score or pooled rating.

## Context and close reading

Negation, irony, metaphor, quotation, speaker attribution, narrative distance,
and historical sense are not solved by lexicon matching. VerseVAD can flag
contexts for review, but flags do not change primary scores. Scholar-approved
exclusions or mappings create explicit alternative scenarios with visible
before-and-after results.

## Sparse and uncertain results

Aggregates with few matched items will be marked sparse or unstable. Missing
data remains missing rather than becoming zero. Coverage, lemma reliance,
mapping reliance, exclusions, and semantic-risk dependence are part of the
result, not merely diagnostics hidden elsewhere.

The Phase 3 interface labels coverage below 60% as limited orientation, 60-80%
as moderate orientation, and at least 80% as broad orientation. These bands are
reading aids only, not validated universal thresholds or exclusion rules. The
exact numerator, denominator, and rate remain primary.

## Phase 1 statistical definitions

Phase 1 reports descriptive statistics on the included matched observations.
Its standard deviation is the population standard deviation (`ddof = 0`),
because it describes the complete selected match set rather than estimating a
larger sampled population. Quartiles use the inclusive method. A single
observation has zero dispersion and quartiles equal to that observation. An
empty match set has missing statistics, not zeros.

Confidence intervals are deliberately deferred until the resampling unit and
dependence structure can be declared for the requested comparison. No
inferential meaning should be attached to the current descriptive summaries.

## Capitalization collisions

Case-insensitive lookup can collapse source entries that have different
capitalization and ratings. The Warriner file contains ten such pairs. The
adapter retains every source entry. Exact source capitalization may resolve the
pair; otherwise the occurrence is left unmatched for review. VerseVAD does not
average the candidates or select the first row.

## Stage 5 pronunciation, syllable, and lexical stress

Stage 5 uses exact observed-form entries from official CMUdict files pinned at
one upstream commit. Case and apostrophe style are normalized for lookup, but
the observed surface, normalized form, lemma, and every dictionary candidate
remain separate. No lemma, possessive-base, spelling repair, or pronunciation
prediction is substituted.

One dictionary candidate resolves directly. Multiple candidates resolve only
when every candidate agrees on both syllable count and the complete lexical-
stress digit sequence; phone-string alternatives remain visible. A difference
in syllables or stress is materially consequential and remains ambiguous until
a poem-specific scholar override supplies validated ARPAbet phones and a
required rationale. Confidence labels describe this categorical resolution
status and are not probabilities.

Unmatched, ambiguous, and source-vowelless observations have missing
pronunciation, syllable, and stress values. A physical line receives a total
and stress sequence only when every eligible lexical token resolves. This
prevents partial coverage from creating deceptively short lines.

Stress digits are CMUdict lexical evidence: `0` unstressed, `1` primary, and
`2` secondary. Stress density divides primary plus secondary stressed
syllables by all resolved syllables. It is not a measure of metrical fit or
performed emphasis.

CMUdict primarily represents North American English. Dialect, historical
pronunciation, performance, context, and poetic elision can differ. Stage 5
therefore reports dictionary-based pronunciation, syllable, and lexical-stress
evidence, not the poem's definitive sound or meter.
