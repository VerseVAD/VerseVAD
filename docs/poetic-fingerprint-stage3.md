# Poetic Fingerprint Expansion: Stage 3 Lexical Frequency and Rarity

Status: implemented and validated on 2026-07-23

## Purpose

Stage 3 adds an optional one-poem module for corpus-relative lexical frequency
evidence. It reads official SUBTLEX-US word-form data locally and summarizes
the Zipf values attached to represented vocabulary. It consumes the same
immutable `PoemDocument` used by the affective and concreteness paths but
remains an independent construct and result.

A Zipf value is a logarithmic frequency measure. Roughly, a one-point increase
corresponds to a tenfold increase in corpus frequency. The value describes how
often a word form appeared in the SUBTLEX-US American subtitle corpus. It does
not measure difficulty, sophistication, accessibility, intelligence, literary
quality, historical appropriateness, or contextual prominence in the poem.

## Installed local source

The module reads this workbook in place:

`resources/subtlex-us/SUBTLEX-US frequency list with PoS and Zipf information.xlsx`

Its SHA-256 is:

`3a8cb93a4e28988c2ce722a63f6b8d394acdc42ebe2ab6e1f0e484ee0d4167a7`

The preserved official download archive is:

`resources/subtlexus1.zip`

Its SHA-256 is:

`458128f90a28c4f396cb2a5b23ac93c56f745ee8cfca9be2afedad4091d15090`

Both are ignored by source control and remain local. The archive is not used
at analysis time. VerseVAD neither modifies the workbook nor copies the full
frequency list into an export.

The main frequency source is Brysbaert, M., and New, B. (2009), "Moving beyond
Kucera and Francis: A critical evaluation of current word frequency norms and
the introduction of a new and improved word frequency measure for American
English," *Behavior Research Methods*, 41, 977-990,
<https://doi.org/10.3758/BRM.41.4.977>. The Zipf presentation follows van
Heuven, W. J. B., Mandera, P., Keuleers, E., and Brysbaert, M. (2014),
<https://doi.org/10.1080/17470218.2013.850521>.

The inspected worksheet is `out1g` and contains 74,286 data rows. Its exact
columns are `Word`, `FREQcount`, `CDcount`, `FREQlow`, `Cdlow`, `SUBTLWF`,
`Lg10WF`, `SUBTLCD`, `Lg10CD`, `Dom_PoS_SUBTLEX`,
`Freq_dom_PoS_SUBTLEX`, `Percentage_dom_PoS`, `All_PoS_SUBTLEX`,
`All_freqs_SUBTLEX`, and `Zipf-value`. Every row has a Zipf value; the observed
range is approximately 1.593 to 7.621.

## Adapter contract

`SubtlexUsAdapter` opens the workbook read-only and validates:

- the pinned source hash, exact worksheet, and exact column contract;
- nonblank word forms and unique normalized lookup keys;
- positive frequency and contextual-diversity counts;
- nonnegative lowercase counts;
- coherent log-frequency and contextual-diversity fields;
- finite Zipf values in the supported range; and
- the expected 74,286 usable entries for the installed source.

The source POS fields are retained as provenance. They do not override the
poem-specific POS tag produced by VerseVAD's installed language model. Valid
source `#N/A` POS fields remain missing rather than causing an invented label.
Any missing, changed, malformed, or unsupported workbook prevents activation.

## Eligibility, optional scope, and matching

The default scope considers every lexical token and excludes punctuation,
numbers, and other non-lexical tokens. Model-tagged proper nouns are also
excluded by default because names can receive corpus counts for reasons that
are not comparable with ordinary vocabulary.

An optional, non-default **Content words only** setting restricts the
denominator to tokens tagged exactly:

- `NOUN`
- `VERB`
- `ADJ`
- `ADV`

It excludes `DET`, `ADP`, `CCONJ`, `SCONJ`, `PRON`, `AUX`, punctuation, and
all other tags. `PROPN` remains excluded under the default proper-name policy.
This strict scope is deliberately separate from the broad Language Profile,
where `VERB` and `AUX` are grouped together under the reader-facing label
**Verb**. Model POS errors remain possible and the complete token audit must be
consulted when the distinction matters.

Eligible tokens are matched in this order:

1. exact normalized observed word form;
2. normalized model lemma, only when enabled and no exact entry exists;
3. a documented conservative apostrophe or possessive fallback; and
4. unmatched with a missing value.

An exact observed form is never silently replaced by its lemma. This matters
because SUBTLEX-US reports word-form frequency and an inflected form can have a
different corpus frequency from its lemma. Each audit row records the lookup
form, match method, source row, source counts, Zipf value, eligibility, and
reason. VerseVAD never translates an absent entry into zero.

## Calculations

The primary summary is the token-weighted median Zipf value. The median is
emphasized because a few very common word forms can pull an arithmetic mean
upward. The module also reports:

- token-weighted mean, population standard deviation, inclusive quartiles,
  interquartile range, minimum, maximum, and range;
- eligible, matched, and unmatched token counts and coverage;
- eligible, matched, and unmatched unique normalized observed-form types and
  type coverage;
- configurable rarity/commonness bands;
- model-POS, physical-line, and stanza summaries;
- lowest- and highest-frequency represented source terms;
- a rare-word tail; and
- a complete token-level audit.

The default display bands are:

- rare: Zipf below 3;
- uncommon: 3 to below 4;
- moderately common: 4 to below 5;
- common: 5 to below 6; and
- very common: 6 or above.

These are configurable VerseVAD orientation aids, not diagnostic categories
published for literary analysis. Repetition contributes repeatedly to
token-weighted statistics. Unique-type coverage is a coverage diagnostic over
observed normalized forms, not a second frequency mean.

Empty inputs have missing aggregates and missing coverage because there is no
eligible denominator. A nonempty but wholly unmatched eligible text has zero
coverage and missing frequency aggregates. Sparse matched sets and coverage
below the configured threshold produce visible warnings.

## Interface and exports

Under **Choose Evidence**, enable **Frequency & rarity profile (SUBTLEX-US
Zipf)**. The module can run with affective lexicons and concreteness or by
itself. Advanced settings expose display-band thresholds, proper-name
exclusion, lemma fallback, the low-coverage caution threshold, and the
non-default **Content words only** scope.

The dedicated **Frequency & Rarity** tab presents the primary median, mean,
interquartile range, coverage, bands, warnings, line/stanza/POS summaries,
lowest/highest terms, rare tail, token audit, configuration, and source
provenance.

The audit ZIP adds:

- `frequency_summary.csv`
- `frequency_distribution.csv`
- `frequency_by_structure.csv`
- `frequency_by_pos.csv`
- `frequency_terms.csv`
- `frequency_token_audit.csv`
- `frequency_result.json`

CSV files are UTF-8 with a byte-order mark. The exports contain poem-specific
results and source-row provenance, not the complete 74,286-row source.

## Compatibility and limitations

Stage 3 advances the development package to `0.9.0.dev0`. It does not change
database schema 3, persist frequency results in corpus projects, modify review
scenarios, change affective or concreteness calculations, introduce
`wordfreq`, pool values from different frequency resources, or add the
deferred emotional-archetype classifier.

SUBTLEX-US is based on American film and television subtitles, not poetry.
Register, historical period, spelling, dialect, capitalization, names, and
genre can affect both coverage and interpretation. Lemma and POS evidence is
model-generated. Read median, distribution, coverage, unmatched forms,
structural patterns, and the audit alongside the poem rather than turning a
corpus-relative frequency value into a claim about the poem or its reader.
