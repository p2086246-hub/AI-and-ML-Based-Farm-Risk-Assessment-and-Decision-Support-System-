import sqlite3
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.farm import FarmCreate
from app.services.weather import geocode_location

router = APIRouter(prefix="/farms", tags=["Farms"])


def _farm_dict(row):
    return dict(row) if row else None


@router.get("")
def list_farms(user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    return [dict(r) for r in db.execute("SELECT * FROM farms WHERE owner_id=? ORDER BY id DESC", (user["id"],)).fetchall()]


@router.post("")
async def create_farm(payload: FarmCreate, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    latitude, longitude = payload.latitude, payload.longitude
    if latitude is None or longitude is None:
        try:
            geo = await geocode_location(payload.location)
        except Exception:
            geo = None
        if geo:
            latitude, longitude = geo["latitude"], geo["longitude"]
    cur = db.execute(
        """INSERT INTO farms(owner_id,name,location,latitude,longitude,crop,crop_stage,area_acres,soil_type,irrigation_type,irrigation_source,sowing_date)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user["id"], payload.name, payload.location, latitude, longitude, payload.crop, payload.crop_stage, payload.area_acres,
         payload.soil_type, payload.irrigation_type, payload.irrigation_source, payload.sowing_date),
    )
    db.commit()
    row = db.execute("SELECT * FROM farms WHERE id=?", (cur.lastrowid,)).fetchone()
    return dict(row)


@router.delete("/{farm_id}")
def delete_farm(farm_id: int, user: dict = Depends(get_current_user), db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id FROM farms WHERE id=? AND owner_id=?", (farm_id, user["id"])).fetchone()
    if not row:
        raise HTTPException(404, "Farm not found")
    db.execute("DELETE FROM farms WHERE id=?", (farm_id,)); db.commit()
    return {"ok": True}
