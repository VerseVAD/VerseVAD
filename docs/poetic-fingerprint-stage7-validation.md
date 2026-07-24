# Poetic Fingerprint Stage 7 Validation

## Automated and synthetic coverage

Stage 7 tests cover exact ABAB grouping, perfect and identical rhyme,
masculine/feminine/multisyllabic labels, graded slant, eye rhyme, internal
rhyme, refrains, alliteration, assonance, consonance, stanza and line evidence,
ambiguous/absent/vowelless pronunciations, empty and punctuation-only lines,
coverage, deterministic output, exports, application integration, and the
Streamlit workflow.

Run the hand-calculated local demonstration:

```powershell
.\.venv\Scripts\python.exe -m versevad.phonology_validation
```

Expected output begins:

```text
VerseVAD Stage 7 rhyme and phonological validation passed.
The exact end-rhyme example produced ABAB with 2 perfect pairs.
```

The demonstration generates synthetic pronunciation files in a temporary
directory, confirms that they remain unchanged, and verifies:

1. `cat/hat` and `night/bright` produce ABAB and two perfect masculine pairs;
2. `motion/ocean` produces feminine and multisyllabic evidence;
3. `sit/seat` supplies graded slant evidence but does not create a scheme group;
4. `love/move` supplies eye-rhyme evidence but does not create a scheme group;
5. `cat/hat` within one line produces internal-rhyme evidence;
6. repeated initial consonants, stressed vowels, and consonants produce
   alliteration, assonance, and consonance evidence; and
7. an absent ending remains `?` with 0% ending coverage.

## Beginner-friendly interface check

1. Start VerseVAD with `start_versevad.bat`.
2. Open **One Poem**.
3. Enter a title.
4. Paste:

   ```text
   The bright cat
   A silver night
   The soft hat
   A quiet light
   ```

5. Clear the affective-lexicon selection if you want a Stage 7-only run.
6. Select **Rhyme & phonological patterns**.
7. Click **Analyze this text**.
8. Open **Rhyme & Sound**.
9. Confirm the whole-poem scheme is `ABAB`, ending coverage is shown, and the
   pair evidence labels `cat/hat` and `night/light` as perfect masculine rhyme.
10. Download the full audit bundle and confirm the seven Stage 7 files listed
    in the Stage 7 method note are present.

Interpret this as dictionary-based textual evidence. Do not report that
VerseVAD proved how the poem must be pronounced or performed.

## Completion results

The Stage 7 completion pass on 2026-07-24 produced:

- `215 passed` in the complete automated suite;
- passing Phase 2, Concreteness, SUBTLEX-US Frequency, Kuperman AoA,
  pronunciation, fixed-candidate meter, and Stage 7 synthetic validations;
- all 11 local diagnostics passing;
- all five affective source lexicons passing read-only hash and structure
  inspection;
- all three installed CMUdict resources available at official repository
  commit `74790861f652b15e4ac49015a90074ad62a27690` with their expected
  SHA-256 hashes;
- the offline lock check resolving all 86 packages without a lock change;
- `git diff --check` passing;
- both rebuilt Word guides passing package, content, page-geometry, table-
  geometry, numbering, and required-term tests; and
- both Word guides opening and paginating locally: 42 User Manual pages and 28
  Values and Terminology Guide pages.

The canonical PNG renderer could not run because LibreOffice is not installed.
Microsoft Word opened and paginated both rebuilt files, but its local PDF
export stalled before creating a file. Therefore the Stage 7 checkpoint
records successful structural, accessibility, opening, and pagination checks,
but not a completed page-image visual inspection.
