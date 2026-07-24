# Poetic Fingerprint Expansion: Stage 2 Concreteness

Status: implemented and validated on 2026-07-23

## Purpose

Stage 2 adds an optional one-poem module for descriptive normative lexical
concreteness. It is independent of the affective lexicons and consumes the
same immutable `PoemDocument` created in Stage 1. The module helps a scholar
inspect how source-rated vocabulary is distributed across a poem; it does not
measure imagery success, readability, literary quality, cognition, or a
poem's emotion.

## Installed local source

The module reads these user-supplied files in place:

- `resources/brysbaert_warriner_kuperman_concreteness_DATA.xlsx`
- `resources/brysbaert_warriner_kuperman_concreteness_PAPER.pdf`

The workbook SHA-256 is
`1673ead761e28833a40e82c0d20f10782955ced9366d600eafeefee0f2254545`.
The paper SHA-256 is
`7bafeef31b771965dbbbe2dea0227e210c8f4d054461343505f829ecfa036b63`.
Neither file is modified, copied into an export, or committed to source
control.

The source is Brysbaert, M., Warriner, A. B., and Kuperman, V. (2014),
"Concreteness ratings for 40 thousand generally known English word lemmas,"
*Behavior Research Methods*, 46, 904-911,
<https://doi.org/10.3758/s13428-013-0403-5>.

The inspected workbook contains 39,954 data rows: 37,058 single-word entries
and 2,896 two-word expressions. Its source columns are `Word`, `Bigram`,
`Conc.M`, `Conc.SD`, `Unknown`, `Total`, `Percent_known`, and `SUBTLEX`.
Ratings use the original 1-5 scale, where the study elicited judgments from
very abstract or language-based to very concrete or experience-based.

The workbook's `SUBTLEX` column is retained as source-row provenance only. It
is not VerseVAD's lexical-frequency analysis. Stage 3 uses a separately
installed and pinned official SUBTLEX-US Zipf resource and does not use
`wordfreq`.

## Adapter contract

`BrysbaertConcretenessAdapter` opens the workbook read-only and validates:

- the exact filename hash and worksheet/header contract;
- numeric types and the 1-5 rating range;
- nonnegative standard deviation, unknown, rater, and source frequency fields;
- consistency among unknown, total, and percent-known fields;
- phrase flags and whitespace structure;
- normalized lookup-key collisions; and
- the expected row and phrase counts for the installed source.

Any missing, changed, malformed, or unsupported workbook prevents module
activation. Partial rows are never activated. The resulting immutable entries
retain their source row, spelling, rating mean, source rating SD, rater fields,
percent known, phrase flag, and source `SUBTLEX` count.

## Eligibility and matching

The baseline scenario uses lexical tokens from the shared poem document.
Punctuation and other non-lexical tokens remain in the audit but are
ineligible. Model-tagged proper nouns are excluded by default because the
study's distributed list was not designed as a proper-name inventory. This
choice is configurable and remains vulnerable to model tagging errors in
poetry.

Matching proceeds in this order:

1. longest exact source-supplied two-word expression within one physical line
   and stanza, when phrase activation is enabled;
2. exact normalized surface form;
3. normalized lemma;
4. a documented conservative apostrophe or possessive fallback; and
5. unmatched with a missing rating.

An exact surface match is never replaced by a lemma match. Every audit row
states the method and reason. No unmatched or ineligible token receives zero,
the scale midpoint, the poem mean, or another invented value.

A matched two-word source expression is one lexical-expression occurrence but
its rating is assigned to each of its two covered token positions for the
declared token-weighted statistics. Both token rows share a stable match-group
ID and list the covered token IDs. The interface and export warn about this
explicit assignment so it cannot be mistaken for two independent source
ratings.

## Calculations

The module reports:

- eligible, rated, and unmatched lexical-token counts;
- token coverage;
- eligible, rated, and unmatched unique normalized-surface types;
- unique-type coverage;
- token-weighted mean, median, inclusive quartiles, interquartile range, and
  population standard deviation on the source 1-5 scale;
- configurable lower and upper orientation-band counts and proportions;
- part-of-speech, physical-line, and stanza summaries;
- most concrete and most abstract matched source terms, with repetition and
  source fields; and
- a complete token-level audit.

Repetition contributes repeatedly to the token-weighted summary. Unique-type
coverage is a coverage diagnostic over normalized surface forms, not a
type-weighted concreteness mean.

The default orientation aids label ratings at or below 2.0 as highly abstract
and ratings at or above 4.0 as highly concrete. These are configurable
VerseVAD display bands, not validated categories claimed by the source paper.

Empty inputs have missing aggregate statistics and missing coverage because
there is no denominator. A nonempty but wholly unmatched eligible text has
zero coverage and missing aggregate statistics. Sparse rated sets and coverage
below the configured caution threshold produce visible warnings.

## Interface and exports

Under **Choose Evidence**, the scholar can enable **Normative lexical
concreteness** when the exact local workbook is available. Advanced settings
expose the two orientation thresholds, proper-noun policy, phrase activation,
and low-coverage caution threshold. Existing affective analysis remains
unchanged, and a concreteness-only one-poem run is allowed.

The dedicated **Concreteness Profile** tab shows overall statistics, coverage,
warnings, physical-line and stanza summaries, model-assigned POS summaries,
term extremes, token audit, configuration, and source provenance.

The audit ZIP adds:

- `concreteness_summary.csv`
- `concreteness_by_structure.csv`
- `concreteness_by_pos.csv`
- `concreteness_terms.csv`
- `concreteness_token_audit.csv`
- `concreteness_result.json`

CSV files are UTF-8 with a byte-order mark. JSON and CSV exports contain result
and source-row provenance, not a copy of the 39,954-row workbook.

## Compatibility and limitations

Stage 2 advances the development package to `0.8.0.dev0`. It does not change
database schema 3, persist concreteness in corpus projects, alter affective
matching or review scenarios, or add the deferred emotional-archetype
classifier.

The source ratings are decontextualized norms, and the paper cautions that
concreteness is not a single complete account of word meaning or sensory
experience. Visual and haptic experience dominated the rating relationship;
auditory experience behaved differently. The distribution can also be
bimodal, so a mean can conceal distinct abstract and concrete vocabulary.
Always inspect coverage, dispersion, structure, terms, and token evidence
alongside the text.
