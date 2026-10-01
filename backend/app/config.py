"""Central configuration for the IdeaOS backend."""

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Vercel serverless filesystem: only /tmp is writable.
if os.environ.get("VERCEL"):
    DATA_DIR = Path("/tmp/ideaos-data")
else:
    DATA_DIR = BACKEND_DIR / "data"

DB_PATH = DATA_DIR / "vault.db"
SOURCE_IMPORTS_DIR = DATA_DIR / "source_imports"
IMPORT_REPORTS_DIR = DATA_DIR / "import_reports"

# Browser origins allowed to call the API.
# Keep local development origins and the Vercel frontend aliases currently used
# by this project. allow_origin_regex in main.py additionally covers future
# Vercel preview aliases without requiring a backend redeploy for each alias.
FRONTEND_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://idea-sooty-psi.vercel.app",
    "https://idea-git-main-aashish-kushwah-s-projects.vercel.app",
    "https://idea-6oen06ft0-aashish-kushwah-s-projects.vercel.app",
]

APP_NAME = "AI Idea Vault"
APP_VERSION = "0.14.0-phase14"