from pathlib import Path

from versevad.demo import run_demo
from versevad.validation import PHASE1_DEMO_TEXT


def test_documented_demo_text_matches_executable_fixture() -> None:
    fixture = Path("tests/fixtures/phase1_demo.txt").read_text(encoding="utf-8")
    assert fixture == PHASE1_DEMO_TEXT


def test_phase1_demo_runs_and_exports(tmp_path: Path) -> None:
    assert run_demo(tmp_path) == 0
    assert (tmp_path / "token_audit.csv").is_file()
    assert (tmp_path / "coverage.csv").is_file()
    assert (tmp_path / "vad_summary.csv").is_file()
    assert (tmp_path / "analysis_manifest.csv").is_file()
