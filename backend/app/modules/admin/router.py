from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import require_admin_key

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin_key)])


@router.post("/import")
def trigger_sheet_import(db: Session = Depends(get_db)):
    """Триггер импорта из Google Sheet (источник истины курации).

    Требует SHEET_CSV_URLS в .env — CSV-export URL вкладок таблицы.
    """
    if not settings.sheet_csv_urls:
        return {"status": "skipped", "detail": "SHEET_CSV_URLS не настроен — см. .env.example"}
    from app.ingest.import_sheet import import_from_urls

    report = import_from_urls(db, settings.sheet_csv_urls.split(","))
    return {"status": "ok", "report": report}
