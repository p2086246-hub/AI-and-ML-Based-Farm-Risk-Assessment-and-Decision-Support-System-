import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.db.session import get_db
from app.services.weather import geocode_location, get_weather, reverse_geocode, search_locations

router = APIRouter(prefix="/weather", tags=["Weather & Location"])


@router.get("/search")
async def search(
    q: str = Query(min_length=2),
    count: int = Query(default=6, ge=1, le=10),
    language: str = Query(default="en", min_length=2, max_length=5),
    user: dict = Depends(get_current_user),
):
    try:
        return await search_locations(q, count=count, language=language)
    except Exception as exc:
        raise HTTPException(502, f"Location search unavailable: {exc}")


@router.get("/geocode")
async def geocode(location: str = Query(min_length=2), user: dict = Depends(get_current_user)):
    geo = await geocode_location(location)
    if not geo:
        raise HTTPException(404, "Location not found")
    return geo


@router.get("/reverse-geocode")
async def reverse(latitude: float, longitude: float, user: dict = Depends(get_current_user)):
    try:
        return await reverse_geocode(latitude, longitude)
    except Exception:
        return {
            "display_name": f"{latitude:.5f}, {longitude:.5f}",
            "compact_name": f"{latitude:.5f}, {longitude:.5f}",
            "latitude": latitude,
            "longitude": longitude,
        }


@router.get("/preview")
async def preview(latitude: float, longitude: float, user: dict = Depends(get_current_user)):
    try:
        return await get_weather(latitude, longitude)
    except Exception as exc:
        raise HTTPException(502, f"Weather service unavailable: {exc}")


@router.get("/farm/{farm_id}")
async def farm_weather(
    farm_id: int,
    user: dict = Depends(get_current_user),
    db: sqlite3.Connection = Depends(get_db),
):
    farm = db.execute("SELECT * FROM farms WHERE id=? AND owner_id=?", (farm_id, user["id"])).fetchone()
    if not farm:
        raise HTTPException(404, "Farm not found")
    lat, lon = farm["latitude"], farm["longitude"]
    if lat is None or lon is None:
        geo = await geocode_location(farm["location"])
        if not geo:
            raise HTTPException(422, "Could not geocode farm location")
        lat, lon = geo["latitude"], geo["longitude"]
        db.execute("UPDATE farms SET latitude=?,longitude=? WHERE id=?", (lat, lon, farm_id))
        db.commit()
    try:
        return await get_weather(lat, lon)
    except Exception as exc:
        raise HTTPException(502, f"Weather service unavailable: {exc}")
