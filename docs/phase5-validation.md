# Phase 5 Validation and Beginner Test Steps

This checklist validates VerseVAD's versioned review scenarios, separate
sentiment reporting, part-of-speech profiles, title-case interface, exports,
and beginner documentation. It uses only invented text.

## Before You Begin

1. Close every older VerseVAD browser tab and launcher window.
2. Double-click `start_versevad.bat`.
3. Confirm that the top workspace choices are **One Poem**, **Projects &
   Corpus**, and **Lexicon Explorer**.
4. In the sidebar, confirm the heading **Installation Check**.
5. Click **Run self-test** and confirm that all 11 checks pass.

## Test A: One-Poem Language and Affect Profiles

1. Open **One Poem**.
2. Use the title `Phase 5 invented test`.
3. Paste:

   `Bright birds sing, and the dark wind rises.`

4. Select NRC VAD v2.1, NRC Emotion, and NRC Emotion Intensity.
5. Click **Analyze this text**.
6. Confirm that the result tabs include **Language Profile**, **VAD Profile**,
   and **Emotion Profile**.
7. Open **Language Profile**. Confirm that **Part-of-Speech Profile** shows a
   token count and percentage for each displayed category and that the shares
   total approximately 100% apart from rounding.
8. Confirm that the table states the lexical-token denominator, universal POS
   tag, unique normalized types, and examples.
9. Read the model-warning text. Treat surprising labels as candidates for
   token-level inspection rather than ground truth.
10. Open **Emotion Profile**. Confirm that **Eight Emotion Associations** and
    **Positive and Negative Sentiment Associations** are separate sections.
11. Confirm that **Emotion Intensity Among Supplied Matches** remains separate
    from both association sections.

Expected result: no exception appears; grammatical, VAD, emotion, sentiment,
and intensity constructs remain separately labeled.

## Test B: Create an Unreviewed Corpus Baseline

1. Create a temporary folder outside `source_lexicons`.
2. Add two UTF-8 files:

   - `short.txt`: `Bright mysteryword.`
   - `long.txt`: `Dark wind. Dark wind. Dark wind.`

3. Open **Projects & Corpus** and create `Phase 5 disposable project`.
4. Under **Works & Metadata**, import the folder.
5. Under **Language Profile**, confirm:

   - **All Works Combined** reports pooled counts and shares;
   - the longer/repeated work contributes more occurrences to that combined
     view;
   - **Work-by-Work Comparison** gives each work its own denominator and share.

6. Under **Analyze & Compare**, choose both works, NRC VAD v2.1, and
   **Unreviewed baseline**.
7. Click **Analyze selected works** and wait for completion.
8. Record the completed baseline batch ID and the unmatched status of
   `mysteryword`.

Expected result: the complete batch is available for comparison. The unknown
form remains missing and is not assigned a neutral score.

## Test C: Create and Apply a Review Scenario

1. Open **Review & Scenarios**.
2. Create a scenario named `Map invented form for validation`.
3. Choose that scenario under **Scenario to Edit**.
4. In the semantic-risk queue, choose the `mysteryword` occurrence for NRC VAD
   v2.1.
5. Choose **Map**.
6. Use mapping target `bright`.
7. Choose **Work** scope.
8. Enter the rationale:

   `Invented validation mapping; not a claim about a historical source form.`

9. Save the decision.
10. Confirm that the scenario version changes and the active decision list
    shows:

    - action `Map`;
    - scope `Work`;
    - source `mysteryword`;
    - target `bright`;
    - one stable decision identity and one active revision.

11. Return to **Analyze & Compare**.
12. Select the exact reviewed scenario version and rerun both works with the
    same lexicon and methodology.

Expected result: the reviewed run records `approved_user_mapping` for the
eligible occurrence. It does not replace an exact, possessive/apostrophe, or
lemma match.

## Test D: Compare Immutable Batches

1. Under **Compare Two Immutable Analysis Batches**, select the unreviewed
   baseline and reviewed batch.
2. Confirm that the comparison shows like-for-like coverage and VAD deltas.
3. Confirm that the baseline remains available and unchanged.
4. Inspect the reviewed evidence and confirm that the mapping and scenario
   version are visible.

Expected result: review changes produce a new result rather than editing the
baseline.

## Test E: Revoke, Restore, and Restore a Snapshot

1. Return to **Review & Scenarios**.
2. Revoke the mapping decision with a rationale.
3. Confirm that a new scenario version is created and the decision is inactive.
4. Restore the decision and confirm that another new scenario version is
   created.
5. Choose an older version under scenario history and restore its snapshot.
6. Confirm that restoration creates a new latest version; it does not overwrite
   the historical version.

Expected result: the decision and scenario histories are append-only.

## Test F: Flag and Exclude

1. In the same disposable scenario, select a review candidate.
2. Add a **Flag** with an occurrence scope and rationale.
3. Rerun and confirm that the flag does not change matching or scores.
4. Add an **Exclude** decision for a suitable published candidate with the
   narrowest defensible scope.
5. Rerun and confirm that:

   - the candidate remains visible in the audit;
   - it is labeled excluded by review;
   - it is omitted from the reviewed aggregate;
   - review-exclusion counts are visible.

Expected result: flags are non-scoring; exclusions alter only the pinned
reviewed scenario.

## Test G: Export

1. Open **Excel Export** and download the workbook from the reviewed batch.
2. Confirm that it includes:

   - **START HERE**;
   - **Corpus Profiles**;
   - **Work VAD**;
   - **Cumulative Load**;
   - **Coverage and Emotion**, with separate construct labels for emotion,
     sentiment, and intensity;
   - **Part of Speech**;
   - **Unmatched QC**;
   - **Review Decisions**;
   - **Text Metadata**;
   - **Methodology**.

3. In **Review Decisions**, confirm the exact decision revision, action, scope,
   source form, target, risk label, and rationale.
4. In **Methodology**, confirm the scenario version and software version.
5. In **Part of Speech**, confirm combined and work-level counts, shares,
   denominators, and model.

Expected result: the workbook is a readable derived report. The SQLite project
database remains authoritative.

## Test H: Beginner Documentation

Open:

- `docs/VerseVAD_User_Manual.docx`;
- `docs/VerseVAD_Values_and_Terminology_Guide.docx`.

Confirm that a new user can find:

- startup and shutdown;
- one-poem and corpus workflows;
- definitions of VAD, stopword, token/type weighting, dispersion, sensitivity,
  cumulative loads, emotions, sentiment, intensity, and part of speech;
- mathematical formulas;
- worked numeric examples;
- review scenario instructions;
- every download and workbook sheet;
- interpretation cautions and a reporting template;
- troubleshooting.

## Cleanup

Delete `Phase 5 disposable project` only if it contains no needed research:

1. Open **Project Settings**.
2. Type the exact project title.
3. Click **Delete this project**.

This does not delete the imported source folder or any source lexicon.
