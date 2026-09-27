import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.ai_organization import OrganizationResult, _clean_cloude, organize_pending, validate_organization
from app.database import initialize

class FakeProvider:
    name = "fake"
    model = "test-model"
    def organize(self, payload):
        assert payload["url"]
        assert "cloud hosting" in (payload["description"] or "")
        return OrganizationResult("Claude resource", "AI", "AI assistants", ["claude", "ai"], ["learning"], _clean_cloude(payload["description"]), "Useful AI resource", ["claude", "assistant"])

class Phase4Tests(unittest.TestCase):
    def test_schema_adds_ai_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "vault.db"
            initialize(db)
            with sqlite3.connect(db) as c:
                columns = {r[1] for r in c.execute("PRAGMA table_info(resources)")}
                self.assertIn("ai_title", columns)
                self.assertIn("ai_status", columns)

    def test_validation_is_strict(self):
        valid = {"title":"x","category":"AI","subcategory":None,"tags":["a"],"use_cases":[],"cleaned_description":None,"summary":None,"keywords":[]}
        self.assertEqual(validate_organization(valid).category, "AI")
        invalid = dict(valid, category="Made Up")
        with self.assertRaises(ValueError): validate_organization(invalid)

    def test_cloude_correction_does_not_change_cloud(self):
        value = _clean_cloude("cloude skill for cloud hosting and cloude code")
        self.assertIn("Claude Skill", value)
        self.assertIn("Claude Code", value)
        self.assertIn("cloud hosting", value)

    def test_only_pending_resources_are_processed_and_original_data_stays(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "vault.db"
            initialize(db)
            with sqlite3.connect(db) as c:
                c.execute("INSERT INTO import_runs(id,source_path,source_sha256,report_path,detected_count,accounted_count,status) VALUES ('r','s','h','p',1,1,'COMPLETE')")
                c.execute("INSERT INTO resources(id,occurrence_fingerprint,import_run_id,source_location,original_url,platform,original_description,description_confidence,import_status,reasons_json,possible_duplicate_of_json) VALUES ('1','f','r','x','https://example.com','Website','cloude skill for cloud hosting','CERTAIN','IMPORTABLE','[]','[]')")
                c.commit()
            result = organize_pending(db, FakeProvider(), 25)
            self.assertEqual(result, {"requested":1,"succeeded":1,"failed":0})
            with sqlite3.connect(db) as c:
                row = c.execute("SELECT original_url,original_description,ai_title,ai_status,ai_tags_json FROM resources WHERE id='1'").fetchone()
                self.assertEqual(row[0], "https://example.com")
                self.assertEqual(row[1], "cloude skill for cloud hosting")
                self.assertEqual(row[2], "Claude resource")
                self.assertEqual(row[3], "COMPLETE")
                self.assertEqual(json.loads(row[4]), ["claude","ai"])

if __name__ == "__main__": unittest.main()
