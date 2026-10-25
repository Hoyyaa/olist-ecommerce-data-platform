"""Small synthetic checks; no real Olist results are asserted."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "profile_sources", Path(__file__).resolve().parents[1] / "scripts/profile_sources.py")
profiler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profiler)


class ProfilingTests(unittest.TestCase):
    def test_summary_is_repeatable_and_preserves_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.csv"
            content = b"id,note\n001,\n001,\n002,  \n003,hello\n"
            path.write_bytes(content)
            result = profiler.profile_csv(path)
            self.assertEqual(result["row_count"], 4)
            self.assertEqual(result["duplicate_rows"], 1)
            self.assertEqual(result["columns"]["id"]["distinct_count"], 3)
            self.assertEqual(result["columns"]["note"],
                             {"missing": 2, "whitespace_only": 1, "distinct_count": 1})
            self.assertEqual(result, profiler.profile_csv(path))
            self.assertEqual(path.read_bytes(), content)

    def test_unusable_csv_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.csv"
            for content in ["", "id,id\nx,x\n", "id,note\nx\n", 'id\n"unfinished']:
                with self.subTest(content=content):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaises((ValueError, profiler.csv.Error)):
                        profiler.profile_csv(path)


if __name__ == "__main__":
    unittest.main()
