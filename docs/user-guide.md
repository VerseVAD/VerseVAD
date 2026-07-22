# VerseVAD User Guide

## Current status

VerseVAD has a validated Phase 2 five-lexicon engine and double-clickable
demonstrations. There is not yet a graphical project workspace or ordinary text
import screen. This guide will grow alongside tested features so it never
promises controls that do not exist.

You do not need to do anything with the source lexicon files. Keep the
`source_lexicons` folder in place and do not rename or edit its contents.

## Run the Phase 1 demonstration

1. Open the `ANEW VAD Study` folder.
2. Double-click `test_phase1.bat`.
3. Wait while the invented validation example runs.
4. Look for `VerseVAD Phase 1 validation passed.`
5. Press any key after reading the result.
6. Open `phase1_demo_output` to inspect the four CSV files.

The demonstration does not analyze a copyrighted poem and does not copy the
supplied lexicons into its output. Delete `phase1_demo_output` if you want to
remove the generated files; the next demonstration can recreate them.

## Run the Phase 2 demonstration

1. Open the `ANEW VAD Study` folder.
2. Double-click `test_phase2.bat`.
3. Wait while VerseVAD validates and analyzes with all five lexicons locally.
4. Look for `VerseVAD Phase 2 validation passed.`
5. Confirm that five separate coverage lines appear and that the heading says
   `Independent results (no consensus score)`.
6. Press any key after reading the result.
7. Open `phase2_demo_output` to inspect the seven CSV files.

The match audit shows selected NRC VAD v2.1 phrases such as `a bit` and
`dark night`, along with their suppressed component candidates. The comparison
file places source-specific metrics side by side and deliberately has no
consensus-score column. Delete only `phase2_demo_output` to remove the generated
files; the test recreates them.

## What the finished application will do

The ordinary workflow will be:

1. start VerseVAD by double-clicking its launcher;
2. create or open a project;
3. import a poem or corpus while preserving the original text;
4. choose one or more lexicons and a documented analysis recipe;
5. run analysis locally;
6. review coverage, matches, unmatched vocabulary, and warnings;
7. create reversible mappings, exclusions, or alternative scenarios;
8. compare the original and revised results;
9. export tables, charts, token audits, and draft methods documentation;
10. back up the project.

## Core terms

**Valence** describes the positive-to-negative or pleasure-to-displeasure
dimension of a word's normative rating.

**Arousal** describes the active/excited-to-passive/calm dimension.

**Dominance** describes the powerful/in-control-to-weak/out-of-control
dimension. NRC VAD v2 also discusses this dimension as competence.

**Token** means one occurrence in a text. If “stone” appears six times, it is
six token occurrences.

**Type** means a unique matched lexical item. Six occurrences of “stone” may
count once in a type-weighted summary.

**Surface form** is the word exactly as represented by the tokenizer in its
textual context.

**Lemma** is a linguistically proposed base form. For example, “cried” may have
the lemma “cry.” Lemmatization can be wrong, especially in poetic or historical
language, so VerseVAD will show the lemma and match method.

**Exact match** links a normalized surface form directly to a lexicon entry.
Exact entries normally take priority over lemma fallback.

**Coverage** states how much of the text found eligible lexicon entries under
the selected policy. A VAD mean without its matched count and coverage can be
misleading.

**Emotion association** is a categorical link, such as a word being associated
with fear. It is not automatically an intensity and does not prove that the
passage or speaker is afraid.

**Emotion intensity** is a numeric rating for a supplied word-emotion pair.
VerseVAD will keep how often such vocabulary occurs separate from the average
intensity among matched entries.

## What VerseVAD will not claim

VerseVAD cannot by itself resolve negation, irony, metaphor, voice, intention,
historical sense, or reader response. It will identify lexical patterns and
possible close-reading candidates while keeping the evidence inspectable.

## Backups and privacy

Project data will remain on this computer unless you deliberately copy an
export or backup elsewhere. Ordinary analysis will not require a paid API or
upload your texts. Detailed backup, restore, uninstall, and upgrade steps will
be added and tested with the graphical application.

## Scholarly review items

Please review the plain-language descriptions in `docs/lexicons.md`, especially
the remaining provenance item:

1. whether you have any original documentation or acquisition notes for the
   Warriner file beyond the supplied XANEW README.

This does not block private analysis. Phase 2 conservatively activates phrases
only for NRC VAD v2.1, the source explicitly containing unigrams and multiword
expressions. Phase 1 also found ten differently rated capitalization pairs in the Warriner source.
VerseVAD preserves both ratings and refuses to guess when capitalization does
not identify one source entry.
