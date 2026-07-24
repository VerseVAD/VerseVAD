# Poetic Fingerprint Expansion: Stage 5 Prosody Foundation

Status: implemented and locally validated on 2026-07-24

## Purpose

Stage 5 adds optional dictionary pronunciation, syllable, and lexical-stress
evidence to the One Poem workspace. It is a foundation for later candidate
meter and rhyme modules; it does not classify meter, rhyme, rhythm in
performance, or definitive scansion.

The module consumes the shared immutable `PoemDocument`. It uses the exact
observed word form, keeps every dictionary alternative, records missing and
ambiguous evidence, and permits explicit poem-specific scholar overrides.

## Authoritative local source

VerseVAD pins the official `cmusphinx/cmudict` repository at commit:

`74790861f652b15e4ac49015a90074ad62a27690`

The authoritative analysis-time files are:

| File | SHA-256 |
| --- | --- |
| `resources/pronunciation/cmudict.dict` | `81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22` |
| `resources/pronunciation/cmudict.phones` | `ffb588a5e55684723582c7256e1d2f9fadb130011392d9e59237c76e34c2cfd6` |
| `resources/pronunciation/cmudict.symbols` | `408ccaae803641c6d7b626b6299949320c2dbca96b2220fd3fb17887b023b027` |
| `resources/pronunciation/CMUDICT_LICENSE.txt` | `bd4ce8e44170a5f9f481310ca85c51de3c4f851a65e679b40e603b143bd3542a` |
| `resources/pronunciation/CMUDICT_README.txt` | `00c34e7564f1f6a68de02e12c123d801471da92bc3091f7d89b605f238bf8554` |

Source: <https://github.com/cmusphinx/cmudict>. The CMU project page is
<https://www.speech.cs.cmu.edu/cgi-bin/cmudict?in=welcome>.

The retained license permits unrestricted research and commercial use and
requests acknowledgment of Carnegie Mellon University as the origin. The
resource files remain local and excluded from source control.

`pronouncing==0.3.0` supplies the pinned ARPAbet stress and syllable utilities.
Its dependency `cmudict==1.1.3` is recorded for reproducibility, but VerseVAD
does not use that package's bundled data at analysis time. The exact local
official files above remain authoritative.

## Source contract

The read-only adapter verifies:

- all three required source files and exact supported hashes;
- 135,166 dictionary rows, 39 phone-inventory rows, and 84 symbol rows;
- lowercase source spellings and CMUdict alternative suffixes such as `(2)`;
- contiguous alternative numbers for each spelling;
- known ARPAbet symbols and the base-phone inventory;
- stress digits `0`, `1`, and `2` only on vowel phones;
- agreement between explicit vowel counts and the pinned `pronouncing`
  syllable/stress utilities;
- duplicate variant numbers, repeated phone strings, malformed rows, unknown
  symbols, and source rows without a marked vowel; and
- SHA-256 checksums without rewriting, cleaning, or copying source rows.

The pinned source contains 126,052 normalized spellings. Of these, 8,447 have
multiple source pronunciation rows; the maximum is four. Eight source
pronunciations have no marked vowel and cannot supply Stage 5 syllable/stress
evidence. Two alternative rows repeat an existing phone sequence; they remain
auditable source variants and are reported as a source warning.

## Matching and alternatives

Eligible observations are lexical token occurrences, including proper nouns.
Punctuation and numeric/non-lexical tokens are excluded.

Lookup uses the normalized observed surface form only. Case is folded, Unicode
is NFC-normalized, and apostrophe styles are made comparable. VerseVAD does
not silently use a lemma, strip a possessive suffix, or substitute another
spelling. Those operations can change pronunciation.

Resolution states are:

- `dictionary_unique`: one source pronunciation;
- `dictionary_prosodic_consensus`: several source pronunciations whose phone
  strings differ but whose syllable count and full lexical-stress sequence
  agree;
- `scholar_override`: a validated poem-specific ARPAbet selection with a
  required note;
- `ambiguous_dictionary`: source alternatives differ in syllable count or
  lexical stress;
- `source_without_marked_vowel`: a source row exists but cannot supply
  syllable/stress evidence;
- `unmatched`: no exact observed-form entry; and
- `not_eligible`: punctuation or numeric/non-lexical material.

An ambiguous, unmatched, or unusable source row remains missing. Stage 5 has
no grapheme-to-phoneme fallback.

The displayed confidence label is categorical source-resolution evidence, not
a calibrated probability.

## Scholar overrides

Advanced methodology settings accept one row per observed word:

```text
permit = P ER0 M IH1 T | noun reading in this line
fire = F AY1 ER0 | two-syllable reading for this performance
```

Each override must:

- name a nonblank observed word;
- use uppercase symbols from the pinned local CMUdict inventory;
- include at least one vowel with a `0`, `1`, or `2` stress digit;
- include a short scholarly rationale; and
- appear only once after normalization.

Overrides apply to all exact occurrences of that observed form in the current
one-poem analysis. They are part of the configuration identity, reversible by
editing or removing the row, and kept distinct from the retained dictionary
candidates. Stage 5 does not yet offer occurrence-specific selection or
Projects & Corpus persistence.

## Metrics and missingness

The module reports:

- resolved syllables per lexical token, with mean, median, population
  dispersion, quartiles, and range;
- complete-line syllable totals and their descriptive distribution;
- word-grouped and compact lexical-stress sequences;
- primary, secondary, and unstressed syllable counts;
- lexical stress density: `(primary + secondary) / resolved syllables`;
- resolved token and observed-type coverage;
- complete-line coverage;
- ambiguity, out-of-dictionary, unusable-source, alternative, and override
  counts; and
- full token, observed-type, line, resource, configuration, and warning
  evidence.

A physical line is complete only when every eligible lexical token has a
resolved syllable count and lexical-stress sequence. Incomplete lines retain
missing totals and sequences. VerseVAD does not sum the known words and present
that partial sum as the line's syllable count.

Stress digits follow CMUdict/ARPAbet:

- `0`: unstressed;
- `1`: primary lexical stress; and
- `2`: secondary lexical stress.

These are dictionary lexical stresses, not contextually assigned metrical
beats.

## Interface and exports

Enable **Pronunciation & prosody foundation (CMUdict)** in One Poem. The
dedicated **Pronunciation & Prosody** tab shows coverage, summary metrics,
complete-line evidence, words needing attention, candidate pronunciations,
overrides, warnings, and provenance.

The full audit ZIP adds:

- `pronunciation_summary.csv`;
- `pronunciation_lines.csv`;
- `pronunciation_types.csv`;
- `pronunciation_token_audit.csv`; and
- `pronunciation_result.json`.

The readable scholar summary and CSV reading guide include pronunciation rows.

## Required interpretive language

Use:

> dictionary-based North American pronunciation, syllable, and lexical-stress
> evidence under the selected override configuration

Do not use:

> the poem is in a particular meter

or:

> the poet pronounces this word this way

Stage 6 will estimate candidate meter transparently from alternatives. Stage 7
will add rhyme and recurring phonological-pattern analysis.

## Current limitations

- CMUdict primarily represents North American English and acknowledges errors,
  omissions, and inconsistencies.
- Historical, dialectal, contextual, performed, and poetically elided
  pronunciations may differ.
- The dictionary does not encode every proper name, inflection, archaic form,
  contraction, or orthographic variant.
- Strict ambiguity handling can make a line incomplete even for common words
  whose dictionary alternatives differ only by contextual stress. A documented
  override is the current resolution mechanism.
- Overrides currently apply by exact observed type within one analysis, not by
  individual occurrence.
- No pronunciation prediction, meter, rhyme, or corpus aggregation is included
  in Stage 5.
