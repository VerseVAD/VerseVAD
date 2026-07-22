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
12. include matched stopwords in the primary scenario;
13. report token- and type-weighted summaries separately;
14. show matched counts and coverage with every aggregate;
15. preserve all candidate, suppression, exclusion, and match provenance.

This recipe will be versioned. Changes create new analyses rather than altering
completed results.

## VAD summaries

Token-weighted summaries count every included occurrence. Type-weighted
summaries count each unique matched lexicon entry once within the declared unit.
Unmatched tokens are absent from the numeric mean; they are not assigned 0,
0.5, or another neutral value.

Cross-scale comparison may use a separate normalized score when the adapter's
source scale supports a documented linear transformation. Original scores and
source limits always remain available.

## Emotion association summaries

NRC Emotion Lexicon values are binary associations, not intensities. A term may
belong to multiple categories, so category percentages need not total 100%.
Every percentage will state its denominator.

Phase 2 reports, for every category, occurrence count, unique matched entry
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

The older Warriner and NRC VAD v1 sources are documented as word or lemma level.
Their whitespace-containing rows remain preserved and counted during validation
but are not active phrase candidates under the Phase 2 default.

## Cross-lexicon comparison

Each lexicon is analyzed independently. Numeric VAD means may be displayed on a
separate normalized 0-1 scale alongside source-scale results. NRC VAD v1 and
v2.1 remain labeled as versions of the same family, not independent
replications. Categorical association rates and intensity prevalence/means keep
their different value kinds and denominators. Phase 2 creates no consensus
score or pooled rating.

## Context and close reading

Negation, irony, metaphor, quotation, speaker attribution, narrative distance,
and historical sense are not solved by lexicon matching. VerseVAD may flag
contexts for review, but flags will not silently change primary scores.
Scholar-approved exclusions or mappings will create explicit alternative
scenarios with visible before-and-after results.

## Sparse and uncertain results

Aggregates with few matched items will be marked sparse or unstable. Missing
data remains missing rather than becoming zero. Coverage, lemma reliance,
mapping reliance, exclusions, and semantic-risk dependence are part of the
result, not merely diagnostics hidden elsewhere.

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
