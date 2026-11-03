import json
import sqlite3
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.assessment import AssessmentCreate, AssessmentResult
from app.services.weather import get_weather
from app.services.risk_engine import calculate

router = APIRouter(prefix="/assessments", tags=["Assessments"])


def _owned_farm(db, farm_id: int, user_id: int):
    return db.execute("SELECT * FROM farms WHERE id=? AND owner_id=?", (farm_id, user_id)).fetchone()


@router.post("/run", response_model=AssessmentResult)
async def run(payload: AssessmentCreate, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    farm = _owned_farm(db, payload.farm_id, user["id"])
    if not farm:
        raise HTTPException(404, "Farm not found")

    vals = payload.model_dump()
    snapshot = None
    source = "manual"
    if payload.use_live_weather:
        if farm["latitude"] is None or farm["longitude"] is None:
            raise HTTPException(422, "Farm has no coordinates. Capture GPS or select the location on the Farm page first.")
        try:
            snapshot = await get_weather(farm["latitude"], farm["longitude"])
            source = "live-weather"
            for key in ["temperature_c", "humidity_pct", "rainfall_next_24h_mm", "soil_moisture_pct", "et0_mm"]:
                if snapshot.get(key) is not None:
                    vals[key] = snapshot[key]
        except Exception as exc:
            raise HTTPException(502, f"Live weather unavailable: {exc}. Turn off Live Weather and use manual values.")

    if any(vals.get(k) is None for k in ["temperature_c", "humidity_pct", "rainfall_next_24h_mm"]):
        raise HTTPException(422, "Temperature, humidity and rainfall are required in manual mode")

    latest_scan = None
    disease_source = "default-baseline"
    disease_pct = vals.get("disease_probability_pct")
    if disease_pct is not None:
        disease_source = "manual-override"
    else:
        latest_scan = db.execute(
            "SELECT * FROM disease_scans WHERE farm_id=? AND usable_for_risk=1 ORDER BY id DESC LIMIT 1",
            (farm["id"],),
        ).fetchone()
        if latest_scan:
            disease_pct = latest_scan["disease_risk_pct"]
            disease_source = f"plant-scan:{latest_scan['id']}"

    result = calculate(
        farm_id=farm["id"], crop_stage=farm["crop_stage"], temperature_c=vals["temperature_c"],
        humidity_pct=vals["humidity_pct"], rainfall_mm=vals["rainfall_next_24h_mm"],
        soil_moisture_pct=vals.get("soil_moisture_pct"), disease_pct=disease_pct,
        et0_mm=vals.get("et0_mm"), weather_snapshot=snapshot,
    )
    result.disease_source = disease_source
    if latest_scan:
        result.latest_scan = {
            "scan_id": latest_scan["id"], "label": latest_scan["label"], "plant_part": latest_scan["plant_part"],
            "confidence_pct": latest_scan["confidence_pct"], "disease_risk_pct": latest_scan["disease_risk_pct"],
        }

    cur = db.execute(
        """INSERT INTO assessments(
          farm_id,source,temperature_c,humidity_pct,rainfall_next_24h_mm,soil_moisture_pct,et0_mm,disease_probability_pct,
          weather_risk,water_stress_risk,disease_risk,crop_health_risk,rule_risk,ml_risk,overall_risk,confidence,status,
          explanation_json,actions_json
        ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            farm["id"], source, vals["temperature_c"], vals["humidity_pct"], vals["rainfall_next_24h_mm"], vals.get("soil_moisture_pct"),
            vals.get("et0_mm"), disease_pct, result.risks["weather"], result.risks["water_stress"], result.risks["disease"],
            result.risks["crop_health"], result.rule_risk, result.ml_risk, result.overall_risk, result.confidence, result.status,
            json.dumps([x.model_dump() for x in result.contributors]), json.dumps([x.model_dump() for x in result.actions]),
        ),
    )
    db.commit()
    result.assessment_id = cur.lastrowid
    return result


@router.get("/history/{farm_id}")
def history(farm_id: int, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    farm = _owned_farm(db, farm_id, user["id"])
    if not farm:
        raise HTTPException(404, "Farm not found")
    rows = db.execute("SELECT * FROM assessments WHERE farm_id=? ORDER BY id ASC", (farm_id,)).fetchall()
    return [
        {
            "id": r["id"], "created_at": r["created_at"], "farm_name": farm["name"], "crop": farm["crop"],
            "overall_risk": r["overall_risk"], "confidence": r["confidence"], "status": r["status"],
            "weather": r["weather_risk"], "water": r["water_stress_risk"], "disease": r["disease_risk"],
            "crop_health": r["crop_health_risk"], "source": r["source"],
            "temperature_c": r["temperature_c"], "humidity_pct": r["humidity_pct"],
            "rainfall_next_24h_mm": r["rainfall_next_24h_mm"], "soil_moisture_pct": r["soil_moisture_pct"],
            "et0_mm": r["et0_mm"], "disease_probability_pct": r["disease_probability_pct"],
        }
        for r in rows
    ]


@router.post("/simulate", response_model=AssessmentResult)
async def simulate(payload: AssessmentCreate, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    farm = _owned_farm(db, payload.farm_id, user["id"])
    if not farm:
        raise HTTPException(404, "Farm not found")

    vals = payload.model_dump()
    snapshot = None
    if payload.use_live_weather:
        if farm["latitude"] is None or farm["longitude"] is None:
            raise HTTPException(422, "Farm has no coordinates")
        try:
            snapshot = await get_weather(farm["latitude"], farm["longitude"])
            for key in ["temperature_c", "humidity_pct", "rainfall_next_24h_mm", "soil_moisture_pct", "et0_mm"]:
                if snapshot.get(key) is not None:
                    vals[key] = snapshot[key]
        except Exception as exc:
            raise HTTPException(502, f"Live weather unavailable: {exc}")

    if any(vals.get(k) is None for k in ["temperature_c", "humidity_pct", "rainfall_next_24h_mm"]):
        raise HTTPException(422, "Temperature, humidity and rainfall are required")

    disease_pct = vals.get("disease_probability_pct")
    disease_source = "manual-override" if disease_pct is not None else "default-baseline"
    latest_scan = None
    if disease_pct is None:
        latest_scan = db.execute(
            "SELECT * FROM disease_scans WHERE farm_id=? AND usable_for_risk=1 ORDER BY id DESC LIMIT 1",
            (farm["id"],),
        ).fetchone()
        if latest_scan:
            disease_pct = latest_scan["disease_risk_pct"]
            disease_source = f"plant-scan:{latest_scan['id']}"

    result = calculate(
        farm_id=farm["id"], crop_stage=farm["crop_stage"], temperature_c=vals["temperature_c"],
        humidity_pct=vals["humidity_pct"], rainfall_mm=vals["rainfall_next_24h_mm"],
        soil_moisture_pct=vals.get("soil_moisture_pct"), disease_pct=disease_pct,
        et0_mm=vals.get("et0_mm"), weather_snapshot=snapshot,
    )
    result.disease_source = disease_source
    if latest_scan:
        result.latest_scan = {
            "scan_id": latest_scan["id"], "label": latest_scan["label"], "plant_part": latest_scan["plant_part"],
            "confidence_pct": latest_scan["confidence_pct"], "disease_risk_pct": latest_scan["disease_risk_pct"],
        }
    return result


class TaskToggle(BaseModel):
    task_key: str
    task_date: str
    completed: bool


def _task(key: str, task_date: date, priority: str, title_code: str, reason_code: str) -> dict:
    return {
        "task_key": key,
        "task_date": task_date.isoformat(),
        "priority": priority,
        "title_code": title_code,
        "reason_code": reason_code,
        "completed": False,
    }


@router.get("/action-plan/{farm_id}")
async def action_plan(farm_id: int, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    farm = _owned_farm(db, farm_id, user["id"])
    if not farm:
        raise HTTPException(404, "Farm not found")

    latest = db.execute("SELECT * FROM assessments WHERE farm_id=? ORDER BY id DESC LIMIT 1", (farm_id,)).fetchone()
    scan = db.execute("SELECT * FROM disease_scans WHERE farm_id=? ORDER BY id DESC LIMIT 1", (farm_id,)).fetchone()
    weather = None
    if farm["latitude"] is not None and farm["longitude"] is not None:
        try:
            weather = await get_weather(farm["latitude"], farm["longitude"])
        except Exception:
            weather = None

    today = date.today()
    tasks = [_task("daily_crop_walk", today, "routine", "TASK_DAILY_CROP_WALK", "TASK_REASON_DAILY_MONITORING")]

    if latest:
        if float(latest["water_stress_risk"]) >= 55:
            tasks.append(_task("check_irrigation", today, "immediate" if float(latest["water_stress_risk"]) >= 75 else "today", "TASK_CHECK_IRRIGATION", "TASK_REASON_WATER_RISK"))
        if float(latest["disease_risk"]) >= 45:
            tasks.append(_task("inspect_plant_health", today, "today", "TASK_INSPECT_PLANT_HEALTH", "TASK_REASON_PLANT_RISK"))
        if float(latest["overall_risk"]) >= 70:
            tasks.append(_task("review_high_risk", today, "immediate", "TASK_REVIEW_HIGH_RISK", "TASK_REASON_HIGH_FARM_RISK"))

    alerts = (weather or {}).get("alerts") or []
    alert_codes = {a.get("code") for a in alerts}
    if "HEAVY_RAIN" in alert_codes or "RAIN_WATCH" in alert_codes:
        tasks.append(_task("check_drainage", today, "today", "TASK_CHECK_DRAINAGE", "TASK_REASON_RAIN_ALERT"))
    if "EXTREME_HEAT" in alert_codes or "HEAT_STRESS" in alert_codes:
        tasks.append(_task("heat_protection", today, "today", "TASK_HEAT_PROTECTION", "TASK_REASON_HEAT_ALERT"))

    days = (weather or {}).get("daily") or []
    if len(days) > 1 and float(days[1].get("rain_probability_pct") or 0) >= 60:
        tasks.append(_task("tomorrow_rain_plan", today + timedelta(days=1), "routine", "TASK_TOMORROW_RAIN_PLAN", "TASK_REASON_RAIN_TOMORROW"))

    if scan:
        tasks.append(_task("repeat_plant_scan", today + timedelta(days=2), "routine", "TASK_REPEAT_PLANT_SCAN", "TASK_REASON_TRACK_PROGRESS"))
    else:
        tasks.append(_task("baseline_plant_scan", today, "today", "TASK_BASELINE_PLANT_SCAN", "TASK_REASON_NO_PLANT_SCAN"))

    rows = db.execute(
        "SELECT task_key,task_date,completed FROM action_task_status WHERE farm_id=? AND task_date>=?",
        (farm_id, (today - timedelta(days=1)).isoformat()),
    ).fetchall()
    state = {(r["task_key"], r["task_date"]): bool(r["completed"]) for r in rows}
    for item in tasks:
        item["completed"] = state.get((item["task_key"], item["task_date"]), False)

    tasks.sort(key=lambda x: (x["task_date"], {"immediate": 0, "today": 1, "routine": 2}.get(x["priority"], 3)))
    return {"farm_id": farm_id, "generated_for": today.isoformat(), "tasks": tasks}


@router.post("/action-plan/{farm_id}/toggle")
def toggle_action_task(payload: TaskToggle, farm_id: int, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    farm = _owned_farm(db, farm_id, user["id"])
    if not farm:
        raise HTTPException(404, "Farm not found")
    db.execute(
        """INSERT INTO action_task_status(farm_id,task_key,task_date,completed,updated_at)
           VALUES(?,?,?,?,CURRENT_TIMESTAMP)
           ON CONFLICT(farm_id,task_key,task_date)
           DO UPDATE SET completed=excluded.completed, updated_at=CURRENT_TIMESTAMP""",
        (farm_id, payload.task_key, payload.task_date, int(payload.completed)),
    )
    db.commit()
    return {"ok": True, "completed": payload.completed}
