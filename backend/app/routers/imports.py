from __future__ import annotations

from pathlib import Path
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import DB_PATH
from app.import_pipeline import import_report
from app.importers.phase2 import run as run_phase2

router = APIRouter(prefix="/resources", tags=["resource imports"])


@router.post("/import-csv")
async def import_csv(file: UploadFile = File(...)):
    """Import a CSV source file as individual URL resources.

    Each CSV URL occurrence is processed by the existing deterministic Phase 2
    extractor and then inserted through the existing Phase 3 importer. The CSV
    itself is not stored as a single local-file resource.
    """
    original_name = file.filename or "import.csv"
    if Path(original_name).suffix.lower() != ".csv":
        raise HTTPException(status_code=422, detail="Only CSV files can be imported through this endpoint.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=422, detail="The selected CSV file is empty.")

    try:
        with tempfile.TemporaryDirectory(prefix="ideaos-csv-import-") as temp_dir:
            temp_root = Path(temp_dir)
            source_path = temp_root / original_name
            source_path.write_bytes(file_bytes)
            report_dir = temp_root / "report"
            report = run_phase2(source_path, report_dir)
            imported = import_report(report_dir / "reconciliation_report.json", DB_PATH)
    except (ValueError, FileExistsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"CSV import failed: {exc}") from exc

    return {
        "status": "CREATED",
        "created": imported["inserted"] > 0,
        "imported": True,
        "resource_type": "URL_IMPORT",
        "source_filename": original_name,
        "detected": imported["detected"],
        "inserted": imported["inserted"],
        "skipped_existing": imported["skipped_existing"],
        "buckets": report["buckets"],
        "import_run_id": imported["import_run_id"],
    }
