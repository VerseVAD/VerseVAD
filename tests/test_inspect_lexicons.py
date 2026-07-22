"""Tests for the read-only Phase 0 lexicon inspection utility."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.inspect_lexicons import LexiconSpec, inspect_one


class InspectLexiconsTests(unittest.TestCase):
    def test_valid_file_reports_structure_without_modification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.tsv"
            original = "term\tvalue\nblue sky\t0.25\nstone\t0.75\n"
            source.write_text(original, encoding="utf-8")
            spec = LexiconSpec(
                lexicon_id="fixture",
                relative_path="fixture.tsv",
                delimiter="\t",
                has_header=True,
                term_column="term",
                key_columns=("term",),
                score_columns=("value",),
                expected_score_min=0.0,
                expected_score_max=1.0,
            )

            result = inspect_one(root, spec)

            self.assertEqual(result["rows"], 2)
            self.assertEqual(result["unique_terms"], 2)
            self.assertEqual(result["phrase_rows"], 1)
            self.assertEqual(result["errors"], [])
            self.assertEqual(source.read_text(encoding="utf-8"), original)

    def test_duplicate_and_out_of_range_values_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.tsv"
            source.write_text("term\tvalue\nstone\t0.5\nstone\t1.5\n", encoding="utf-8")
            spec = LexiconSpec(
                lexicon_id="fixture",
                relative_path="fixture.tsv",
                delimiter="\t",
                has_header=True,
                term_column="term",
                key_columns=("term",),
                score_columns=("value",),
                expected_score_min=0.0,
                expected_score_max=1.0,
            )

            result = inspect_one(root, spec)

            self.assertEqual(result["duplicate_keys"], 1)
            self.assertEqual(result["duplicate_row_excess"], 1)
            self.assertEqual(result["out_of_range_scores"], 1)


if __name__ == "__main__":
    unittest.main()
