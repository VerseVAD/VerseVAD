# Local Poetic Fingerprint Resources

This directory is reserved for locally installed research resources used by
optional VerseVAD modules. Resource data are ignored by source control. Only
this instruction file is tracked.

Planned local layout:

```text
resources/
  concreteness/
  frequency/
  aoa/
  pronunciation/
```

Do not place the five existing VAD and emotion lexicons here. They remain
immutable under `source_lexicons/` and continue to be read in place by their
existing adapters.

Each future resource adapter must:

1. read its source file in place;
2. compute and record a SHA-256 checksum;
3. record the resource name, edition or version, citation, usage notice, and
   adapter version;
4. keep original source values separate from derived values;
5. report missing, malformed, and unsupported resources in plain language;
6. leave unmatched tokens missing rather than assigning a neutral or zero
   value; and
7. avoid copying a licensed dataset into exports, backups, or source control.

The planned frequency module will use a locally installed, explicitly versioned
SUBTLEX-US source. VerseVAD will not use `wordfreq` as a fallback or alternate
frequency source.
