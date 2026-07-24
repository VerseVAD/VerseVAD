# Poetic Fingerprint Expansion: Stage 14

Stage 14 adds an optional performance-aware interpretation above the validated
fixed candidate-meter layer and a measured performance architecture across
VerseVAD. Candidate meter remains the default.

## What remains unchanged

- CMUdict or a poem-specific scholar override remains the source of lexical
  stress. Performance-aware meter never edits that source evidence.
- The candidate inventory remains five recurring patterns—iambic, trochaic,
  anapestic, dactylic, and amphibrachic—at one through eight feet.
- Stage 6 dynamic-programming costs, alternatives, ending allowances, and
  candidate summaries remain available and regression-tested exactly.
- Spondaic and pyrrhic evidence remains a local substitution description, not
  an additional whole-line base meter.
- Missing pronunciation leaves a line unanalyzable. No neutral stress, fit, or
  performance score is fabricated.
- The removed named stanza-form classifier is not restored. A stable
  alternating sequence may be described generically.

## Analysis layers

The meter configuration offers three explicit modes:

1. **Candidate meter only** is the validated default and returns the existing
   fixed-template result.
2. **Performance-aware realization** retains the fixed result and adds a
   profile-dependent realized reading.
3. **Compare both** presents the fixed and realized layers together.

The realized layer reranks a bounded number of retained fixed candidates. For
each candidate it keeps these components separate:

- fixed candidate fit;
- contextual prominence fit;
- syllable-count fit;
- punctuation-supported phrase fit;
- line-ending fit;
- pronunciation-path plausibility;
- poem recurrence;
- stanza recurrence;
- declared style compatibility;
- a visible substitution penalty.

The configured default weights reserve most influence for the fixed and
contextual evidence. The component values and weights are exported; the
overall score is not a probability.

## Contextual realization

Every aligned syllable retains:

- observed lexical-stress digit;
- proposed weak, strong, extrametrical, or omitted metrical position;
- proposed promotion, demotion, secondary-stress flexibility, or no
  adjustment;
- contextual prominence and position-fit values;
- source token, surface form, and part of speech;
- a text notation symbol and explanation.

Promotion and demotion are interpretive proposals. Initial inversion, headless
opening, feminine ending, catalexis, local spondaic/pyrrhic movement, extra
syllables, omitted positions, stress clash, stress lapse, and
punctuation-supported caesura remain separately labeled evidence. Visible
poetic contractions are recognized only when the scholar enables the
non-default option and the preserved spelling visibly marks the contraction.
Unmarked written syllables are never silently removed.

## Declared style profiles

The optional broad profiles are versioned:

- General English Verse;
- Traditional Accentual-Syllabic Verse;
- Romantic / Victorian Verse;
- Modernist Verse;
- Contemporary Formal Verse;
- Free Verse / Cadential;
- Custom visible weights.

A profile changes transparent tolerance and recurrence weights. VerseVAD does
not infer a literary period, movement, poet, date, or uniquely correct
performance from the text.

## Poem and stanza results

The realized layer reports:

- primary and retained secondary candidate;
- accentual-syllabic, accentual, syllabic, locally metrical, mixed, no-stable-
  pattern, or insufficient-evidence organization;
- rule-based confidence and explanation;
- line coverage, mean realized score, primary-candidate share, position
  agreement, substitution frequency, variability, candidate entropy, and
  ambiguous-line share;
- stanza candidate recurrence, line-position sequence, regularity, and
  exceptions;
- a line trajectory for realized score, syllables, beats, lexical-stress
  density, substitutions, and first caesura evidence;
- generic alternating recurrence when a stable alternating line sequence is
  observed.

These are textual and dictionary-based descriptions, not recovered performed
timing or authorial intention.

## Performance architecture

Stage 14 formalizes this dependency graph:

```text
preserved source text
  -> shared preprocessing
     -> affective sources -> PoetryID
     -> concreteness -----/
     -> frequency --------/
     -> AoA --------------/
     -> pronunciation
        -> candidate meter -> optional realized meter
        -> rhyme and recurring sounds
     -> lexical style
```

The application now uses bounded process-local layers for:

- immutable static resources already loaded by source hash;
- shared preprocessing;
- individual module results;
- display-ready data;
- completed exports.

Keys include only relevant source, configuration, resource, engine, and
upstream-result fingerprints. Changing a PoetryID threshold therefore does not
invalidate VAD. Changing a pronunciation override invalidates pronunciation,
meter, and rhyme while leaving unrelated lexical-style evidence valid.
Display and appearance changes invalidate no analytical result.

Every managed cache entry records a schema version, creation time, dependency
fingerprint, and inexpensive approximate size. Cached objects are validated
before use; invalid entries are discarded and recomputed. The caches are
thread-safe, suppress duplicate concurrent work for one key, and are bounded.
Settings exposes cache counts, debugging disablement, cache clearing, and
optional release of reloadable static resources. Clearing caches never removes
projects, source files, or saved results.

## Responsiveness choices

- ordinary startup no longer performs development-only hot reloads;
- complete downloads are prepared only after **Prepare downloads** is pressed;
- unchanged exports reuse a bounded export cache;
- meter alignment plans are cached independently of token display metadata;
- repeated documents and repeated lines reuse validated work;
- corpus persistence stays sequential and transactional to avoid multiplying
  large language and lexical resources across worker processes;
- corpus cancellation hooks act only between works, so a partially written
  work is never published;
- rerunning an interrupted batch in the same process can reuse valid module
  computations, but persistent cross-restart batch resume is not claimed.

## Exports

Candidate-only runs retain the original five meter files. Performance-aware
runs add:

- `meter_realizations.csv`;
- `meter_stanzas.csv`;
- `meter_rhythm_trajectory.csv`;
- `meter_scansion_report.txt`.

The existing nested meter JSON also contains the optional realized result.
When the scholar records one or more explicit line revisions, the bundle also
adds `meter_scholar_revisions.csv`; an empty revisions file is not created.
These files are available from Single Poem, Other Text, and each work's
Project/Corpus module artifact without duplicating the engine.
