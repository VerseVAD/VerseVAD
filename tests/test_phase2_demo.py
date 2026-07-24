import csv

from versevad import __version__
from versevad.phase2_demo import run_demo


def test_phase2_demo_runs_all_five_sources_and_exports_bundle(tmp_path) -> None:
    paths = run_demo(tmp_path)
    assert len(paths) == 8
    assert (tmp_path / "phase2_results.json").is_file()
    with (tmp_path / "phase2_manifest.csv").open(
        "r", encoding="utf-8-sig", newline=""
    ) as source:
        rows = list(csv.DictReader(source))
    assert len(rows) == 5
    assert {row["software_version"] for row in rows} == {__version__}
    assert {row["phrase_policy"] for row in rows} == {"phrase_preferred"}
    assert all(row["source_loaded_at_utc"].endswith("+00:00") for row in rows)
