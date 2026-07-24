# Poetic Fingerprint Stage 7: Rhyme and Phonological Patterns

Stage 7 is an optional, framework-independent module for descriptive rhyme and
recurring-sound evidence. It consumes the exact local CMUdict evidence retained
by Stage 5 and never changes the pronunciation audit.

## Evidence boundary

CMUdict supplies North American dictionary pronunciations with ARPAbet phones
and lexical stress. VerseVAD derives the classifications. It does not claim to
transcribe a reading, settle a dialectal pronunciation, identify authorial
intention, or prove that two words rhyme in performance.

An ending is analyzable only when all retained pronunciation alternatives
support one rhyme part. Materially different alternatives, absent words, and
source rows without a marked vowel remain unresolved. A poem-specific Stage 5
scholar override may resolve a form, but Stage 7 never predicts one.

## End-rhyme grouping and schemes

The rhyme part begins at the final primary-stressed vowel and continues to the
word end. If no primary stress exists, the final secondary-stressed vowel is
used; if neither exists, the final marked vowel is used.

Whole-poem and stanza schemes use only robust perfect or identical rhyme parts:

- `A`, `B`, and later letters identify exact rhyme groups;
- `x` identifies an analyzable but ungrouped ending;
- `?` identifies an unresolved ending; and
- blank or nonlexical physical lines are excluded from the letter sequence.

Slant and eye rhyme remain separate evidence and never create scheme groups.
End-rhyme pair comparisons are within preserved stanzas.

## Rhyme evidence

- **Perfect rhyme:** the rhyme parts agree but the complete retained endings
  are not identical.
- **Identical rhyme:** the complete retained phonological endings agree,
  including repeated end words or homophonic complete endings.
- **Masculine rhyme:** the exact rhyme part contains one final stressed
  syllable.
- **Feminine rhyme:** the exact rhyme part contains a stressed syllable followed
  by an unstressed syllable.
- **Multisyllabic rhyme:** the exact rhyme part spans more than one syllable.
- **Eye rhyme:** spelling supplies a shared final orthographic rime while the
  pronunciations do not form an exact rhyme.
- **Internal rhyme:** exact dictionary rhyme parts recur between eligible words
  within one physical line.
- **Refrain evidence:** exact normalized physical lines recur; this is textual
  repetition evidence, not a CMUdict classification.

## Graded slant evidence

Every analyzable within-stanza pair retains five transparent similarities:

`slant = 0.35(stressed vowel) + 0.25(final consonants) + 0.25(rhyme-part edit) + 0.10(stress alignment) + 0.05(syllable similarity)`

The default slant threshold is `0.68`. Related vowel families receive `0.60`
for the vowel component. When multiple pronunciations remain, VerseVAD uses
the minimum score across retained combinations for classification and records
the maximum too. If alternatives cross the threshold, the relationship remains
`ambiguous_pronunciation`. The score is a configurable heuristic, not a
probability.

## Recurring sound evidence

For each physical line and in aggregate, Stage 7 reports:

- phonemic alliteration from repeated initial consonant phones;
- assonance from repeated stressed-vowel phones;
- consonance from repeated consonant phones;
- line densities and dominant sound families; and
- the exact phone sequences supporting each result.

The default minimum repetition is two. These observations describe recurring
dictionary phonemes, not their perceptual salience in a performance.

## Coverage, limits, and safeguards

Coverage is analyzable eligible line endings divided by eligible physical-line
endings. Unresolved endings receive no rhyme label and no neutral value. A
configurable maximum pair count prevents unexpectedly large quadratic
comparisons.

Current limits:

- the module is available in the One Poem workflow and audit bundle, not yet
  persistent or aggregated in Projects & Corpus;
- phrase-level phonological phenomena, historical pronunciations, dialect
  models, and audio-derived performance evidence are not implemented;
- internal rhyme currently uses exact rhyme parts rather than the graded slant
  method; and
- the method supplies close-reading evidence rather than a universal theory of
  poetic rhyme.

## Interface and exports

Select **Rhyme & phonological patterns** and analyze the poem. Stage 5 runs
automatically. The **Rhyme & Sound** tab presents the whole-poem and stanza
schemes, coverage, exact/slant/eye pair evidence, masculine/feminine/
multisyllabic labels, internal rhyme, refrains, recurring sounds, warnings, and
provenance.

The audit bundle adds:

- `rhyme_summary.csv`;
- `rhyme_stanzas.csv`;
- `rhyme_lines.csv`;
- `rhyme_pairs.csv`;
- `rhyme_internal.csv`;
- `phonological_sounds.csv`; and
- `rhyme_result.json`.

## Method references

- Carnegie Mellon Speech Group, [CMU Pronouncing
  Dictionary](https://github.com/cmusphinx/cmudict), pinned locally by exact
  commit and SHA-256.
- Thomas Haider and Jonas Kuhn, [Supervised Rhyme Detection with Siamese
  Recurrent Networks](https://aclanthology.org/W18-4509/), used as background
  for computational rhyme representation rather than as a claim that
  VerseVAD reproduces its model.
- Patrick McCurdy, Vivek Srikumar, and Miriah Meyer, [RhymeDesign: A Tool for
  Analyzing Sonic Devices in Poetry](https://aclanthology.org/W12-2502/), used
  as background for line-level sound-device evidence.
