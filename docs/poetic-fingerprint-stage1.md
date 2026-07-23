# Poetic Fingerprint Expansion: Stage 1 Shared Processing

Status: implemented and validated on 2026-07-23

## Purpose

Stage 1 gives later Poetic Fingerprint modules one local, reusable processing
record. A one-poem request is parsed once, and every selected lexicon receives
the same immutable token sequence. This prevents future modules from quietly
using different tokenization, structure, normalization, or model annotations.

The shared record supports descriptive lexical analysis. Model output remains
evidence to inspect, not a declaration about a poem, speaker, reader, or
author.

## `PoemDocument`

`versevad.core.documents.PoemDocument` contains:

- the exact existing `TextDocument`;
- the complete `PreprocessingConfiguration` and its deterministic
  `configuration_id`;
- preprocessing recipe, pipeline, model, and component provenance;
- one exact section plus stanza and physical-line records;
- model sentence records that may cross poetic line or stanza boundaries;
- the existing immutable token records, including original surface,
  normalized form, lemma, part of speech, morphology, offsets, and structural
  coordinates;
- dependency records with explicit line/stanza-crossing flags;
- optional named-entity records;
- hyphenated-expression, contraction, and apostrophe-form spans;
- content/function/other/non-lexical token classifications;
- processing coverage and plain-language warnings.

The current default recipe ID remains
`versevad-default-preprocessing-v1`, preserving the existing VAD provenance.
The separate configuration hash records the newly explicit processing choices.
Changing a configuration choice therefore changes the configuration ID without
pretending that the source text changed.

## Exact text and poetic structure

The source string is never normalized in place. The processor retains exact
characters, capitalization, indentation, blank physical lines, and `CRLF` or
`LF` line endings. Physical-line records must reconstruct the complete source
string exactly.

Each nonblank run belongs to a stanza. Blank lines are retained as physical
line records under the section so that stanza separators remain visible
without fabricating lexical content. Sentence segmentation is a separate model
layer: a sentence may cross a line or stanza boundary, and that crossing is
recorded rather than silently forcing prose and poetic structure to agree.

Lookup forms use NFC normalization in a separate processing representation.
Punctuation remains in the token audit even when it is ineligible for a
lexical aggregate.

## Linguistic annotations and classifications

The pinned `en_core_web_sm` pipeline supplies tokenization, sentence
segmentation, lemmatization, Universal Dependencies part-of-speech tags,
morphological features, and dependency labels. These annotations may be
uncertain for poetic syntax, fragments, archaisms, dialect, unusual
capitalization, or ambiguous forms. Stage 1 therefore preserves source forms
and model output together.

Content/function labels are explicit configuration-based groupings over the
model POS tag. `PROPN` is retained as proper-noun evidence even though the
beginner-facing broad Language Profile continues to merge `NOUN` and `PROPN`
under **Noun**. Punctuation and spaces are non-lexical; other model categories
remain separately labeled rather than being forced into content or function.

Hyphenated expressions, contractions, and other apostrophe forms retain their
model token components and receive an additional exact-source span record.
This exposes the tokenization choice without rewriting the surface text.

Named-entity recognition is optional and disabled by default. Enabling it is a
configuration change, and any entity record remains a model proposal rather
than a corrected literary identification.

## Coverage and missing values

Processing coverage records total and lexical tokens, sentences, tokens with
sentence annotations, dependency records, entities, and their applicable
rates. Empty denominators remain missing.

`en_core_web_sm` does not provide a real vector vocabulary. Stage 1 therefore
records model-vocabulary availability as false and leaves model OOV count/rate
missing. It does not call every word in-vocabulary or out-of-vocabulary, and it
does not confuse model OOV status with failure to match a lexicon or future
local resource. Later resource adapters, including planned SUBTLEX-US
frequency, must report their own eligible, matched, and unmatched coverage.

spaCy does not expose a calibrated confidence value for each dependency edge,
so dependency confidence remains missing. VerseVAD does not invent one.

## Workspace and module integration

`run_workspace_analysis` now:

1. validates and preserves the requested text;
2. creates one `PoemDocument`;
3. wraps it in a read-only prepared preprocessor;
4. reuses its exact tokens for every selected lexicon; and
5. returns the common document on `WorkspaceAnalysis`.

`ModuleInput.from_poem_document` exposes the same source, tokens,
preprocessing provenance, and shared document to future framework-independent
modules. Existing modules can still use the Stage 0 fields directly.

The Language Profile shows a **Shared Processing Record** with structure,
coverage, recipe, configuration ID, model pipeline, NER state, and warnings.
The full audit ZIP adds `poem_document.json`. That local JSON includes the
original text, so it should be handled with the same privacy care as the
existing detailed result export.

## Compatibility and deferred work

Stage 1 does not:

- alter exact-first affective-lexicon matching or any existing calculation;
- assign a neutral value to an unmatched observation;
- change SQLite schema 3 or persist structural records in the project database;
- install or query SUBTLEX-US;
- add a formal emotional-archetype centroid/region classifier; or
- send any text, lexicon, project, or result to an external service.

Schema-4 module-result persistence remains a later migration after backup and
migration tests. The formal emotional-profile classifier remains deferred until
its profile sources, coordinate system, distance metric, confidence method,
sparse-coverage behavior, validation examples, and appropriately tentative
wording have a defensible specification.
