# Updating an existing VerseVAD installation

You do not need to delete VerseVAD, redownload the whole project, reinstall
research resources, or recreate projects when the existing folder is a Git
clone. Pull the new tracked application files into the same folder, then run
the setup helper once to synchronize only any changed locked dependencies.

Before updating:

1. Finish or export any temporary Single Poem work.
2. Close the VerseVAD browser tab and launcher window.
3. Leave `source_lexicons/`, installed files under `resources/`, `projects/`,
   `.runtime/`, `.tools/`, and `.venv/` in place.
4. Do not use Git clean, hard reset, or manually replace the whole folder.

Those local-data and environment paths are intentionally excluded by
`.gitignore`. A normal fetch and pull updates tracked application files without
removing the ignored research resources or project database.

## GitHub Desktop on Windows or macOS

1. Open GitHub Desktop and select **VerseVAD**.
2. Confirm **Current Branch** is `main`.
3. If the **Changes** tab shows edits to tracked source or documentation,
   commit them first or stop and decide whether to keep them. Installed
   lexicons and projects should not appear there.
4. Click **Fetch origin**.
5. When it changes to **Pull origin**, click **Pull origin**.
6. In the updated VerseVAD folder, run the setup helper:

   - Windows: double-click `setup_windows.bat`.
   - macOS: open Terminal in the folder and run
     `bash setup_macos.command`.

7. Launch VerseVAD normally and run **Installation Check** if the update
   changed dependencies or research-resource support.

The setup helper reuses the project-local download cache and environment. Its
locked synchronization installs, removes, or changes Python packages only as
needed to match `uv.lock`. It does not alter research resources, projects,
exports, or backups.

## Terminal update on macOS

For a clone in the Mac Documents folder:

```bash
cd ~/Documents/VerseVAD
git status
git fetch origin
git pull --ff-only origin main
bash setup_macos.command
./start_versevad.command
```

Read the `git status` result before pulling. If it reports tracked local
changes, commit them or ask for help rather than discarding them. The
`--ff-only` safeguard stops instead of creating an unexpected merge commit.

## PowerShell update on Windows

For a clone in the Windows Documents folder:

```powershell
Set-Location "$HOME\Documents\VerseVAD"
git status
git fetch origin
git pull --ff-only origin main
.\setup_windows.bat
.\start_versevad.bat
```

If `git status` reports tracked local changes, commit them or ask for help
before pulling.

## Check whether the folder is a Git clone

Run this from inside the VerseVAD folder:

```bash
git rev-parse --is-inside-work-tree
```

`true` means the in-place update instructions above apply. An error saying the
folder is not a Git repository usually means VerseVAD was obtained with
**Download ZIP** rather than cloned.

A ZIP download has no Git history or remote, so it cannot receive a normal
pull. For one-time migration, clone
`https://github.com/nickybennett/VerseVAD.git` with GitHub Desktop into a new
folder, then copy only the private ignored data you need from the ZIP folder
into the matching locations in the clone:

- `source_lexicons/`
- installed dataset files under `resources/`
- `projects/`
- any wanted `exports/`, `backups/`, or `data/private/`

Run the setup helper in the new clone. Keep the old folder until VerseVAD opens
and the projects and resources are confirmed. Future updates can then use
**Fetch origin** and **Pull origin** without another migration.

## What an ordinary update preserves

- licensed lexicons and supplementary datasets;
- local SQLite projects, text versions, analyses, and review scenarios;
- saved exports and backups;
- operating-system-specific runtime downloads and caches; and
- the existing environment when it remains compatible.

The updater does not migrate a virtual environment between operating systems.
If the same checkout is copied from Windows to macOS or between computers, the
setup helper may rebuild only `.venv/`; it still preserves research data and
projects.
