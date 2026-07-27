# Stage 15 Inherited Form Validation

> Historical validation note: these results validate the original
> ten-profile foundation. Registry version 2.0 expands that foundation to 169
> profiles and adds separate expansion-regression checks.

Validation date: 2026-07-26

## Outcome

The initial ten-profile inherited-form implementation passed its synthetic,
integration, persistence, export, interface, documentation, and full-suite
checks.

## Profile and scoring checks

- The registry contains exactly ten source-backed profiles.
- Exact synthetic villanelle, sestina, and pantoum structures rank their
  intended profiles first.
- An exact Shakespearean-sonnet fixture consumes the existing meter and rhyme
  results and ranks the Elizabethan/Shakespearean profile first.
- A modified refrain case remains graded rather than receiving all-or-nothing
  credit.
- A short three-line poem without required syllable evidence is not promoted
  to the English-language 5-7-5 haiku profile.
- Missing evidence lowers coverage rather than becoming a zero score.
- Candidate tooltips contain the traditional form definition and
  poem-specific agreement evidence.

## Automated results

| Check | Result |
|---|---|
| New Stage 15 tests | 13 passed |
| Application, corpus, repository, and export regressions | 34 passed |
| Design and responsive-table regressions | 6 passed |
| Main end-to-end Streamlit analysis-view regression | 1 passed |
| Complete pytest suite | 315 passed; 0 failed; 0 errors; 0 skipped |
| Standalone inherited-form validator | Passed |
| Runtime-only installation diagnostics | All checks passed |
| `git diff --check` | Passed; only the existing Git CRLF normalization notice for `ui/app.py` was emitted |

The complete pytest count is taken from the generated JUnit report:
315 tests completed in 89.380 seconds with no failures, errors, or skips.

## Export and persistence checks

The one-poem audit bundle was verified to contain exactly these Stage 15
artifacts:

- `inherited_form_summary.csv`
- `inherited_form_candidates.csv`
- `inherited_form_features.csv`
- `inherited_form_profiles.csv`
- `inherited_form_methodology.csv`
- `inherited_form_manifest.csv`
- `inherited_form_report.docx`

No JSON artifact is produced. Project/corpus persistence reconstructs the
module result and its CSV/DOCX artifacts without duplicating pronunciation,
meter, or rhyme processing.

## Manual checks

The Word user manual was rebuilt from its Markdown source. The DOCX
accessibility audit reported zero high-, medium-, or low-severity findings.
A structural open/read check found all new Stage 15 headings, formulas,
definitions, and export entries.

Page-image rendering could not be completed on the validation machine because
LibreOffice/`soffice` was not installed. This is a documentation QA limitation,
not an application runtime dependency.

## Interpretation boundary

These tests validate deterministic behavior against documented fixtures. They
do not establish that the profile weights are universally authoritative or
that every historical/modern instance of a form will be recognized. Expansion
beyond the initial ten profiles should follow corpus-based scholarly review,
false-positive review, and explicit registry versioning.
