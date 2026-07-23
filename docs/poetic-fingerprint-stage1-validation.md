# Poetic Fingerprint Expansion Stage 1 Validation

Date: 2026-07-23

## What this stage validates

Stage 1 is an additive shared-processing layer. It preserves current VAD,
emotion, corpus, review, interface, and database behavior while making one
exact, reusable `PoemDocument` available to all selected one-poem analyses and
future modules.

The Stage 1 synthetic cases cover:

- exact `CRLF` text, indentation, physical lines, blank stanza separators, and
  reconstruction from line records;
- model sentences and dependencies that cross poetic lines;
- em dashes, apostrophes, contractions, and hyphenated expressions;
- decomposed Unicode retained in the source with separate NFC lookup forms;
- content, function, other, non-lexical, and proper-noun evidence;
- unusual capitalization, one-word lines, punctuation-free poems, archaic
  forms, and repeated refrains;
- named-entity recognition disabled by default and enabled only by explicit
  configuration;
- unavailable small-model vocabulary coverage retained as missing;
- empty input, deterministic repeated processing, immutable common-module
  input, invalid configuration overlap, and inconsistent coverage refusal; and
- one preprocessing pass reused across multiple selected lexicons.

No private poem or restricted lexicon row is embedded in these fixtures.

## Automated and local checks

The completion run executes:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.demo
.\.venv\Scripts\python.exe -m versevad.phase2_demo
.\.venv\Scripts\versevad-diagnose.exe
```

The complete pytest result, synthetic demonstration results, diagnostic result,
and Word-manual render review are recorded in the Stage 1 source-control
checkpoint and completion report.

Automated result:

```text
129 passed in 36.14s
```

Both invented demonstrations passed. Phase 1 reproduced 7/9 matched lexical
tokens, 77.8% coverage, and mean normative valence 4.428571 on its synthetic
1-9 scale. Phase 2 verified all five local source checksums and reproduced its
independent phrase, VAD, association, intensity, and cross-source examples
without a consensus score.

The local diagnostic reported `11/11` passes, including VerseVAD
`0.7.0.dev0`, Streamlit 1.60.0, `en_core_web_sm` 3.8.0, the three
hand-calculated engine checks, and all five private source checksums. It did
not modify or transmit a source file.

`uv lock --check --offline` also passed with all 81 packages resolved from the
existing local cache and no network access.

The Word manual was rebuilt from its maintained Markdown source and opened
read-only in local Microsoft Word. LibreOffice was not installed, so Word's
local PDF save was used as the documented rendering fallback; Poppler produced
25 page images at 150 DPI. Every page was inspected. Header rows remain with
the first data row, glossary rows no longer split across pages, and no clipped
text, overlap, broken table, missing border, or unexpected page geometry was
found. The final manual remains a 25-page US Letter document.

## Beginner-friendly interface check

Use invented text so no private literary material is needed:

1. Double-click `start_versevad.bat`.
2. Open **One Poem**.
3. Enter the title `Stage 1 invented check`.
4. Paste this exact text:

   ```text
   O'er the moon-lit hill—
   NIGHT turns, and doesn't stay.

   Return
   return
   ```

5. Leave at least two lexicons selected and click **Analyze this text**.
6. Open **Language Profile**.
7. Confirm that **Shared Processing Record** shows two stanzas, five physical
   lines, the token and lexical-token counts, recipe and configuration IDs,
   model pipeline, dependency coverage, NER disabled, and processing cautions.
8. Confirm that the ordinary broad and detailed part-of-speech profiles still
   appear beneath the shared record.
9. Open **Downloads**, download the full audit ZIP, and open
   `START_HERE.txt`.
10. Confirm the ZIP contains `poem_document.json`.
11. Open that JSON in a text editor and confirm:
    - `source.original_text` retains the em dash, capitalization, apostrophe,
      hyphen, blank line, and repeated refrain exactly;
    - `configuration.preserve_original_text` and
      `configuration.preserve_punctuation` are `true`;
    - `structural_units` contains stanza and line records;
    - `orthographic_spans` records the hyphenated expression, contraction, and
      apostrophe form; and
    - `coverage`, `warnings`, and preprocessing provenance are present.
12. Return to **Overview**, **VAD Profile**, **Emotion Profile**, and
    **Evidence** and confirm the existing lexical-evidence views still load.

Expected result: Stage 1 makes the processing audit visible without changing
the interpretation of existing affective results. POS, lemma, sentence,
dependency, and optional entity fields remain model outputs.

## Privacy and cleanup

All processing is local. The full audit ZIP and `poem_document.json` contain the
original text; store or delete them according to the same rules used for other
research exports. The invented check can be discarded by closing the temporary
one-poem session. Source lexicons are never modified.

## Limitations

- The pinned modern-English statistical model can misparse poetic, archaic,
  dialectal, fragmented, or unusually punctuated language.
- Sentence and dependency boundaries do not replace poetic line/stanza
  structure; both layers are retained when they disagree.
- Dependency confidence remains missing because the model does not provide a
  calibrated per-edge value.
- The small English model has no usable vector vocabulary, so model OOV
  count/rate remain missing. This is separate from lexicon/resource coverage.
- Named-entity recognition is disabled by default and is not exposed as an
  ordinary analysis setting yet.
- Shared structural records are in memory and in the one-poem audit JSON; they
  are not new schema-3 database tables.
- SUBTLEX-US integration and the formal emotional-archetype classifier remain
  later stages.
