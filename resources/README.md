# Local Poetic Fingerprint Resources

This directory is reserved for locally installed research resources used by
optional VerseVAD modules. Resource data are ignored by source control. Only
this instruction file is tracked.

Current and planned local layout:

```text
resources/
  brysbaert_warriner_kuperman_concreteness_DATA.xlsx
  brysbaert_warriner_kuperman_concreteness_PAPER.pdf
  subtlexus1.zip
  subtlex-us/
    SUBTLEX-US frequency list with PoS and Zipf information.xlsx
  aoa/
  pronunciation/
```

The two concreteness filenames are exact. Keep both directly inside
`resources/`; do not rename or edit them. VerseVAD currently requires the
workbook for the optional Stage 2 one-poem module and retains the paper beside
it as the local methodological reference. The workbook is expected at SHA-256
`1673ead761e28833a40e82c0d20f10782955ced9366d600eafeefee0f2254545`;
the paper is expected at
`7bafeef31b771965dbbbe2dea0227e210c8f4d054461343505f829ecfa036b63`.

The Stage 3 frequency module requires the exact workbook path shown above.
Keep it under `resources/subtlex-us/`; do not rename or edit it. Its expected
SHA-256 is
`3a8cb93a4e28988c2ce722a63f6b8d394acdc42ebe2ab6e1f0e484ee0d4167a7`.
The preserved official download archive `resources/subtlexus1.zip` has
SHA-256
`458128f90a28c4f396cb2a5b23ac93c56f745ee8cfca9be2afedad4091d15090`;
the adapter does not read the archive at analysis time.

Do not place the five existing VAD and emotion lexicons here. They remain
immutable under `source_lexicons/` and continue to be read in place by their
existing adapters.

Each resource adapter must:

1. read its source file in place;
2. compute and record a SHA-256 checksum;
3. record the resource name, edition or version, citation, usage notice, and
   adapter version;
4. keep original source values separate from derived values;
5. report missing, malformed, and unsupported resources in plain language;
6. leave unmatched tokens missing rather than assigning a neutral or zero
   value; and
7. avoid copying a licensed dataset into exports, backups, or source control.

The implemented frequency module uses only the pinned official SUBTLEX-US
Zipf workbook. VerseVAD does not use `wordfreq` as a fallback or alternate
frequency source. Absent word forms remain unmatched with missing values.
