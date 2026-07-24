# Poetic Fingerprint Expansion: Stage 4 Age of Acquisition

Status: implementation, engine validation, and source validation complete on
2026-07-23; final Word visual QA remains pending because the installed Word
PDF converter stalled

## Purpose

Stage 4 adds an optional one-poem module for retrospective normative lexical
Age of Acquisition (AoA) evidence. It reads the official Kuperman,
Stadthagen-Gonzalez, and Brysbaert supplement locally and summarizes the source
mean ages attached to represented vocabulary. It consumes the same immutable
`PoemDocument` as the affective, concreteness, and frequency modules but keeps
its construct, configuration, coverage, warnings, and provenance independent.

AoA describes the age, in years, at which adult source respondents believed
they had learned a word well enough to understand it. It is not identical to
word difficulty, grade level, frequency, familiarity, concreteness,
comprehension, intelligence, or reader response.

The required warning is:

> Age-of-acquisition results describe lexical patterns and are not diagnostic
> of cognitive impairment or decline.

## Primary source and local files

The analysis-time source is the official electronic supplement made available
through the 2013 erratum:

`resources/kuperman_2013_erratum_ESM1_official.xlsx`

Its SHA-256 is:

`3f69a1332359de1cd4a7ccd3c4c3c2e39b388eeb171d6e90544709c3dc1a8a6e`

The locally retained publisher paper is:

`resources/kuperman_stadthagen_gonzalez_brysbaert_2012_aoa_PAPER.pdf`

Its SHA-256 is:

`fa72b2dd7980707de710b4dcb346d0368d5e2c21d657824a935ea4b8b8b80e1a`

Citation:

Kuperman, V., Stadthagen-Gonzalez, H., and Brysbaert, M. (2012).
"Age-of-acquisition ratings for 30,000 English words," *Behavior Research
Methods*, 44, 978-990,
<https://doi.org/10.3758/s13428-012-0210-4>. The electronic supplement was
published with the 2013 erratum,
<https://doi.org/10.3758/s13428-013-0348-8>.

The files remain local and excluded from source control. VerseVAD reads the
workbook in place, records its hash, does not modify it, and does not copy the
complete source into exports.

Three other locally supplied workbooks are retained unchanged but are not
analysis sources:

- `AoA_51715_words.xlsx` is a derived multi-source compilation containing
  direct and lemma-level fields from several norms;
- `AoA_ratings_Kuperman_et_al_BRM_with_PoS.xlsx` adds a POS column to the
  Kuperman rows; and
- `Master file with all values for test based AoA measures Biemiller.xlsx`
  represents a distinct test-based AoA construct.

VerseVAD does not merge or silently substitute these sources.

## Source audit and the content-word question

The paper says the target list was constructed from base words used most
frequently as nouns, verbs, or adjectives in parsed SUBTLEX-US data. The
official supplement nonetheless includes rated polyfunctional spellings such
as:

- `the`: 3.983747 years;
- `and`: 4.569882 years;
- `he`: 3.813235 years;
- `of`: 4.548568 years; and
- `to`: 3.951776 years.

This is not evidence that the paper abandoned its sampling rule. A spelling
can have a content-word sense, can have been used as a control or calibrator,
or can be polyfunctional. The important implementation consequence is that an
exact spelling match does not prove that a particular occurrence in a poem is
a content-word use.

VerseVAD therefore keeps two separate concepts:

1. source-list construction, documented by the paper; and
2. the installed model's contextual POS tag for the poem occurrence.

The default analysis includes all lexical tokens, except default-excluded
proper nouns. An optional, non-default **AoA content words only** setting
restricts the poem denominator to model-tagged `NOUN`, `VERB`, `ADJ`, and
`ADV`. It excludes determiners, prepositions, conjunctions, pronouns,
auxiliaries, punctuation, numbers, and other tags. This option is meaningful
even though the paper describes its target list as content words.

## Workbook contract

The official `Sheet1` has these exact columns:

`Word`, `OccurTotal`, `OccurNum`, `Freq_pm`, `Rating.Mean`, `Rating.SD`,
and `Dunno`.

The inspected workbook contains:

- 31,124 nonblank unique normalized word rows;
- 31,105 numeric `Rating.Mean` values;
- 19 entries with `Rating.Mean = NA`;
- numeric mean ages from 1.58 to 25.0 years;
- no duplicate normalized lookup keys; and
- 194 physically present but completely blank trailing worksheet rows, which
  the adapter ignores rather than treating as source entries.

For every row, the source `Dunno` value equals `OccurNum / OccurTotal`, despite
the potentially confusing column label. VerseVAD preserves the exact source
field and separately labels the derived quantity **numeric-response
proportion**. It also derives the unknown-response count as
`OccurTotal - OccurNum`.

`KupermanAoAAdapter` validates:

- the pinned source hash, `Sheet1`, and exact seven-column header;
- nonblank single-word terms and unique normalized lookup keys;
- integer and internally coherent response counts;
- optional `#N/A` source frequency values;
- numeric source means on the retained 0-25-year range or the exact `NA`
  marker;
- numeric source standard deviations when at least two numeric responses
  exist, and `NA` when fewer than two exist;
- the source `Dunno` field's exact relationship to the response counts; and
- the expected separation of 31,105 rated and 19 unrated entries.

Any changed, malformed, missing, or unsupported file prevents module
activation. The 19 source entries without numeric means remain lookup-visible
in the audit but cannot contribute to an aggregate.

## Eligibility and matching

The default eligibility policy includes lexical tokens, excludes punctuation,
numbers, and other non-lexical tokens, and excludes model-tagged proper nouns.
A scholar may explicitly include proper nouns. The optional contextual
content-word scope is off by default.

Eligible tokens are matched in this order:

1. exact normalized observed form;
2. normalized model lemma, only when enabled and no exact form is available;
3. documented conservative apostrophe or possessive fallbacks; and
4. unmatched with a missing value.

An exact observed form is never silently replaced by a lemma. If a spelling
exists in the source but its `Rating.Mean` is `NA`, the audit records the
source row and response evidence with the method
`source_entry_without_numeric_rating`; the token has no numeric AoA and does
not enter the aggregate.

## Calculations

The module reports token-weighted:

- mean and median normative source AoA;
- population standard deviation;
- inclusive first and third quartiles;
- interquartile range;
- minimum and maximum;
- configured early-, middle-, and later-acquired proportions;
- eligible, matched, unmatched, and source-unrated token counts;
- matched-token coverage;
- eligible, matched, and unmatched unique normalized observed-form counts;
- matched unique-word coverage;
- model-POS, physical-line, and stanza summaries;
- earliest- and latest-acquired represented terms; and
- a complete token-level audit.

Default orientation bands are:

- early-acquired: source mean age at or below 5;
- middle range: above 5 and below 12; and
- later-acquired: source mean age at or above 12.

These are configurable VerseVAD interface aids, not categories validated by
the source paper. Repetition contributes repeatedly to token-weighted
summaries.

The population standard deviation of the poem's matched source means is kept
separate from each source entry's `Rating.SD`. The latter describes variation
among source respondents for one word. Term and token tables also retain
`OccurTotal`, `OccurNum`, unknown-response count, numeric-response proportion,
and source frequency when available. The source paper advises caution with
means based on fewer than five numeric responses in small stimulus sets;
VerseVAD keeps those ratings visible, counts them, and issues a warning rather
than silently deleting them.

Empty inputs produce missing aggregates and missing coverage because no
eligible denominator exists. A nonempty but wholly unmatched eligible text
has zero coverage and missing AoA aggregates. No missing value becomes age
zero or a neutral age.

## Optional relationships

When Frequency or Concreteness is enabled in the same one-poem run, VerseVAD
adds a descriptive Spearman rank correlation between AoA and the other
measure. The calculation:

- joins evidence by the same token ID;
- collapses repeated occurrences to unique normalized observed surface types;
- uses one paired type-level mean per represented surface type;
- excludes multiword concreteness assignments because their expression rating
  is not aligned to one AoA word entry;
- requires at least three paired types; and
- reports the paired-type count, weighting, method, coefficient, and warning.

The coefficient is descriptive. It does not establish causation, difficulty,
or a reader effect. If too few paired types or no rank variation exists, the
coefficient remains missing.

## Interface and exports

Under **Choose Evidence**, enable **Age of Acquisition profile (Kuperman et
al. ratings)**. It can run alone or alongside affective, concreteness, and
frequency evidence. Advanced settings expose early/later thresholds,
proper-name exclusion, lemma fallback, the coverage caution, and the optional
contextual content-word scope.

The dedicated **Age of Acquisition** tab presents:

- mean, median, coverage, and configured band proportions;
- distribution and source-response evidence;
- optional relationships with enabled frequency and concreteness modules;
- warnings and the required non-diagnostic notice;
- line, stanza, and model-POS summaries;
- earliest/latest represented terms;
- token-level matching and missing-value evidence; and
- source, adapter, module, configuration, lookup, and inclusion provenance.

The audit ZIP adds:

- `aoa_summary.csv`
- `aoa_distribution.csv`
- `aoa_by_structure.csv`
- `aoa_by_pos.csv`
- `aoa_terms.csv`
- `aoa_relationships.csv`
- `aoa_token_audit.csv`
- `aoa_result.json`

CSV files are UTF-8 with a byte-order mark. Exports contain poem-specific
result evidence and source-row references, not the complete source workbook.
Stable module metrics and provenance make the result ready for a future
longitudinal aggregator.

## Current corpus boundary

Stage 4 is currently a one-poem, in-memory module, like expansion Stages 2 and
3. The **Projects & Corpus** workspace does not yet batch, persist, aggregate,
or export Concreteness, Frequency, or AoA results. Calling these outputs
"longitudinal-ready" means they have stable metric IDs, configuration IDs,
coverage, and provenance suitable for later aggregation; it does not mean
career-period analysis is already present.

Project/corpus integration requires the planned schema-4 module-result store,
batch orchestration, immutable run links, grouping by separately recorded
composition/publication metadata, corpus UI, and workbook sheets. That work
remains part of the corpus/longitudinal stage unless deliberately promoted
ahead of prosody.

## Compatibility and limitations

Stage 4 advances the development package to `0.10.0.dev0`. It does not change
database schema 3, review scenarios, affective, concreteness, or frequency
calculations, or the deferred emotional-archetype classifier.

Important limits:

- source values are retrospective adult judgments rather than observed
  individual acquisition dates;
- a source entry does not resolve a poem occurrence's sense;
- POS and lemma evidence is model-generated and can be uncertain in poetry;
- the paper's source sampling and the optional contextual POS filter answer
  different questions;
- early/later thresholds are configurable orientation aids;
- response count and source SD should accompany term-level interpretation;
- relationships require enough paired types and remain descriptive; and
- no lexical AoA pattern alone supports a cognitive or medical inference.
