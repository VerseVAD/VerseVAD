# Testing VerseVAD

This guide covers user diagnostics, developer tests, optional-resource checks,
and the public-release checklist for VerseVAD 1.0.0.

## User diagnostics

The application’s **Installation Check** reports the runtime, linguistic model,
bundled reference corpus, and installed research resources. Missing optional
datasets disable only the affected modules.

Platform helpers provide the same checks outside the interface:

- Windows: double-click `diagnose_windows.bat`
- macOS: run `./diagnose_macos.command`

Diagnostics do not upload poems or datasets.

## Complete automated suite

After running the platform setup helper, close the running application and
execute the full test suite from the repository root.

Windows PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q
```

macOS or another POSIX shell:

```bash
./.venv/bin/python -m pytest -p no:cacheprovider -q
```

`-p no:cacheprovider` prevents a `.pytest_cache` write during release checks.
The suite uses `src` and the repository root from `pyproject.toml`.

## Focused tests

Examples:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_public_release.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_cross_platform.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ui_app.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_research_library.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_versemap.py -q
```

On macOS, replace the executable with `./.venv/bin/python` and use `/` in file
paths.

## Test design

The automated suite favors small invented fixtures with hand-calculated
answers. It covers:

- text preservation, tokenization, phrases, contractions, and normalization;
- resource validation and exact checksums;
- exact/lemma/mapped matching order and missingness;
- VAD, association, intensity, cumulative load, and coverage;
- concreteness, frequency, AoA, sensorimotor, readability, and lexical style;
- pronunciation review, syllables, meter, rhyme, and inherited forms;
- PoetryID and VerseMap;
- two-poem and multi-poem comparison;
- project/corpus persistence, migrations, aggregation, and deletion;
- Analysis Library saves, historical restoration, notes, and deletion;
- CSV, Word, and audit-bundle exports;
- Streamlit state helpers and workspace rendering contracts;
- Windows/macOS launchers and public-release safeguards.

The engine tests do not require a browser. Interface tests inspect presentation
contracts without turning Streamlit into the calculation layer.

## Optional research resources

Most tests use synthetic fixtures and do not require licensed datasets.
Resource-integration tests skip or report unavailable resources when the
corresponding local file is absent. To test an installed resource:

1. place the unchanged file at the exact path in
   [resource-installation.md](resource-installation.md);
2. run Installation Check;
3. run the relevant focused adapter/module test; and
4. confirm the source hash, source version, adapter version, coverage, and
   unmatched behavior.

Do not test by rewriting or sampling every source lexicon row. The adapter
contract, supported checksum, representative fixtures, boundary conditions,
and known failure modes are the release checks.

## Performance benchmark

The synthetic benchmark uses fixed invented lines and writes only aggregate
timing and cache data under ignored `tmp/` storage:

```powershell
.\.venv\Scripts\python.exe scripts\benchmark_performance.py --quick
```

On macOS, use `./.venv/bin/python`. Wall-clock values are descriptive and
machine-dependent; they are not pass/fail correctness thresholds.

## Manual smoke test

Before a release:

1. Start VerseVAD with the platform launcher.
2. Confirm the top navigation, sidebar, all six themes, and help/settings
   controls remain usable at wide and narrow browser widths.
3. Run one short poem through the default profile.
4. Change lexicon, weighting, and stopword views; confirm the active report
   section remains selected.
5. Run a two-poem comparison and a comparison with at least three poems.
6. Save, reopen, rename, and delete an analysis explicitly.
7. Create or open a local project, analyze at least two poems, select Whole
   Corpus and one poem, then export.
8. Review an ambiguous and an unmatched pronunciation; confirm approved
   overrides update dependent syllable, meter, rhyme, and form evidence.
9. Open VerseMap, Lexicon Explorer, Form Library, Corpus Browser,
   Documentation, and Methodology.
10. Create CSV, Word, and full-audit downloads and inspect their filenames and
    contents.

Use invented or public-domain text during public testing.

## Documentation and repository checks

Run:

```powershell
git diff --check
git status --short
```

Verify:

- Markdown links resolve;
- `README.md`, `CITATION.cff`, `pyproject.toml`, and `src/versevad/__init__.py`
  agree on the release version;
- repository URLs use `https://github.com/VerseVAD/VerseVAD`;
- ignored licensed/private paths have not been staged;
- the Word manual was rebuilt from its tracked source after a manual change;
- launchers contain no computer-specific absolute paths; and
- the complete test suite passes.

## Release checklist

- [ ] Working tree reviewed; unrelated user data is absent.
- [ ] Version and citation metadata agree.
- [ ] New resources have documented provenance and redistribution review.
- [ ] New calculations have synthetic expected-value tests.
- [ ] Migrations preserve older databases and create safe backups.
- [ ] Windows and macOS setup/launch paths remain valid.
- [ ] Documentation describes current behavior and limitations.
- [ ] Word documentation passes structural and visual checks where rendering
      support is available.
- [ ] `git diff --check` passes.
- [ ] Complete pytest suite passes.
- [ ] Commit is pushed and local `HEAD` matches `origin/main`.
