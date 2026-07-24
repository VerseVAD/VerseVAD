# Poetic Fingerprint Stage 10: Narrowed Lexical Style

## Scope decision

On 2026-07-24, the scholar explicitly skipped the broader planned Stage 8
visible-structure analysis and Stage 9 syntax/lineation analysis. VerseVAD
therefore does **not** add approximate refrains, punctuation or typography
profiles, syntactic complexity, enjambment, end-stopping, or line-boundary
classification in this stage.

The approved scope is:

- lexical diversity;
- alphabetic-character word length;
- lexical-token count for every preserved physical line; and
- lexical-token count for every preserved stanza.

The line and stanza counts are included here because they are needed alongside
the lexical-style results. They do not reactivate the skipped broader
visible-structure stage.

## Shared word unit

The module consumes the existing `PoemDocument`; it does not tokenize the poem
again. One counted word is one shared-preprocessing **lexical token**:
punctuation and numeric tokens are excluded. This keeps every count tied to the
same token IDs, offsets, line numbers, stanza numbers, normalized forms, and
model annotations already used elsewhere in VerseVAD.

This policy can differ from an editor's orthographic word count. For example,
the shared preprocessing record may represent components of a contraction or
hyphenated expression separately. The audit exposes those decisions rather
than hiding them.

Lexical-diversity types use each token's normalized **observed surface form**.
The model lemma remains visible in the audit but is never substituted for a
surface form.

## Lexical-diversity measures

### Descriptive token and type counts

VerseVAD reports lexical-token count, normalized observed surface-type count,
and plain surface type-token ratio:

```text
TTR = normalized observed surface types / lexical tokens
```

Plain TTR is retained as descriptive support only. It is not presented as the
primary comparison measure because it is sensitive to text length.

### Moving-average type-token ratio

For a configured window of `w` tokens, VerseVAD calculates TTR for every
overlapping window and returns their arithmetic mean:

```text
MATTR(w) = mean(TTR of tokens 1..w, 2..w+1, ... n-w+1..n)
```

The default window is 50. A poem shorter than the configured window receives a
missing MATTR value, not an automatically changed denominator.

### Hypergeometric distribution diversity

HD-D uses sampling without replacement. For a type occurring `f` times in a
text of `N` tokens and configured sample size `s`, the probability of observing
that type at least once is:

```text
P(type observed) = 1 - C(N-f, s) / C(N, s)
```

VerseVAD sums this probability over types and divides by `s`, yielding an
expected distinct-type proportion. The default sample size is 42. A poem
shorter than the sample receives a missing value.

### Measure of textual lexical diversity

MTLD moves through the token sequence until cumulative TTR reaches the
configured threshold, counts a factor, resets, and continues. A proportional
partial factor is retained at the end. VerseVAD performs the calculation
forward and in reverse and reports their mean. The default threshold is 0.72.

If no finite bidirectional factorization is available, MTLD remains missing.

These measures describe different properties of the observed vocabulary. None
is a probability, a measure of literary merit, or evidence of a reader's
vocabulary, intelligence, comprehension, or education.

The method choices follow the published descriptions of
[MTLD and HD-D](https://doi.org/10.3758/BRM.42.2.381) and
[MATTR](https://doi.org/10.1080/09296171003643098). Results should be compared
only when their token policy and configured parameters agree.

## Word length

Word length is the count of Unicode alphabetic characters in the observed
lexical-token surface. Apostrophes, hyphens, and other punctuation marks do not
increase the length. VerseVAD reports:

- mean and median;
- population standard deviation;
- minimum and maximum;
- inclusive first and third quartiles; and
- an exact character-length distribution.

A lexical token containing no alphabetic character stays in structural word
counts but receives no word-length value. Missing length is never entered as
zero.

## Line and stanza word counts

Every preserved physical line receives a row. Blank stanza separators remain
visible with word count zero. Summary statistics for words per line use
nonblank physical lines, while the detailed export retains blank rows.

Every preserved stanza receives:

- nonblank physical-line count;
- lexical-token word count;
- normalized observed surface-type count;
- descriptive stanza TTR; and
- mean and median alphabetic-character word length.

Line and stanza TTR values are local descriptive observations, not
length-resistant corpus comparison measures.

## Interface and exports

The optional, off-by-default module appears as **Lexical Style** in the One
Poem workspace. Advanced settings expose the MATTR window, HD-D sample size,
MTLD threshold, and short-text caution threshold.

The audit bundle adds:

- `lexical_style_summary.csv`;
- `lexical_style_word_lengths.csv`;
- `lexical_style_lines.csv`;
- `lexical_style_stanzas.csv`;
- `lexical_style_token_audit.csv`; and
- `lexical_style_result.json`.

Each result records the source-text hash, software and module versions,
preprocessing recipe and model, configuration ID, scenario, inclusion policy,
coverage, and warnings. The result is currently in-memory and available only
in One Poem. The later Projects & Corpus port should invoke this same module
rather than duplicate its calculations.

## Current limitations

- No broader typography, punctuation, repetition, syntax, enjambment, or
  lineation classifier is included.
- General tokenization choices can be uncertain for poetic, archaic, invented,
  contracted, or hyphenated forms.
- Surface normalization collapses case and the configured lookup
  normalization distinctions; the exact surface remains in the audit.
- Short poems can produce unstable diversity estimates even when a formula is
  mathematically available.
- MATTR and HD-D are not comparable across different window/sample settings.
- These values are not yet persisted or aggregated in Projects & Corpus.
