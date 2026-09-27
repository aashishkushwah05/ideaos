import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import database_summary
from app.import_pipeline import ImportValidationError, import_report
from app.importers.phase2 import run as phase2_run


class Phase3Tests(unittest.TestCase):
    def _report(self, root: Path) -> Path:
        source = root / "source.csv"
        with source.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Record #", "URL", "Description"])
            writer.writerows([
                ["1", "https://www.instagram.com/reel/ABC/?igsh=first", "one"],
                ["2", "https://www.instagram.com/reel/ABC/?igsh=first", "same"],
                ["3", "https://www.instagram.com/reel/ABC/?igsh=second", "variant"],
                ["4", "https://example.com/article", "other"],
            ])
        output = root / "phase2"
        phase2_run(source, output)
        return output / "reconciliation_report.json"

    def test_import_is_atomic_and_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root, database = Path(temp), Path(temp) / "vault.db"
            report = self._report(root)
            first = import_report(report, database)
            self.assertEqual((first["detected"], first["inserted"], first["skipped_existing"]), (4, 4, 0))
            self.assertEqual(database_summary(database)["resources"], 4)
            second = import_report(report, database)
            self.assertEqual((second["inserted"], second["skipped_existing"]), (0, 4))
            self.assertEqual(database_summary(database)["resources"], 4)
            with sqlite3.connect(database) as connection:
                duplicate = connection.execute("SELECT exact_duplicate_of_resource_id FROM resources WHERE import_status = 'EXACT_DUPLICATE'").fetchone()
                self.assertIsNotNone(duplicate[0])

    def test_moved_project_accepts_exact_hash_matched_source_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root, database = Path(temp), Path(temp) / "vault.db"
            report = self._report(root)
            source_dir = root / "data" / "source_imports"
            source_dir.mkdir(parents=True)
            moved_source = source_dir / "source.csv"
            moved_source.write_bytes((root / "source.csv").read_bytes())
            import app.import_pipeline as pipeline
            old = pipeline.SOURCE_IMPORTS_DIR
            pipeline.SOURCE_IMPORTS_DIR = source_dir
            try:
                result = import_report(report, database)
                self.assertEqual(result["inserted"], 4)
            finally:
                pipeline.SOURCE_IMPORTS_DIR = old

    def test_changed_source_refuses_database_import(self):
        with tempfile.TemporaryDirectory() as temp:
            root, database = Path(temp), Path(temp) / "vault.db"
            report = self._report(root)
            (root / "source.csv").write_text("Record #,URL,Description\n1,https://changed.example,new\n", encoding="utf-8")
            with self.assertRaises(ImportValidationError):
                import_report(report, database)
            self.assertFalse(database.exists())


if __name__ == "__main__":
    unittest.main()
