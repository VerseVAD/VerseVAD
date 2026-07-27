"""Versioned, source-backed profiles for inherited poetic-form analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


PROFILE_REGISTRY_VERSION = "1.0.0"


class RuleRole(StrEnum):
    """The interpretive importance of one conventional form feature."""

    REQUIRED = "required"
    PREFERRED = "preferred"
    OPTIONAL = "optional"


@dataclass(frozen=True)
class FormRule:
    rule_id: str
    feature_id: str
    label: str
    role: RuleRole
    weight: float
    expected: str
    parameters: tuple[tuple[str, object], ...] = ()

    def __post_init__(self) -> None:
        if not self.rule_id or not self.feature_id or not self.label:
            raise ValueError("Every inherited-form rule requires stable identifiers.")
        if self.weight <= 0:
            raise ValueError("Inherited-form rule weights must be positive.")

    @property
    def parameter_map(self) -> dict[str, object]:
        return dict(self.parameters)


@dataclass(frozen=True)
class FormProfile:
    profile_id: str
    name: str
    family: str
    tradition: str
    definition: str
    tooltip_definition: str
    rules: tuple[FormRule, ...]
    source_urls: tuple[str, ...]
    limitations: tuple[str, ...] = ()
    registry_version: str = PROFILE_REGISTRY_VERSION

    def __post_init__(self) -> None:
        if not self.profile_id or not self.name or not self.definition:
            raise ValueError("An inherited-form profile requires an ID, name, and definition.")
        if not self.rules:
            raise ValueError("An inherited-form profile requires at least one rule.")
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise ValueError("Rule IDs must be unique within a form profile.")
        if not self.source_urls:
            raise ValueError("Every form profile requires at least one source.")


def _rule(
    rule_id: str,
    feature_id: str,
    label: str,
    role: RuleRole,
    weight: float,
    expected: str,
    **parameters: object,
) -> FormRule:
    return FormRule(
        rule_id=rule_id,
        feature_id=feature_id,
        label=label,
        role=role,
        weight=weight,
        expected=expected,
        parameters=tuple(parameters.items()),
    )


POETS_SONNET = "https://poets.org/glossary/sonnet"
POETS_VILLANELLE = "https://poets.org/glossary/villanelle"
POETS_SESTINA = "https://poets.org/glossary/sestina"
POETS_LIMERICK = "https://poets.org/glossary/limerick"
POETS_HAIKU = "https://poets.org/glossary/haiku"
HSA_HAIKU = "https://www.hsa-haiku.org/hsa-definitions-2004.html"
POETS_PANTOUM = "https://poets.org/glossary/pantoum"
FOUNDATION_PANTOUM = "https://www.poetryfoundation.org/education/glossary/pantoum"
POETS_TERZA_RIMA = "https://poets.org/glossary/terza-rima"
POETS_GHAZAL = "https://poets.org/glossary/ghazal"


FORM_PROFILES: tuple[FormProfile, ...] = (
    FormProfile(
        profile_id="elizabethan_sonnet",
        name="Elizabethan / Shakespearean Sonnet",
        family="sonnet",
        tradition="English accentual-syllabic",
        definition=(
            "A fourteen-line English sonnet conventionally organized as three "
            "quatrains and a closing couplet, with ABAB CDCD EFEF GG rhyme and "
            "usually iambic pentameter."
        ),
        tooltip_definition=(
            "Traditionally: 14 lines, usually iambic pentameter, with three "
            "quatrains and a closing couplet rhyming ABAB CDCD EFEF GG."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "14 lines", count=14),
            _rule(
                "rhyme",
                "rhyme_scheme",
                "Rhyme architecture",
                RuleRole.REQUIRED,
                5,
                "ABAB CDCD EFEF GG",
                schemes=("ABABCDCDEFEFGG",),
            ),
            _rule(
                "meter",
                "meter_pattern",
                "Governing meter",
                RuleRole.PREFERRED,
                4,
                "Predominantly iambic pentameter",
                pattern="iambic",
                foot_count=5,
            ),
            _rule(
                "stanzas",
                "stanza_pattern",
                "Printed stanza pattern",
                RuleRole.OPTIONAL,
                1,
                "One 14-line block or 4/4/4/2",
                patterns=((14,), (4, 4, 4, 2)),
            ),
        ),
        source_urls=(POETS_SONNET,),
        limitations=("VerseVAD does not infer a rhetorical or thematic volta.",),
    ),
    FormProfile(
        profile_id="petrarchan_sonnet",
        name="Petrarchan / Italian Sonnet",
        family="sonnet",
        tradition="Italian and English sonnet traditions",
        definition=(
            "A fourteen-line sonnet conventionally divided into octave and "
            "sestet, often rhyming ABBAABBA CDECDE or ABBAABBA CDCDCD."
        ),
        tooltip_definition=(
            "Traditionally: 14 lines divided into an octave and sestet; the "
            "octave commonly rhymes ABBAABBA and the sestet may use CDECDE or CDCDCD."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "14 lines", count=14),
            _rule(
                "rhyme",
                "rhyme_scheme",
                "Rhyme architecture",
                RuleRole.REQUIRED,
                5,
                "ABBAABBA CDECDE or ABBAABBA CDCDCD",
                schemes=("ABBAABBACDECDE", "ABBAABBACDCDCD"),
            ),
            _rule(
                "meter",
                "meter_pattern",
                "Common English meter",
                RuleRole.PREFERRED,
                3,
                "Often iambic pentameter in English",
                pattern="iambic",
                foot_count=5,
            ),
            _rule(
                "stanzas",
                "stanza_pattern",
                "Printed stanza pattern",
                RuleRole.OPTIONAL,
                1,
                "One 14-line block or 8/6",
                patterns=((14,), (8, 6)),
            ),
        ),
        source_urls=(POETS_SONNET,),
        limitations=("VerseVAD does not infer the semantic turn between octave and sestet.",),
    ),
    FormProfile(
        profile_id="spenserian_sonnet",
        name="Spenserian Sonnet",
        family="sonnet",
        tradition="English accentual-syllabic",
        definition=(
            "A fourteen-line English sonnet using interlocking quatrains and a "
            "closing couplet, conventionally ABAB BCBC CDCD EE and usually iambic pentameter."
        ),
        tooltip_definition=(
            "Traditionally: 14 lines, usually iambic pentameter, with interlocking "
            "quatrains and a couplet rhyming ABAB BCBC CDCD EE."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "14 lines", count=14),
            _rule(
                "rhyme",
                "rhyme_scheme",
                "Rhyme architecture",
                RuleRole.REQUIRED,
                5,
                "ABAB BCBC CDCD EE",
                schemes=("ABABBCBCCDCDEE",),
            ),
            _rule(
                "meter",
                "meter_pattern",
                "Governing meter",
                RuleRole.PREFERRED,
                4,
                "Predominantly iambic pentameter",
                pattern="iambic",
                foot_count=5,
            ),
            _rule(
                "stanzas",
                "stanza_pattern",
                "Printed stanza pattern",
                RuleRole.OPTIONAL,
                1,
                "One 14-line block or 4/4/4/2",
                patterns=((14,), (4, 4, 4, 2)),
            ),
        ),
        source_urls=(POETS_SONNET,),
        limitations=("VerseVAD does not infer rhetorical turns.",),
    ),
    FormProfile(
        profile_id="villanelle",
        name="Villanelle",
        family="fixed refrain form",
        tradition="French-derived English fixed form",
        definition=(
            "A nineteen-line form of five tercets and a closing quatrain, using "
            "two rhymes and two refrains whose final appearance closes the poem."
        ),
        tooltip_definition=(
            "Traditionally: 19 lines arranged as five tercets and a quatrain; "
            "lines 1 and 3 recur in alternation and together close the poem, "
            "within an ABA-based two-rhyme scheme."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "19 lines", count=19),
            _rule(
                "stanzas",
                "stanza_pattern",
                "Stanza architecture",
                RuleRole.REQUIRED,
                4,
                "3/3/3/3/3/4",
                patterns=((3, 3, 3, 3, 3, 4),),
            ),
            _rule(
                "refrains",
                "villanelle_refrains",
                "Alternating refrains",
                RuleRole.REQUIRED,
                6,
                "Line 1 at 1/6/12/18; line 3 at 3/9/15/19",
            ),
            _rule(
                "rhyme",
                "rhyme_scheme",
                "Two-rhyme architecture",
                RuleRole.PREFERRED,
                4,
                "ABA ABA ABA ABA ABA ABAA",
                schemes=("ABAABAABAABAABAABAA",),
            ),
        ),
        source_urls=(POETS_VILLANELLE,),
        limitations=("Modified refrains receive partial credit; thematic development is not scored.",),
    ),
    FormProfile(
        profile_id="sestina",
        name="Sestina",
        family="fixed end-word form",
        tradition="Provençal-derived fixed form",
        definition=(
            "A thirty-nine-line form of six sestets and a three-line envoi, "
            "rotating six line-ending words in a prescribed order."
        ),
        tooltip_definition=(
            "Traditionally: six six-line stanzas plus a three-line envoi. Six "
            "end-words rotate ABCDEF / FAEBDC / CFDABE / ECBFAD / DEACFB / BDFECA; "
            "all six return in the envoi."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "39 lines", count=39),
            _rule(
                "stanzas",
                "stanza_pattern",
                "Stanza architecture",
                RuleRole.REQUIRED,
                5,
                "6/6/6/6/6/6/3",
                patterns=((6, 6, 6, 6, 6, 6, 3),),
            ),
            _rule(
                "rotation",
                "sestina_rotation",
                "End-word rotation",
                RuleRole.REQUIRED,
                8,
                "ABCDEF / FAEBDC / CFDABE / ECBFAD / DEACFB / BDFECA",
            ),
            _rule(
                "envoi",
                "sestina_envoi",
                "Envoi end-word return",
                RuleRole.PREFERRED,
                4,
                "All six end-words return; ECA or ACE at line ends",
            ),
        ),
        source_urls=(POETS_SESTINA,),
        limitations=("VerseVAD detects normalized lexical end-words, not semantic transformation of repetition.",),
    ),
    FormProfile(
        profile_id="limerick",
        name="Limerick",
        family="comic stanza form",
        tradition="English-language popular verse",
        definition=(
            "A five-line form conventionally rhyming AABBA, with longer first, "
            "second, and fifth lines and shorter third and fourth lines, often in anapestic meter."
        ),
        tooltip_definition=(
            "Traditionally: five lines rhyming AABBA; lines 1, 2, and 5 are "
            "longer, lines 3 and 4 shorter, with a strong anapestic tendency."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "5 lines", count=5),
            _rule(
                "rhyme",
                "rhyme_scheme",
                "Rhyme scheme",
                RuleRole.REQUIRED,
                5,
                "AABBA",
                schemes=("AABBA",),
            ),
            _rule(
                "length",
                "limerick_length_relation",
                "Long/short line relationship",
                RuleRole.PREFERRED,
                3,
                "Lines 1/2/5 longer than 3/4",
            ),
            _rule(
                "meter",
                "limerick_meter",
                "Metrical tendency",
                RuleRole.PREFERRED,
                3,
                "Anapestic trimeter tendency in 1/2/5 and dimeter in 3/4",
            ),
        ),
        source_urls=(POETS_LIMERICK,),
        limitations=("Comic tone, narrative closure, and performance timing are not scored.",),
    ),
    FormProfile(
        profile_id="english_575_haiku",
        name="English-Language 5–7–5 Haiku Profile",
        family="short-form profile",
        tradition="English-language adaptation of Japanese haiku",
        definition=(
            "A deliberately narrow English-language classroom profile: three "
            "lines with a 5–7–5 syllable pattern. It is not a general definition of haiku."
        ),
        tooltip_definition=(
            "This profile tests the English-language 5–7–5 convention: three "
            "short lines with 5, 7, and 5 syllables. Traditional Japanese haiku "
            "uses sound units (on), and many English-language haiku do not use strict 5–7–5."
        ),
        rules=(
            _rule("lines", "line_count_exact", "Line count", RuleRole.REQUIRED, 5, "3 lines", count=3),
            _rule(
                "syllables",
                "syllable_pattern",
                "Syllable profile",
                RuleRole.REQUIRED,
                6,
                "5/7/5 syllables",
                counts=(5, 7, 5),
            ),
            _rule(
                "brevity",
                "maximum_total_syllables",
                "Brevity",
                RuleRole.PREFERRED,
                2,
                "Approximately 17 resolved syllables",
                maximum=19,
            ),
        ),
        source_urls=(POETS_HAIKU, HSA_HAIKU),
        limitations=(
            "Kigo, kireji, juxtaposition, image, and Japanese on are not scored.",
            "A high score indicates 5–7–5 structural resemblance, not definitive haiku identity.",
        ),
    ),
    FormProfile(
        profile_id="pantoum",
        name="Pantoum",
        family="repeating-line form",
        tradition="Malay-derived French and English form",
        definition=(
            "A sequence of quatrains in which the second and fourth lines of "
            "each stanza become the first and third lines of the next."
        ),
        tooltip_definition=(
            "Traditionally: linked quatrains where stanza lines 2 and 4 recur as "
            "lines 1 and 3 of the following stanza; the ending often circles back "
            "to lines from the opening stanza."
        ),
        rules=(
            _rule(
                "stanzas",
                "quatrain_sequence",
                "Quatrain architecture",
                RuleRole.REQUIRED,
                5,
                "At least three four-line stanzas",
                minimum=3,
            ),
            _rule(
                "repetition",
                "pantoum_repetition",
                "Interstanza line repetition",
                RuleRole.REQUIRED,
                7,
                "Each stanza's lines 2/4 recur as the next stanza's lines 1/3",
            ),
            _rule(
                "closure",
                "pantoum_closure",
                "Circular closure",
                RuleRole.PREFERRED,
                2,
                "Opening lines return in the final stanza",
            ),
        ),
        source_urls=(POETS_PANTOUM, FOUNDATION_PANTOUM),
        limitations=("Line substitutions and translated variants receive graded rather than binary credit.",),
    ),
    FormProfile(
        profile_id="terza_rima",
        name="Terza Rima",
        family="interlocking stanza form",
        tradition="Italian-derived stanza form",
        definition=(
            "A sequence of tercets linked by interlocking rhyme, conventionally "
            "ABA BCB CDC and continuing, sometimes closed by a final line or couplet."
        ),
        tooltip_definition=(
            "Traditionally: interlocking tercets rhyming ABA BCB CDC and so on. "
            "English examples often use iambic pentameter and may add a terminal line or couplet."
        ),
        rules=(
            _rule(
                "stanzas",
                "terza_stanzas",
                "Tercet architecture",
                RuleRole.REQUIRED,
                4,
                "Linked tercets, optionally with a terminal line or couplet",
            ),
            _rule(
                "rhyme",
                "terza_rhyme",
                "Interlocking rhyme",
                RuleRole.REQUIRED,
                7,
                "ABA BCB CDC …",
            ),
            _rule(
                "meter",
                "meter_pattern",
                "Common English meter",
                RuleRole.PREFERRED,
                3,
                "Often iambic pentameter in English",
                pattern="iambic",
                foot_count=5,
            ),
            _rule(
                "length",
                "line_length_uniformity",
                "Line-length regularity",
                RuleRole.OPTIONAL,
                1,
                "Broadly consistent line length",
            ),
        ),
        source_urls=(POETS_TERZA_RIMA,),
        limitations=("English slant rhyme receives partial credit; rhetorical progression is not scored.",),
    ),
    FormProfile(
        profile_id="ghazal",
        name="Ghazal",
        family="couplet form",
        tradition="Arabic-, Persian-, Urdu-, and English-language traditions",
        definition=(
            "A sequence of autonomous couplets conventionally linked by a "
            "repeated refrain (radif), a preceding rhyme (qafia), and consistent line length."
        ),
        tooltip_definition=(
            "Traditionally: usually 5–15 autonomous couplets of consistent length. "
            "Both lines of the opening couplet and the second line of later couplets "
            "end with a repeated radif preceded by the qafia rhyme; a signature couplet may close it."
        ),
        rules=(
            _rule(
                "couplets",
                "ghazal_architecture",
                "Couplet architecture",
                RuleRole.REQUIRED,
                5,
                "5–15 couplets",
                minimum=5,
                maximum=15,
            ),
            _rule(
                "radif_qafia",
                "ghazal_radif_qafia",
                "Radif and qafia",
                RuleRole.REQUIRED,
                8,
                "Opening two lines and later even lines repeat a radif after qafia rhyme",
            ),
            _rule(
                "length",
                "line_length_uniformity",
                "Line-length regularity",
                RuleRole.PREFERRED,
                2,
                "Broadly consistent line length",
            ),
        ),
        source_urls=(POETS_GHAZAL,),
        limitations=(
            "Couplet semantic autonomy and the optional maqta/signature are not scored.",
            "This profile models shared formal markers without collapsing distinct ghazal traditions.",
        ),
    ),
)


FORM_PROFILE_BY_ID = {profile.profile_id: profile for profile in FORM_PROFILES}

if len(FORM_PROFILE_BY_ID) != 10:
    raise RuntimeError("Inherited-form registry version 1 must contain exactly ten profiles.")


__all__ = [
    "FORM_PROFILES",
    "FORM_PROFILE_BY_ID",
    "PROFILE_REGISTRY_VERSION",
    "FormProfile",
    "FormRule",
    "RuleRole",
]
