import sqlite3
import tempfile
import unittest
from pathlib import Path

from app.database import initialize
from app.search import search_facets, search_resources, recent_searches


class Phase5Tests(unittest.TestCase):
    def _db(self):
        root = Path(tempfile.mkdtemp())
        db = root / "vault.db"
        initialize(db)
        with sqlite3.connect(db) as c:
            c.execute("INSERT INTO import_runs(id,source_path,source_sha256,report_path,detected_count,accounted_count,status) VALUES ('r','s','h','p',2,2,'COMPLETE')")
            c.execute("""INSERT INTO resources(id,occurrence_fingerprint,import_run_id,source_location,original_url,platform,original_description,description_confidence,import_status,reasons_json,possible_duplicate_of_json,ai_title,ai_category,ai_subcategory,ai_tags_json,ai_summary,ai_keywords_json,resource_type) VALUES ('1','f1','r','x','https://github.com/a/repo','GitHub','Next.js authentication repository','CERTAIN','IMPORTABLE','[]','[]','Next.js Auth Starter','Development','Next.js','[\"nextjs\",\"auth\"]','Authentication starter','[\"authentication\",\"nextjs\"]','Repository')""")
            c.execute("""INSERT INTO resources(id,occurrence_fingerprint,import_run_id,source_location,original_url,platform,original_description,description_confidence,import_status,reasons_json,possible_duplicate_of_json,ai_title,ai_category,resource_type,favorite) VALUES ('2','f2','r','y','https://youtube.com/watch?v=abc','YouTube','React tutorial','CERTAIN','IMPORTABLE','[]','[]','React Course','Learning','Video',1)""")
            c.commit()
        return db

    def test_full_text_and_filters(self):
        db = self._db()
        result = search_resources(db, q="Next.js authentication")
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], "1")
        result = search_resources(db, platform="YouTube", favorite=True)
        self.assertEqual(result["total"], 1)

    def test_pagination_and_facets(self):
        db = self._db()
        result = search_resources(db, page=1, page_size=1)
        self.assertEqual(result["total"], 2)
        self.assertTrue(result["has_more"])
        facets = search_facets(db)
        self.assertIn("GitHub", facets["platforms"])
        self.assertIn("Repository", facets["resource_types"])

    def test_recent_searches(self):
        db = self._db()
        search_resources(db, q="React")
        search_resources(db, q="React")
        search_resources(db, q="Next.js")
        self.assertEqual(recent_searches(db), ["Next.js", "React"])


if __name__ == "__main__": unittest.main()
