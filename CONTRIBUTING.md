# Contributing to VerseVAD

Thank you for helping improve VerseVAD. Contributions should preserve its
central commitment: computational evidence must support close reading without
pretending to replace interpretation.

## Before you begin

1. Read the [documentation index](docs/index.md), especially
   [architecture.md](docs/architecture.md),
   [methodology.md](docs/methodology.md), and [testing.md](docs/testing.md).
2. Open an issue before a large feature, data-model change, new dependency, or
   new research resource adapter.
3. Never commit licensed lexicons, private literary texts, user projects,
   personal corpora, exports, backups, secrets, or generated environments.
4. Confirm that any new bundled text or data can legally be redistributed
   under the proposed terms.

## Development setup

Use the ordinary platform setup helper:

- Windows: `setup_windows.bat`
- macOS: `bash setup_macos.command`

The helpers create `.venv/`, `.runtime/`, and `.tools/` inside the checkout.
Those directories are ignored.

Run the complete suite before opening a pull request:

```powershell
.\.venv\Scripts\python.exe -m pytest -p no:cacheprovider -q
```

On macOS, use `./.venv/bin/python` instead.

## Design and evidence rules

- Keep the analysis engine independent of Streamlit.
- Preserve imported text exactly; normalize only in a separate processing
  representation.
- Treat source lexicons as immutable and record exact source hashes.
- Keep source values separate from derived values.
- Never give unmatched evidence a neutral numeric value.
- Never silently replace an exact surface-form match with a lemma match.
- Report denominators, coverage, missingness, warnings, configuration, model
  version, adapter version, and resource provenance.
- Use cautious scholarly language. A lexical norm is not a contextual emotion,
  intention, authorship judgment, or reader response.
- Add small synthetic fixtures with hand-calculated expected results.
- Keep Windows and macOS paths and launch behavior working.

## Pull requests

A pull request should:

- explain the research or usability problem;
- describe the methodological and interface changes;
- identify new dependencies or data-license implications;
- include or update tests;
- update current documentation and `CHANGELOG.md`;
- avoid unrelated generated files; and
- report the exact test command and result.

Maintainers review correctness, transparency, licensing, privacy, regression
risk, accessibility, cross-platform behavior, and whether the result can be
explained to a humanities researcher.

## Reporting bugs

Include the operating system, VerseVAD version, workspace, enabled modules,
steps to reproduce, the plain-language error, and any relevant terminal
traceback. Do not attach copyrighted poems, licensed lexicons, private notes,
or project databases to a public issue unless you have permission to share
them.
