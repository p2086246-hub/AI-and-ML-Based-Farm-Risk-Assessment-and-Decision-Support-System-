import json
import sqlite3
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.disease import analyze_plant_image
from app.services.treatment import build_treatment_guidance
from app.data_crop_catalog import normalize_crop

router = APIRouter(prefix="/disease", tags=["Plant Visual AI"])


@router.post("/analyze")
async def analyze(
    farm_id: int = Form(...),
    crop_name: str = Form(...),
    plant_part: str = Form(...),
    symptoms: str = Form(default=""),
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    farm = db.execute("SELECT * FROM farms WHERE id=? AND owner_id=?", (farm_id, user["id"])).fetchone()
    if not farm:
        raise HTTPException(404, "Farm not found")
    content = await file.read()
    if not content:
        raise HTTPException(422, "Empty image")
    if len(content) > 10_000_000:
        raise HTTPException(413, "Image too large (max 10 MB)")
    if plant_part not in {"leaf", "flower", "fruit_pod", "stem", "root", "whole_plant", "seed_grain", "other"}:
        raise HTTPException(422, "Unsupported plant part")
    try:
        result = analyze_plant_image(content, crop_name.strip(), plant_part, symptoms)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    except Exception as exc:
        raise HTTPException(500, f"Plant image analysis failed: {exc}")

    crop_match_farm = normalize_crop(crop_name) == normalize_crop(farm["crop"])
    if not crop_match_farm:
        result["warnings"].append("scan_crop_does_not_match_farm")
        result["warnings"] = list(dict.fromkeys(result["warnings"]))
        result["usable_for_risk"] = False

    # Build treatment guidance only after reliability and farm/crop validation.
    # This prevents a mismatched or low-quality photo from triggering chemical advice.
    result["treatment"] = build_treatment_guidance(result, crop_name.strip(), plant_part)

    specific = result.get("specific_leaf") if isinstance(result.get("specific_leaf"), dict) else {}
    cur = db.execute(
        """INSERT INTO disease_scans(
            farm_id,filename,crop_name,plant_part,analysis_mode,label,confidence_pct,disease_risk_pct,image_quality_pct,
            usable_for_risk,specific_label,specific_confidence_pct,warnings_json,top_predictions_json,metrics_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            farm_id, file.filename or "plant-photo.jpg", crop_name.strip(), plant_part, result["analysis_mode"], result["label"],
            result["confidence_pct"], result["disease_risk_pct"], result["image_quality_pct"], int(bool(result["usable_for_risk"])),
            specific.get("label"), specific.get("confidence_pct"), json.dumps(result["warnings"], ensure_ascii=False),
            json.dumps(result["top_predictions"], ensure_ascii=False), json.dumps(result["metrics"], ensure_ascii=False),
        ),
    )
    db.commit()
    result.update({"scan_id": cur.lastrowid, "farm_id": farm_id, "crop_name": crop_name.strip(), "plant_part": plant_part})
    return result


@router.get("/latest/{farm_id}")
def latest(farm_id: int, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    farm = db.execute("SELECT id FROM farms WHERE id=? AND owner_id=?", (farm_id, user["id"])).fetchone()
    if not farm:
        raise HTTPException(404, "Farm not found")
    row = db.execute("SELECT * FROM disease_scans WHERE farm_id=? ORDER BY id DESC LIMIT 1", (farm_id,)).fetchone()
    if not row:
        return None
    return {
        "scan_id": row["id"], "crop_name": row["crop_name"], "plant_part": row["plant_part"], "analysis_mode": row["analysis_mode"],
        "label": row["label"], "confidence_pct": row["confidence_pct"], "disease_risk_pct": row["disease_risk_pct"],
        "image_quality_pct": row["image_quality_pct"], "usable_for_risk": bool(row["usable_for_risk"]), "created_at": row["created_at"],
    }


@router.get("/history/{farm_id}")
def scan_history(
    farm_id: int,
    limit: int = 12,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    farm = db.execute("SELECT id FROM farms WHERE id=? AND owner_id=?", (farm_id, user["id"])).fetchone()
    if not farm:
        raise HTTPException(404, "Farm not found")
    limit = max(2, min(int(limit), 50))
    rows = db.execute(
        "SELECT * FROM disease_scans WHERE farm_id=? ORDER BY id DESC LIMIT ?",
        (farm_id, limit),
    ).fetchall()
    return [
        {
            "scan_id": row["id"],
            "crop_name": row["crop_name"],
            "plant_part": row["plant_part"],
            "analysis_mode": row["analysis_mode"],
            "label": row["label"],
            "confidence_pct": row["confidence_pct"],
            "disease_risk_pct": row["disease_risk_pct"],
            "image_quality_pct": row["image_quality_pct"],
            "usable_for_risk": bool(row["usable_for_risk"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@router.get("/progress/{farm_id}")
def scan_progress(
    farm_id: int,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    farm = db.execute("SELECT id FROM farms WHERE id=? AND owner_id=?", (farm_id, user["id"])).fetchone()
    if not farm:
        raise HTTPException(404, "Farm not found")
    latest = db.execute(
        "SELECT * FROM disease_scans WHERE farm_id=? ORDER BY id DESC LIMIT 1",
        (farm_id,),
    ).fetchone()
    if not latest:
        return {"status": "no_scans", "delta": None, "latest": None, "previous": None}
    previous = db.execute(
        """SELECT * FROM disease_scans
           WHERE farm_id=? AND id<? AND lower(crop_name)=lower(?) AND plant_part=?
           ORDER BY id DESC LIMIT 1""",
        (farm_id, latest["id"], latest["crop_name"], latest["plant_part"]),
    ).fetchone()

    def pack(row):
        if not row:
            return None
        return {
            "scan_id": row["id"], "crop_name": row["crop_name"], "plant_part": row["plant_part"],
            "label": row["label"], "risk": row["disease_risk_pct"], "confidence": row["confidence_pct"],
            "quality": row["image_quality_pct"], "usable_for_risk": bool(row["usable_for_risk"]),
            "created_at": row["created_at"],
        }

    if not previous:
        return {"status": "first_scan", "delta": None, "latest": pack(latest), "previous": None}

    delta = round(float(latest["disease_risk_pct"]) - float(previous["disease_risk_pct"]), 1)
    if delta <= -8:
        status = "improving"
    elif delta >= 8:
        status = "worsening"
    else:
        status = "stable"
    return {
        "status": status,
        "delta": delta,
        "latest": pack(latest),
        "previous": pack(previous),
        "note": "Progress compares scan risk for the same crop and plant part; it is not a laboratory measurement of lesion area.",
    }
