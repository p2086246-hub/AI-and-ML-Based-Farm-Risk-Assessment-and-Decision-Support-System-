import json
from pathlib import Path
from fastapi import APIRouter
from app.core.config import BASE_DIR

router=APIRouter(prefix="/research",tags=["Research"])

@router.get("/metrics")
def metrics():
    p=BASE_DIR / "models" / "metrics.json"
    return json.loads(p.read_text()) if p.exists() else {"status":"metrics unavailable"}
