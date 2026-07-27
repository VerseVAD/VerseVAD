# Inherited Form Registry Version 2.0

## Scope

Registry version 2.0 contains 169 source-documented profiles. It expands the
initial ten-form validation set across fixed and inherited forms, stanza
structures, rhyme and refrain architectures, syllabic and accentual patterns,
linked and serial forms, historical traditions, and selected modern invented
forms.

No finite registry can establish a universal or permanently exhaustive
taxonomy of poetry. Form names, requirements, variants, transliterations, and
community practices change across periods, languages, and scholarly sources.
The registry is therefore comprehensive by documented profile coverage, not a
claim that every poetic practice is reducible to one closed list.

The authoritative inventory is the versioned `FORM_PROFILES` registry. Users
can inspect the same complete inventory in **All Inherited Forms** or export
`inherited_form_profiles.csv`; this avoids a second static list drifting out of
sync with the implementation.

## Assessment Modes

The registry contains:

- 58 **automatic** profiles whose encoded evidence can support a cautious
  potential-match suggestion;
- 27 **partial** profiles whose important observable structure can be compared
  while named conventions remain interpretive; and
- 84 **manual** profiles with at least one defining contextual, visual,
  linguistic, thematic, or compositional requirement VerseVAD cannot
  responsibly infer.

Manual profiles are not discarded. A user can select any one, read its
traditional definition, inspect every requirement and weight, compare any
observable evidence, and review its sources and limitations. The defining
manual requirement remains missing rather than receiving a zero and the
profile cannot become an automatic suggestion.

## Sources and Definition Policy

Profiles prefer institutional and educational reference sources, especially
the Academy of American Poets glossary and Poetry Foundation glossary.
Specialist or practitioner references supplement the registry for forms not
covered there. Contemporary and nonce-form sources are labeled through their
profile tradition, definition, limitations, and source URL rather than being
presented as timeless universal conventions.

Each profile must include:

- a stable profile ID, display name, family, tradition, and version;
- a concise traditional definition and tooltip definition;
- one or more source URLs;
- required, preferred, and optional rules with visible weights;
- an assessment mode;
- explicit limitations where important conventions are not scored; and
- feature-level expected, detected, score, coverage, explanation, and source
  module evidence at analysis time.

## Ranking and Presentation

Consistency is a weighted mean over available evidence. Evidence coverage is
reported separately. The ranking score uses consistency, coverage, and a
documented assessment-mode factor so a profile supported only by one generic
observation does not outrank a more specific, well-covered match. Missing
pronunciation, meter, rhyme, syllable, or manual evidence stays missing.

Automatic suggestions require the configured consistency, overall evidence,
required-evidence, and contradiction thresholds. Confidence is a rule-based
label, not a probability.

When no profile qualifies, the main table displays only the ten nearest
profiles. **All Inherited Forms** always provides an alphabetical selector over
all 169 profiles, including obviously distant forms. Candidate, feature, and
profile CSV exports also retain the full registry.

## Maintenance

New or revised profiles require source review, an explicit assessment-mode
decision, detector validation where applicable, exact and near-miss fixtures,
missing-evidence checks, export validation, and a registry-version change when
the analytical contract changes.
