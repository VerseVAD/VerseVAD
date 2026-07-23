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
