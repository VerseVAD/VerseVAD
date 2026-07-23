"""Build the VerseVAD values and terminology guide from Markdown."""

from pathlib import Path

from build_user_manual import ROOT, build_document_from_source


SOURCE = ROOT / "docs" / "VerseVAD_Values_and_Terminology_Guide_Source.md"
OUTPUT = ROOT / "docs" / "VerseVAD_Values_and_Terminology_Guide.docx"


def build_guide() -> Path:
    return build_document_from_source(
        source=SOURCE,
        output=OUTPUT,
        title="VerseVAD Values and Terminology Guide",
        subject=(
            "Beginner-friendly definitions, formulas, worked examples, and "
            "interpretation guidance for VerseVAD"
        ),
        header_title="VerseVAD Values & Terminology",
        comments=(
            "Generated from "
            "docs/VerseVAD_Values_and_Terminology_Guide_Source.md"
        ),
    )


if __name__ == "__main__":
    print(build_guide())
