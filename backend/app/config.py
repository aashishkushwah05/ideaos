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

FRONTEND_DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://idea-sooty-psi.vercel.app",
]

APP_NAME = "AI Idea Vault"
APP_VERSION = "0.14.0-phase14"