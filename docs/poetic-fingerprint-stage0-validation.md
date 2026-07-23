# Poetic Fingerprint Expansion Stage 0 Validation

Date validated: 2026-07-23

Stage 0 is an additive software foundation. It does not add a new analysis
button or change current VAD results.

## Automated result

The complete suite passed:

```text
115 passed
```

The 15 new Stage 0 tests cover:

- framework-independent module protocol use;
- immutable common result records;
- direct-observation/computed-summary/interpretation labeling;
- line-scoped metric identity;
- coverage counts and rates;
- missing coverage for empty denominators;
- rejection of invalid counts and non-finite numeric values;
- exact source-text SHA-256 provenance;
- local resource checksums without source changes;
- missing, malformed, and unsupported resource states;
- configured-root path containment;
- deterministic multiple-resource order; and
- refusal to record unavailable resources as completed-run provenance.

## Synthetic and local validation result

Both existing hand-calculated demonstrations passed:

- Phase 1 reproduced 7 of 9 matched lexical tokens, 77.8% coverage, and mean
  normative valence 4.428571 on its 1-9 scale.
- Phase 2 verified all five private source checksums, reproduced its synthetic
  calculations, and created source-specific results without a consensus score.

The 11-check diagnostic also passed:

- VerseVAD package;
- Streamlit;
- pinned English linguistic model;
- phrase and VAD calculation;
- categorical emotion calculation;
- emotion-intensity calculation; and
- all five locally supplied lexicon files and checksums.

Generated validation exports were placed in ignored temporary directories,
inspected through the successful demonstrations, and then removed. No source
lexicon was changed.

## Beginner-friendly verification

No command line is required for an ordinary interface check:

1. Double-click `start_versevad.bat`.
2. In the sidebar, open **Installation Check**.
3. Click **Run self-test**.
4. Confirm that all 11 checks say `PASS`.
5. Open **One Poem**.
6. Enter the title `Stage 0 invented check`.
7. Paste:

   `Bright stone moves beneath the dark wind.`

8. Select any installed VAD source and click **Analyze this text**.
9. Confirm that the existing Overview, Language Profile, VAD Profile, Emotion
   Profile, Evidence, Unmatched Vocabulary, and Guidance tabs behave as before.
10. Close the browser tab and launcher window when finished.

Expected result: current analyses remain unchanged. Stage 0 has no new visible
metric because it supplies contracts for later modules.

## Developer verification

From the project directory:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m versevad.demo --output tmp\stage0_phase1_validation
.\.venv\Scripts\python.exe -m versevad.phase2_demo --output tmp\stage0_phase2_validation
.\.venv\Scripts\python.exe -m versevad.diagnostics
```

Remove only the two generated `tmp\stage0_*_validation` directories after the
demonstrations pass.

## Confirmed limitations

- Existing VAD results do not yet implement `AnalysisModule`; no compatibility
  wrapper was needed for Stage 0.
- No Stage 1 `PoemDocument`, dependency record, entity record, or schema-4
  migration exists yet.
- No concreteness, SUBTLEX-US, AoA, pronunciation, meter, rhyme, or syntax
  resource has been installed by this stage.
- The existing Emotion Profile workspace remains a presentation of current
  evidence, not a centroid/region classifier.
- Resource presence and checksum validation do not replace adapter-specific
  format, column, range, and scholarly-provenance validation.
