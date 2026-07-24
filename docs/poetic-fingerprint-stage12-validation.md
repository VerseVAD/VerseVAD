# Poetic Fingerprint Stage 12 Validation

## Hand-calculated example

The synthetic validation supplies normalized VAD `(0.2, 0.5, 0.8)` under the
default fixed thresholds:

- valence `0.2 <= 0.4`: low;
- arousal `0.4 < 0.5 < 0.6`: moderate;
- dominance `0.8 >= 0.6`: high.

The registry maps low valence, moderate arousal, and high dominance to **The
Survivor**. Default centroids are `0.2`, `0.5`, and `0.8`, so this point's
distance from The Survivor centroid is exactly zero.

Run:

```powershell
.\.venv\Scripts\python.exe -m versevad.poetry_id_validation
```

Expected result:

```text
VerseVAD PoetryID validation passed.
Input VAD: valence 0.2, arousal 0.5, dominance 0.8.
Categorical profile: The Survivor (low, moderate, high).
Nearest-centroid distance: 0.000000.
All 27 distances retained; relative affinities sum to 1.
Export bundle: seven CSV/TXT files and no PoetryID JSON.
```

## Automated coverage

Stage 12 tests cover:

- all 27 unique profile combinations and canonical mappings;
- exact inclusive threshold boundaries and invalid custom profiles;
- categorical and nearest-centroid assignments;
- all 27 sorted distances and normalized inverse-distance affinities;
- high, low, and boundary-sensitive confidence rules;
- insufficient token/type counts and low coverage;
- token/type separation and source/view/configuration identity;
- native-scale concreteness, SUBTLEX-US Zipf, and AoA lexical character;
- missing optional dimensions without changing the VAD profile;
- seven CSV/TXT exports and the absence of PoetryID JSON;
- One Poem dependency reuse through exact upstream VAD analysis IDs;
- schema-4 per-work persistence and project/corpus artifact bundles;
- corpus profile grouping by source, view, weighting, and configuration;
- workbook and existing-module regression behavior.

## Beginner interface check

1. Start VerseVAD with `start_versevad.bat`.
2. Open **One Poem** and paste a poem containing at least five ordinary
   lexical items.
3. Keep at least one VAD lexicon selected.
4. Enable **PoetryID lexical-affective profile**.
5. Leave **All Matched**, token and type weighting, and the default fixed
   thresholds selected.
6. Click **Analyze This Text**, then open **PoetryID**.
7. Confirm that the source, view, weighting, continuous VAD, categorical
   levels, profile, confidence, coverage, maps, scales, and neighbors appear.
8. Open the methods/download expander. Confirm that seven PoetryID CSV/TXT
   files are offered and no PoetryID JSON file is present.
9. Enable one or more of Concreteness, Frequency, or AoA and rerun. Confirm
   their secondary character appears without changing the VAD method.
10. In **Projects & Corpus**, run a batch with PoetryID selected. Confirm that
    the module results include compatible profile distributions, map counts,
    continuous positions, token/type sensitivity, and per-work audit ZIPs.

## Completion record

Completed on 2026-07-24:

- `245 passed` in the complete automated suite, including PoetryID engine,
  integration, export, application, project/corpus, workbook, interface, and
  documentation regressions;
- all ten direct synthetic demonstrations passed, including the
  hand-calculated PoetryID example;
- all 11 local diagnostics passed;
- all five immutable source lexicons retained their expected hashes and passed
  structural inspection;
- concreteness, SUBTLEX-US, Kuperman AoA, and all three CMUdict resource
  contracts passed;
- the offline dependency lock check passed with 86 resolved packages;
- both Word guides rebuilt and passed structural/content tests; the
  accessibility audit reported no high-severity findings and four
  medium-severity layout-table advisories in each guide;
- the canonical DOCX page-image renderer was attempted for both guides but
  could not run because LibreOffice/`soffice` is not installed in this
  environment. No visual-render success is claimed.
