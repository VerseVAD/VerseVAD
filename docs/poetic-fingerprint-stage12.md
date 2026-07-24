# Poetic Fingerprint Stage 12: PoetryID

## Scope

PoetryID is a dependent, descriptive classifier over VerseVAD's completed
source-specific normalized VAD results. It does not tokenize text, load a VAD
lexicon, match words, or calculate VAD independently. Each output is tied to
one source lexicon, analysis view, and weighting:

- VAD source: Warriner VAD, NRC VAD v1, or NRC VAD v2.1;
- view: all matched or stopwords excluded;
- weighting: token or type.

These combinations remain separate. PoetryID does not average sources or
produce a consensus profile.

## The 27-profile registry

Each dimension is classified as low, moderate, or high. The combination maps
to one canonical candidate profile.

| Dominance | Valence | Arousal | Profile |
|---|---|---|---|
| High | High | Low | The Sage |
| High | High | Moderate | The Steward |
| High | High | High | The Conqueror |
| High | Moderate | Low | The Monk |
| High | Moderate | Moderate | The Architect |
| High | Moderate | High | The Challenger |
| High | Low | Low | The Stoic |
| High | Low | Moderate | The Survivor |
| High | Low | High | The Avenger |
| Moderate | High | Low | The Gardener |
| Moderate | High | Moderate | The Companion |
| Moderate | High | High | The Celebrant |
| Moderate | Moderate | Low | The Still Water |
| Moderate | Moderate | Moderate | The Observer |
| Moderate | Moderate | High | The Adventurer |
| Moderate | Low | Low | The Hermit |
| Moderate | Low | Moderate | The Pilgrim |
| Moderate | Low | High | The Storm |
| Low | High | Low | The Sanctuary |
| Low | High | Moderate | The Dreamer |
| Low | High | High | The Reveler |
| Low | Moderate | Low | The Echo |
| Low | Moderate | Moderate | The Witness |
| Low | Moderate | High | The Wanderer |
| Low | Low | Low | The Void |
| Low | Low | Moderate | The Mourner |
| Low | Low | High | The Abyss |

These names are interpretive labels for normative lexical-affective
neighborhoods. They do not identify the emotion of a poem, the speaker's
psychology, authorial intent, or reader response.

## Threshold and distance method

Version 1 provides:

- a built-in fixed profile with `low <= 0.40`, `high >= 0.60`, and moderate
  between those inclusive boundaries;
- custom fixed low/high boundaries for each VAD dimension;
- centroids derived from the centers of the three configured regions unless a
  programmatic configuration supplies explicit in-region centroids;
- Euclidean distance across continuous normalized valence, arousal, and
  dominance;
- all 27 ranked centroid distances;
- inverse-distance relative affinities normalized across all 27 candidates.

Relative affinities are similarity summaries, not probabilities. The
categorical assignment and nearest continuous centroid are retained separately
and may differ near boundaries.

Corpus-tertile and z-score profiles are deliberately deferred. Implementing
them requires a defensible, versioned reference-corpus rule rather than an
implicit batch-dependent definition.

## Confidence and evidence states

The rule-based confidence label considers:

- distance from the assigned centroid;
- margin between the nearest and second-nearest centroids;
- proximity to each configured threshold boundary;
- categorical/nearest-centroid agreement;
- VAD coverage.

The possible labels are `high_confidence`, `moderate_confidence`,
`boundary_sensitive`, and `low_confidence`. These are documented evidence
labels, not calibrated probabilities.

By default, a token-weighted assignment requires five VAD observations and
20% token coverage; a type-weighted assignment requires three VAD observations
and 20% type coverage. These settings are configurable. Insufficient counts,
insufficient coverage, missing VAD, or invalid normalized means produce an
explicit unavailable result rather than a neutral value.

## Secondary lexical character

When the corresponding modules are enabled, PoetryID can describe:

- concreteness on the source 1-5 rating scale;
- frequency using local SUBTLEX-US Zipf values;
- age of acquisition using Kuperman retrospective normative mean ages.

Token and type summaries remain separate. Their thresholds come from the exact
completed module configurations. These dimensions are secondary descriptors
and never change the VAD profile.

## One Poem interface

Enable **PoetryID lexical-affective profile**, choose one or more selected VAD
sources, weighting views, and analysis views, then analyze. The PoetryID tab
shows:

1. continuous VAD and classified levels;
2. categorical and nearest-centroid candidates;
3. rule-based confidence, boundary, and coverage evidence;
4. a threshold-scale chart for V, A, and D;
5. three 3x3 valence-by-arousal maps, one per dominance level;
6. five nearest candidates and an expandable all-27 distance table;
7. optional secondary lexical character;
8. methodology, unmatched terms, cautions, and downloads.

## Projects and Corpus

PoetryID uses the same engine and shared per-work VAD results in a corpus batch.
Schema 4's generic module tables persist its metrics, coverage, warnings,
provenance, and checksummed artifacts without a new schema migration.

Collection views group only compatible source, view, weighting, module version,
and configuration records. They include profile prevalence, 3x3 map counts,
continuous work-level valence/arousal positions with dominance, and token/type
sensitivity. They do not declare one corpus-wide PoetryID identity.

## Exports

PoetryID intentionally produces CSV and plain text only:

- `poetry_id_summary.csv`;
- `poetry_id_neighbors.csv`;
- `poetry_id_lexical_character.csv`;
- `poetry_id_methodology.csv`;
- `poetry_id_archetype_map.csv`;
- `poetry_id_vad_scales.csv`;
- `poetry_id_report.txt`.

There is no PoetryID JSON export. Other pre-existing VerseVAD modules retain
their own established export formats.

## Current limitations

- Thresholds are descriptive study choices, not validated universal emotional
  regions.
- Centroid distance assumes equal dimension weighting and Euclidean geometry.
- Normative lexical means do not model negation, syntax, historical semantic
  change, irony, voice, or reading context.
- Short texts and low-coverage sources may be unstable or unavailable.
- A profile name is a reading aid for lexical evidence, not a psychological or
  biographical conclusion.
