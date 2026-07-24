# Poetic Fingerprint Stage 11: Project/Corpus Modules and Expanded Explorer

Status: implemented locally on 2026-07-24.

## Scope

Stage 11 makes the seven existing optional analysis modules available in
**Projects & Corpus**:

- concreteness;
- SUBTLEX-US frequency and rarity;
- Kuperman retrospective Age of Acquisition;
- CMUdict pronunciation and lexical stress;
- candidate meter and rhythmic regularity;
- rhyme and phonological patterns; and
- lexical diversity, word length, and line/stanza word counts.

The corpus path calls the same framework-independent modules used by **One
Poem**. Each work receives one shared preprocessing representation, and
pronunciation is reused as the dependency of meter and rhyme. No module
calculation has been copied into the interface or corpus aggregation layer.

## Persistence

Database schema 4 adds generic, immutable module tables:

- `module_results` records stable result, run, module, configuration, scenario,
  text-version, source-text-hash, module-version, and provenance identities;
- `module_metrics` retains value, layer, scope, scope ID, unit, weighting,
  denominator, and a safe observation count where one exists;
- `module_coverage` retains eligible, matched, unmatched, coverage-rate, and
  unmatched-item evidence;
- `module_warnings` retains plain-language and technical warning detail;
- `module_artifacts` stores the existing local CSV/JSON audit files with
  SHA-256 checksums; and
- `corpus_module_aggregates` stores only explicitly calculated collection
  aggregates.

`corpus_batches` records the selected module names and exact serialized
configurations. A batch may contain affective lexicons, optional modules, or
both. All writes for one work are transactional. A pending or failed batch
does not replace the latest complete comparison.

## Collection summaries

Every compatible numeric document metric receives an **equal-work mean**.
An **observation-weighted mean** is added only when every included work has a
defensible observation count for that exact metric. Configuration ID, module
version, metric ID, unit, and weighting must agree before values are grouped.

Lexical diversity receives additional, separately labeled calculations over
the **ordered pooled normalized-surface token sequence**. VerseVAD recalculates
pooled TTR, MATTR, HD-D, MTLD, and mean alphabetic word length from stored
token-audit evidence. It does not manufacture a pooled result by averaging
work-level diversity values.

Meter candidates, rhyme schemes, and other categorical evidence remain
work-level results. Stage 11 does not declare a corpus-wide meter or rhyme
scheme. Later visualization work may add clearly labeled categorical
prevalence views without changing those work-level records.

## Projects & Corpus interface and workbook

Additional modules are off by default. Frequency and AoA retain their
non-default content-word-only choices. The result view exposes:

- compatible collection summaries;
- explicitly pooled lexical-style calculations;
- work, line, stanza, token, type, and distribution metrics;
- coverage and unmatched evidence;
- warnings; and
- deterministic per-work module audit ZIPs.

The Excel workbook adds **Module Collection**, **Module Categories**, **Module
Work Results**, **Module Structure**, **Module Coverage**, **Module
Provenance**, and **Module Warnings** sheets. Binary audit artifacts remain
separate ZIP downloads.

## Expanded Lexicon Explorer

One search now checks every installed affective lexicon plus the local
concreteness, SUBTLEX-US, AoA, and CMUdict resources. It reports:

- all source-supplied concreteness fields;
- Zipf and the accompanying SUBTLEX-US frequency, contextual-diversity, and
  source-POS fields;
- AoA mean, dispersion, response counts, unknown-response evidence, and source
  frequency; and
- every exact CMUdict pronunciation candidate with ARPAbet phones, syllable
  count, and lexical-stress digits.

The Explorer distinguishes available-and-matched, source entry without a
numeric rating, available-but-unmatched, and resource-unavailable states. It
labels exact, lemma-derived, and user-mapped lookup methods. CMUdict lookup is
exact observed form only; alternatives remain separate. These are
decontextualized lexical or dictionary observations, not interpretations of a
poem's meaning or performance.

## Deferred work

Stage 11 is the foundational project/corpus port. Advanced longitudinal
visualization, sequence-aware trend models, change-point detection, PCA,
clustering, and the separate PoetryID proposal remain later work. The formal
emotional-archetype classifier also remains deferred pending its scholarly
specification.
