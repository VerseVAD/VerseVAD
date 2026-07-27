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

`espeakng-loader==0.2.4` supplies a project-local eSpeak NG shared library and
voice data for Windows and Intel/Apple-silicon macOS. It is used only when the
scholar requests an audible preview of an explicit displayed ARPAbet
candidate. It is not an analysis source and does not select or predict a
pronunciation.

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

When the linguistic model splits a contraction, Stage 5 uses the complete
orthographic contraction span recorded by shared preprocessing. For example,
`you're`, `can't`, and `won't` each receive one exact observed-form lookup;
their internal model-token components are retained as `not_eligible` audit
rows rather than analyzed as independent words. Leading-apostrophe spellings
such as `'tis` are joined only when the complete form has exact CMUdict evidence
or an explicit override. An unmatched complete contraction remains one
unmatched review item and is never replaced by fragment-level G2P candidates.

Resolution states are:

- `dictionary_unique`: one source pronunciation;
- `dictionary_prosodic_consensus`: several source pronunciations whose phone
  strings differ but whose syllable count and full lexical-stress sequence
  agree;
- `dictionary_user_selection`: the scholar explicitly selected one retained
  CMUdict candidate for the observed form in the current session;
- `scholar_override`: a validated poem-specific ARPAbet selection with a
  required note;
- `ambiguous_dictionary`: source alternatives differ in syllable count or
  lexical stress;
- `source_without_marked_vowel`: a source row exists but cannot supply
  syllable/stress evidence;
- `unmatched`: no exact observed-form entry; and
- `not_eligible`: punctuation or numeric/non-lexical material.

An ambiguous, unmatched, or unusable source row remains missing. A provisional
G2P candidate shown for review is not an analytical fallback and does not
change that missingness unless explicitly approved or edited into an override.

The displayed confidence label is categorical source-resolution evidence, not
a calibrated probability.

The session-selection addition advances the pronunciation module to `1.1.0`
and the default scenario to `cmudict-prosody-foundation-v2`, so cached and
exported provenance cannot silently conflate earlier results with the new
dictionary-user-selection label.

Complete-contraction lookup advances the module to `1.2.0` and the default
scenario to `cmudict-prosody-foundation-v3`. That cache boundary prevents
results produced by fragment-level lookup from being reused after the
contraction policy changed.

## Scholar overrides

Advanced methodology settings accept one row per observed word:

```text
permit = P ER0 M IH1 T | verb reading in this line
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

The default-collapsed **Words Needing Attention** interface provides a selector
for materially different retained dictionary candidates and writes the chosen
candidate into this same editable session override configuration. **Apply
Approved Pronunciations and Reanalyze** recalculates pronunciation and
dependent meter, rhyme/sound, and inherited-form evidence.

For an out-of-dictionary word, the default-off **Show Out-of-Dictionary Words**
subsection also requests a local, provisional US-English G2P candidate from
eSpeak NG 1.52.0 and maps the separated IPA result to validated CMUdict-style
ARPAbet. The word remains `unmatched`. **Leave explicitly unresolved** is
selected by default. The user may instead approve the prediction or edit its
ARPAbet and approve the edited reading. Only that explicit action copies a
source-labeled row into the session override configuration. A prediction
failure likewise leaves the word unmatched while permitting fully manual
ARPAbet entry.

Each pronunciation candidate in **Words Needing Attention** and Lexicon
Explorer has a
**Hear** control. It converts that displayed ARPAbet sequence to eSpeak NG
phoneme notation and synthesizes a local WAV preview on demand. The result is a
robotic orientation aid rather than a recording or an additional source of
pronunciation evidence. Hearing a G2P candidate does not approve it.

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
complete-line evidence, **Words Needing Attention**, candidate pronunciations,
overrides, warnings, and provenance.

The full audit ZIP adds:

- `pronunciation_summary.csv`;
- `pronunciation_lines.csv`;
- `pronunciation_types.csv`;
- `pronunciation_token_audit.csv`;
- `pronunciation_manifest.csv`; and
- `pronunciation_report.docx`.

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
