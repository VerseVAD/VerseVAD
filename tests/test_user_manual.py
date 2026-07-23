from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


ROOT = Path(__file__).parents[1]
MANUAL = ROOT / "docs" / "VerseVAD_User_Manual.docx"
SOURCE = ROOT / "docs" / "VerseVAD_User_Manual_Source.md"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = f"{{{NS['w']}}}"


def _xml(package: ZipFile, member: str):
    return ElementTree.fromstring(package.read(member))


def test_comprehensive_user_manual_is_current_and_structurally_sound() -> None:
    assert MANUAL.is_file()
    assert MANUAL.stat().st_size > 40_000
    assert SOURCE.is_file()

    with ZipFile(MANUAL) as package:
        names = set(package.namelist())
        assert {
            "word/document.xml",
            "word/styles.xml",
            "word/numbering.xml",
            "word/header1.xml",
            "word/footer1.xml",
        }.issubset(names)
        document = _xml(package, "word/document.xml")
        text = "".join(element.text or "" for element in document.iter(f"{W}t"))
        assert "{{VERSION}}" not in text
        assert "{{DATE}}" not in text
        for required in (
            "Dual VAD reporting and stopwords",
            "Projects & corpus workspace",
            "Lexicon Explorer",
            "Mathematical formulas",
            "Midpoint-centered contribution",
            "Delete a project",
            "phase2_results.json",
        ):
            assert required in text

        section = document.find(".//w:sectPr", NS)
        assert section is not None
        page_size = section.find("w:pgSz", NS)
        page_margins = section.find("w:pgMar", NS)
        assert page_size is not None
        assert page_size.get(f"{W}w") == "12240"
        assert page_size.get(f"{W}h") == "15840"
        assert page_margins is not None
        for side in ("top", "right", "bottom", "left"):
            assert page_margins.get(f"{W}{side}") == "1440"

        tables = document.findall(".//w:tbl", NS)
        assert len(tables) >= 10
        for table in tables:
            width = table.find("w:tblPr/w:tblW", NS)
            indent = table.find("w:tblPr/w:tblInd", NS)
            grid_widths = [
                int(column.get(f"{W}w"))
                for column in table.findall("w:tblGrid/w:gridCol", NS)
            ]
            assert width is not None
            assert width.get(f"{W}type") == "dxa"
            assert int(width.get(f"{W}w")) == 9360
            assert indent is not None
            assert int(indent.get(f"{W}w")) == 120
            assert sum(grid_widths) == 9360
            for row in table.findall("w:tr", NS):
                cell_widths = [
                    int(cell.get(f"{W}w"))
                    for cell in row.findall("w:tc/w:tcPr/w:tcW", NS)
                ]
                assert cell_widths == grid_widths

        numbering = _xml(package, "word/numbering.xml")
        formats = {
            element.get(f"{W}val")
            for element in numbering.iter(f"{W}numFmt")
        }
        assert {"bullet", "decimal"}.issubset(formats)
