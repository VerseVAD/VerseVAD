# Stage 15: Inherited Form Analysis

> Historical foundation note: this document records the initial version-1
> ten-profile implementation. Registry version 2.0 now contains 169 profiles
> and is documented in
> [`inherited-form-registry-v2.md`](inherited-form-registry-v2.md).

## Objective

Stage 15 adds a transparent candidate-ranking system for inherited poetic
forms. It answers:

> Which documented formal profile most closely resembles the observed poem,
> how much of that profile could be tested, and where does the poem agree or
> depart?

It does not declare the poem's genre, tradition, quality, authorial intention,
or single correct reading.

## Version-1 registry

The first registry contains ten profiles:

| Profile | Principal machine-readable evidence | Definition sources |
|---|---|---|
| Elizabethan / Shakespearean sonnet | 14 lines; ABAB CDCD EFEF GG; iambic pentameter; one block or 4/4/4/2 | [Academy of American Poets: Sonnet](https://poets.org/glossary/sonnet) |
| Petrarchan / Italian sonnet | 14 lines; ABBAABBA CDECDE or CDCDCD; common English pentameter; one block or 8/6 | [Academy of American Poets: Sonnet](https://poets.org/glossary/sonnet) |
| Spenserian sonnet | 14 lines; ABAB BCBC CDCD EE; iambic pentameter; one block or 4/4/4/2 | [Academy of American Poets: Sonnet](https://poets.org/glossary/sonnet) |
| Villanelle | 19 lines; five tercets plus quatrain; alternating first/third-line refrains; two-rhyme architecture | [Academy of American Poets: Villanelle](https://poets.org/glossary/villanelle) |
| Sestina | 39 lines; six sestets plus envoi; prescribed six-end-word rotation; envoi return | [Academy of American Poets: Sestina](https://poets.org/glossary/sestina) |
| Limerick | five lines; AABBA; long 1/2/5 versus short 3/4; anapestic tendency | [Academy of American Poets: Limerick](https://poets.org/glossary/limerick) |
| English-language 5–7–5 haiku profile | three lines; 5/7/5 resolved syllables; brevity | [Academy of American Poets: Haiku](https://poets.org/glossary/haiku); [Haiku Society of America definitions](https://www.hsa-haiku.org/hsa-definitions-2004.html) |
| Pantoum | linked quatrains; each stanza's lines 2/4 recur as the next stanza's 1/3; circular closure preferred | [Academy of American Poets: Pantoum](https://poets.org/glossary/pantoum); [Poetry Foundation: Pantoum](https://www.poetryfoundation.org/education/glossary/pantoum) |
| Terza rima | tercets; interlocking ABA BCB CDC rhyme; common English pentameter; optional terminal line/couplet | [Academy of American Poets: Terza Rima](https://poets.org/glossary/terza-rima) |
| Ghazal | 5–15 couplets; radif; preceding qafia; consistent line length | [Academy of American Poets: Ghazal](https://poets.org/glossary/ghazal) |

The registry is typed and versioned in
`src/versevad/inherited_form/profiles.py`. Every rule has a stable ID, feature
ID, required/preferred/optional role, positive weight, expected wording, and
parameters. Every profile contains an original concise definition, tooltip
definition, source URLs, tradition label, and explicit limitations.

## Shared evidence

Inherited Form Analysis depends on the existing shared modules:

```text
PoemDocument
  + PronunciationAnalysisResult
  + MeterAnalysisResult
  + PhonologicalAnalysisResult
  -> InheritedFormEngine
  -> ten FormCandidateResult records
```

Selecting the module automatically runs those dependencies. The engine:

- never tokenizes the poem again;
- never reloads CMUdict independently;
- never creates a second meter estimator;
- consumes performance-aware realized meter when present and otherwise uses
  the existing fixed candidate layer;
- consumes exact, identical, graded slant, and eye-rhyme evidence from the
  existing phonology result; and
- adds only ordered text/end-word detectors needed for the forms themselves.

## New form-specific detectors

- Villanelle compares the two anchor lines with positions 1/6/12/18 and
  3/9/15/19. Modified refrains receive graded lexical-sequence credit.
- Sestina uses exact normalized lexical line-ending words for the six-stanza
  rotation `ABCDEF / FAEBDC / CFDABE / ECBFAD / DEACFB / BDFECA`. The envoi
  checks the terminal ECA/ACE convention and whether all six seed words return.
- Pantoum compares every 2→1 and 4→3 interstanza line relationship and records
  circular closure separately as preferred evidence.
- Terza rima generates the eligible ABA BCB CDC chain for the observed tercets
  and applies the shared graded-rhyme comparison.
- Ghazal finds a repeated lexical suffix on the two opening lines and later
  even lines as a radif candidate. The preceding resolved pronunciation
  supplies qafia-rhyme evidence.
- Limerick compares resolved long-line and short-line syllable means and reads
  anapestic trimeter/dimeter candidates from the shared meter result.

## Scoring contract

For profile feature \(i\):

- \(s_i\) is its 0–1 agreement score;
- \(w_i\) is its documented profile weight;
- \(c_i\) is the available evidence share for that feature.

The available-evidence consistency index is:

\[
\text{consistency} =
\frac{\sum_i w_i c_i s_i}{\sum_i w_i c_i}
\]

The evidence-coverage index is:

\[
\text{coverage} =
\frac{\sum_i w_i c_i}{\sum_i w_i}
\]

An unavailable feature has no \(s_i\), contributes no consistency numerator or
denominator, and contributes zero available coverage. A partially supported
feature contributes only its supported fraction. Missing evidence is never
converted to a failed match.

A candidate must pass:

- the configured consistency threshold;
- overall weighted evidence coverage;
- required-feature evidence coverage; and
- the absence of a severe contradiction among available required features.

The candidate labels are:

- Strict;
- Strongly conforming;
- Modified;
- Form-derived;
- Suggestive resemblance; and
- No inherited-form match.

The confidence band is low, moderate, or high. It uses consistency, evidence
coverage, required-feature contradictions, and the margin over the runner-up.
It is not a calibrated probability.

## Traditional-definition tooltip

When a candidate is suggested, the classification metric exposes a tooltip.
The same content appears visibly in the result:

1. a concise traditional definition;
2. the strongest poem-specific agreements; and
3. the most material available departures.

This helps a reader understand what “potential match” means without treating
the label as self-explanatory. The complete definition, source links,
limitations, detected values, weights, and feature scores remain available in
the evidence table and exports.

## Tradition-aware limitations

- The haiku profile is explicitly **English-Language 5–7–5 Haiku Profile**.
  It does not claim that Japanese *on* are English syllables or that 5–7–5 is
  a universal definition. Kigo, kireji, juxtaposition, image, and aesthetic
  identity are not scored.
- Ghazal semantic autonomy and optional maqta/signature are not inferred.
- Sonnets do not receive an automatically guessed semantic volta.
- Sestina repetition is structural; semantic transformation is not scored.
- Limerick comic tone and performance timing are not scored.
- Physical stanza layout remains separate from logical rhyme/form
  architecture, so a sonnet printed as one block can still be evaluated.

## Interfaces and persistence

Single Poem displays:

- potential match, classification, consistency, coverage, and confidence;
- source-backed traditional-definition tooltip;
- nearest alternative and margin;
- complete ten-profile ranking;
- selectable feature-level evidence;
- definitions, source links, and limitations; and
- a direct narrative DOCX download.

Project / Corpus uses the same engine and schema-4 module storage. It provides
a per-poem table with match, classification, consistency, coverage,
confidence, nearest alternative, margin, and status. It does not pool poems
into one collection form.

The artifact bundle contains six UTF-8 CSV files and one DOCX report:

- `inherited_form_summary.csv`;
- `inherited_form_candidates.csv`;
- `inherited_form_features.csv`;
- `inherited_form_profiles.csv`;
- `inherited_form_methodology.csv`;
- `inherited_form_manifest.csv`; and
- `inherited_form_report.docx`.

No JSON export is created.

## Expansion rule

The initial registry is intentionally limited to ten profiles so the scoring,
terminology, tooltips, near-miss behavior, and evidence thresholds can be
reviewed with representative poems. Later profiles should be added as data,
not scattered conditional UI prose, and must include sources, weights,
tolerances, limitations, fixtures, and near-miss validation.
