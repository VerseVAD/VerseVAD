# Poetic Fingerprint Expansion: Stage 6 Candidate Meter and Rhythmic Regularity

Status: implemented and locally validated on 2026-07-24

## Purpose and claim boundary

Stage 6 adds optional candidate-meter and rhythmic-regularity evidence to the
One Poem workspace. It consumes the retained Stage 5 dictionary lexical-stress
evidence and compares it with explicit templates. It reports a *nearest
configured candidate*, never a definitive meter, correct scansion, performed
rhythm, dialect, or authorial intention.

Selecting Stage 6 automatically runs the local Stage 5 pronunciation
foundation. No affective lexicon is required. Stage 6 does not rewrite the
Stage 5 result when a pronunciation alternative improves a metrical fit.

## Fixed line candidates

The fixed grid crosses five recurring base patterns with eight foot counts:

| Pattern | Foot stress |
| --- | --- |
| Iambic | `01` |
| Trochaic | `10` |
| Anapestic | `001` |
| Dactylic | `100` |
| Amphibrachic | `010` |

The foot-count names are monometer, dimeter, trimeter, tetrameter,
pentameter, hexameter, heptameter, and octameter. The default grid therefore
contains 40 fixed templates.

Spondaic `11` and pyrrhic `00` feet are reported as local substitutions in a
binary-foot alignment. They are not added as ordinary whole-line base meters.

## Alignment method

For each physical line, deterministic dynamic-programming sequence alignment
compares retained stress paths with each template. The configuration records
costs for:

- primary or secondary stress in a weak position;
- secondary stress in a strong position;
- promotion of an unstressed content or function-word syllable;
- an extra or omitted syllable;
- a feminine ending;
- a catalectic ending; and
- initial inversion.

The line fit is:

```text
fit = max(0, 1 - selected alignment cost / max(observed syllables, template syllables, 1))
```

Fit is a configured similarity from 0 to 1, not a probability. Function-word
promotion receives a lower default cost than content-word promotion, and
secondary stress has explicit flexibility costs. These are declared analytic
choices, not universal laws of English meter.

For an ambiguous Stage 5 dictionary entry, Stage 6 explores every retained
materially different stress pattern up to the configured per-line combination
limit. The candidate-specific selected stress path remains visible. It is not
promoted to a dictionary fact or claim about performance.

If any eligible word has no usable pronunciation evidence, the physical line
receives no meter fit. If the number of stress combinations exceeds the
configured limit, the line also remains unscored. Neither case receives a
neutral or partial fit.

## Poem-level result

Stage 6 aggregates equal-weight physical-line fits for:

- all 40 fixed templates;
- the dominant stress-pattern family;
- line-level nearest fixed templates;
- matching-line proportion;
- population variation in selected line fits;
- substitution, inversion, extra/omitted syllable, feminine-ending,
  catalectic, spondaic, and pyrrhic counts; and
- a rule-based candidate-confidence category.

The nearest poem-level result is a fixed pattern/foot-count candidate.
Candidate kind, pattern, and foot count remain separate fields. The removed
common-meter experiment is not part of the current result.

The rule-based confidence label uses analyzable-line count, coverage, mean fit,
margin over the nearest alternative, and matching-line proportion. It is not a
calibrated probability. Sparse, weak, or closely tied evidence receives an
insufficient or mixed/irregular assessment.

## Interface

In **One Poem**, enable **Meter & rhythmic regularity** under **Choose
Evidence**. The option is off by default and available when the pinned CMUdict
resources pass local validation.

The dedicated **Meter & Rhythm** tab shows:

- nearest candidate, kind, alternative, margin, fit, coverage, and confidence;
- physical-line fixed-template evidence;
- all 40 fixed candidates;
- deviations, warnings, and method provenance.

Advanced settings expose the line-fit threshold, poem candidate-fit threshold,
candidate-margin threshold, and maximum stress paths per line. Pronunciation
overrides remain available because Stage 6 depends on Stage 5.

## Exports

The readable scholar summary and CSV reading guide include Stage 6 rows. The
full audit ZIP adds:

- `meter_summary.csv`;
- `meter_candidates.csv`;
- `meter_lines.csv`;
- `meter_alignment_operations.csv`; and
- `meter_result.json`.

`meter_lines.csv` preserves the nearest fixed line candidate and selected
stress path. The operation audit preserves each observed/template stress
comparison, cost, word, model POS tag, and ending flag.

## Current limitations

- The starting evidence is North American dictionary lexical stress, not
  contextual or performed stress.
- Contextual promotion, demotion, dialect, historical pronunciation, elision,
  and performance can change a plausible scansion.
- The cost model and thresholds are transparent heuristics requiring future
  validation against a suitably licensed, independently annotated poetry
  corpus.
- The module does not yet model resolution, caesura, foot boundaries beyond
  the selected base template, rhetorical phrasing, or occurrence-specific
  pronunciation overrides.
- Stage 6 is currently available in the One Poem in-memory workflow and
  exports, not Projects & Corpus aggregation.
- The short-lived common-meter comparison was removed at the user's direction;
  the 40 fixed candidates remain unchanged.
- Rhyme and recurring phonological pattern analysis is implemented in Stage 7.
