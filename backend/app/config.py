"""Central configuration for the local-only AI Idea Vault backend."""
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
DB_PATH = DATA_DIR / "vault.db"
SOURCE_IMPORTS_DIR = DATA_DIR / "source_imports"
IMPORT_REPORTS_DIR = DATA_DIR / "import_reports"

FRONTEND_DEV_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
APP_NAME = "AI Idea Vault"
APP_VERSION = "0.14.0-phase14"
