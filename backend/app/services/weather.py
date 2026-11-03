from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
NOMINATIM_SEARCH = "https://nominatim.openstreetmap.org/search"


def _safe(values, index, default=None):
    try:
        value = values[index]
        return default if value is None else value
    except Exception:
        return default


def _num(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _iso_hour(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def search_locations(name: str, count: int = 6, language: str = "en") -> list[dict[str, Any]]:
    """Farmer-friendly place search.

    Open-Meteo is excellent for towns/cities used by weather forecasting, while Nominatim adds
    village/locality/address coverage. Results are merged and de-duplicated so a farmer can type
    a village, nearby town, district or locality and then select the exact coordinates.
    """
    query = (name or "").strip()
    if len(query) < 2:
        return []
    count = max(1, min(int(count), 10))
    output: list[dict[str, Any]] = []

    # 1) Weather-geocoding source: fast and well aligned with the forecast API.
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.get(
                GEOCODE,
                params={"name": query, "count": count, "language": language or "en", "format": "json"},
            )
            response.raise_for_status()
            items = response.json().get("results") or []
        for item in items:
            name_part = item.get("name")
            admin2 = item.get("admin2")
            admin1 = item.get("admin1")
            country = item.get("country")
            display = ", ".join([x for x in [name_part, admin2, admin1, country] if x])
            output.append({
                "id": f"om-{item.get('id')}", "name": name_part or query,
                "admin1": admin1, "admin2": admin2, "country": country,
                "country_code": item.get("country_code"), "latitude": item.get("latitude"),
                "longitude": item.get("longitude"), "timezone": item.get("timezone"),
                "display_name": display or query, "provider": "open-meteo",
            })
    except Exception:
        pass

    # 2) Locality/village fallback. Nominatim often resolves smaller Indian villages/localities
    # that are not present in a weather-oriented city index.
    try:
        headers = {"User-Agent": "AgriTechCollegeProject/7.0"}
        async with httpx.AsyncClient(timeout=12, headers=headers) as client:
            response = await client.get(
                NOMINATIM_SEARCH,
                params={
                    "q": query, "format": "jsonv2", "addressdetails": 1,
                    "limit": count, "accept-language": language or "en",
                },
            )
            response.raise_for_status()
            items = response.json() or []
        for item in items:
            address = item.get("address") or {}
            name_part = (
                address.get("village") or address.get("town") or address.get("city")
                or address.get("suburb") or address.get("hamlet") or item.get("name")
                or str(item.get("display_name") or "").split(",")[0]
            )
            admin2 = address.get("state_district") or address.get("county")
            admin1 = address.get("state")
            country = address.get("country")
            output.append({
                "id": f"osm-{item.get('place_id')}", "name": name_part or query,
                "admin1": admin1, "admin2": admin2, "country": country,
                "country_code": address.get("country_code"), "latitude": float(item["lat"]),
                "longitude": float(item["lon"]), "timezone": None,
                "display_name": item.get("display_name") or query, "provider": "openstreetmap",
            })
    except Exception:
        pass

    # De-duplicate places that resolve to nearly the same coordinates and keep the list short.
    seen: set[tuple[float, float]] = set()
    merged: list[dict[str, Any]] = []
    for item in output:
        try:
            key = (round(float(item["latitude"]), 3), round(float(item["longitude"]), 3))
        except Exception:
            continue
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= count:
            break
    return merged


async def geocode_location(name: str):
    items = await search_locations(name, count=1)
    return items[0] if items else None


async def reverse_geocode(latitude: float, longitude: float):
    headers = {"User-Agent": "AgriTechCollegeProject/2.0"}
    params = {
        "lat": latitude,
        "lon": longitude,
        "format": "jsonv2",
        "zoom": 14,
        "addressdetails": 1,
    }
    async with httpx.AsyncClient(timeout=15, headers=headers) as client:
        response = await client.get(NOMINATIM_REVERSE, params=params)
        response.raise_for_status()
        data = response.json()
    address = data.get("address") or {}
    village = (
        address.get("village")
        or address.get("town")
        or address.get("city")
        or address.get("municipality")
        or address.get("suburb")
    )
    district = address.get("state_district") or address.get("county")
    state = address.get("state")
    country = address.get("country")
    compact = ", ".join([x for x in [village, district, state, country] if x])
    return {
        "display_name": data.get("display_name") or compact,
        "compact_name": compact or data.get("display_name") or f"{latitude:.5f}, {longitude:.5f}",
        "latitude": latitude,
        "longitude": longitude,
    }


def _spray_window(hourly: dict[str, list], hours: int = 48) -> dict[str, Any]:
    times = hourly.get("time") or []
    n = min(hours, len(times))
    if n == 0:
        return {"status": "unavailable", "score": 0, "reason_codes": ["NO_FORECAST"]}

    def hour_score(i: int) -> tuple[float, list[str]]:
        temp = _num(_safe(hourly.get("temperature_2m") or [], i, 25), 25)
        humidity = _num(_safe(hourly.get("relative_humidity_2m") or [], i, 60), 60)
        pprob = _num(_safe(hourly.get("precipitation_probability") or [], i, 0), 0)
        precip = _num(_safe(hourly.get("precipitation") or [], i, 0), 0)
        wind = _num(_safe(hourly.get("wind_speed_10m") or [], i, 0), 0)
        gust = _num(_safe(hourly.get("wind_gusts_10m") or [], i, wind), wind)
        is_day = int(_num(_safe(hourly.get("is_day") or [], i, 1), 1))

        reasons: list[str] = []
        score = 100.0
        if is_day != 1:
            score -= 22
            reasons.append("NIGHT")
        if pprob > 20:
            score -= min(45, (pprob - 20) * 0.75)
            reasons.append("RAIN_PROBABILITY")
        if precip > 0.2:
            score -= min(45, precip * 18)
            reasons.append("RAIN_EXPECTED")
        if wind > 15:
            score -= min(45, (wind - 15) * 3.2)
            reasons.append("WINDY")
        if gust > 25:
            score -= min(35, (gust - 25) * 2.2)
            reasons.append("GUSTY")
        if temp > 32:
            score -= min(30, (temp - 32) * 4)
            reasons.append("HOT")
        elif temp < 12:
            score -= min(20, (12 - temp) * 2.5)
            reasons.append("COOL")
        if humidity > 88:
            score -= min(20, (humidity - 88) * 1.6)
            reasons.append("VERY_HUMID")
        return max(0.0, min(100.0, score)), reasons

    best = None
    # Prefer a practical 3-hour daylight window.
    for i in range(max(0, n - 2)):
        group = [hour_score(i + j) for j in range(3)]
        avg = sum(s for s, _ in group) / 3
        dt = _iso_hour(times[i])
        if dt and 5 <= dt.hour <= 18:
            avg += 4
        reasons = list(dict.fromkeys(r for _, rs in group for r in rs))
        item = {"index": i, "score": round(min(100, avg), 1), "reason_codes": reasons}
        if best is None or item["score"] > best["score"]:
            best = item

    if best is None:
        best = {"index": 0, "score": 0.0, "reason_codes": ["NO_FORECAST"]}

    i = best["index"]
    start = _safe(times, i)
    end = _safe(times, min(i + 2, len(times) - 1))
    score = best["score"]
    status = "good" if score >= 75 else "caution" if score >= 50 else "avoid"
    return {
        "status": status,
        "score": score,
        "start_time": start,
        "end_time": end,
        "reason_codes": best["reason_codes"],
        "note": "Weather-only spray suitability. Always follow the pesticide label and local agricultural guidance.",
    }


def _farm_alerts(hourly: dict[str, list], daily: dict[str, list]) -> list[dict[str, Any]]:
    temps = [_num(v) for v in (hourly.get("temperature_2m") or [])[:48] if v is not None]
    humidity = [_num(v) for v in (hourly.get("relative_humidity_2m") or [])[:48] if v is not None]
    gusts = [_num(v) for v in (hourly.get("wind_gusts_10m") or [])[:48] if v is not None]
    pprob = [_num(v) for v in (hourly.get("precipitation_probability") or [])[:48] if v is not None]
    rain24 = _num(_safe(daily.get("precipitation_sum") or [], 0, 0), 0)
    alerts: list[dict[str, Any]] = []

    if temps and max(temps) >= 38:
        alerts.append({"code": "EXTREME_HEAT", "severity": "high", "value": round(max(temps), 1), "unit": "°C"})
    elif temps and max(temps) >= 35:
        alerts.append({"code": "HEAT_STRESS", "severity": "moderate", "value": round(max(temps), 1), "unit": "°C"})
    if temps and min(temps) <= 4:
        alerts.append({"code": "COLD_STRESS", "severity": "moderate", "value": round(min(temps), 1), "unit": "°C"})
    if rain24 >= 35:
        alerts.append({"code": "HEAVY_RAIN", "severity": "high", "value": round(rain24, 1), "unit": "mm"})
    elif rain24 >= 15:
        alerts.append({"code": "RAIN_WATCH", "severity": "moderate", "value": round(rain24, 1), "unit": "mm"})
    if gusts and max(gusts) >= 45:
        alerts.append({"code": "STRONG_WIND", "severity": "high", "value": round(max(gusts), 1), "unit": "km/h"})
    if humidity and sum(1 for h in humidity[:24] if h >= 88) >= 5:
        alerts.append({"code": "DISEASE_FAVORABLE_HUMIDITY", "severity": "moderate", "value": round(max(humidity), 1), "unit": "%"})
    if pprob and max(pprob[:24]) >= 75 and rain24 < 15:
        alerts.append({"code": "RAIN_LIKELY", "severity": "info", "value": round(max(pprob[:24]), 1), "unit": "%"})
    return alerts[:5]


def _irrigation_advice(*, soil_pct: float | None, rain24: float, et0: float | None, temp: float | None) -> dict[str, Any]:
    if rain24 >= 12:
        return {"code": "WAIT_FOR_RAIN", "urgency": "low", "reason_values": {"rain24_mm": round(rain24, 1)}}
    if soil_pct is not None and soil_pct < 18 and rain24 < 5:
        return {
            "code": "IRRIGATE_SOON",
            "urgency": "high",
            "reason_values": {"soil_moisture_pct": round(soil_pct, 1), "rain24_mm": round(rain24, 1), "et0_mm": et0},
        }
    if soil_pct is not None and soil_pct < 28 and (_num(et0, 0) >= 4.5 or _num(temp, 0) >= 33):
        return {
            "code": "CHECK_IRRIGATION",
            "urgency": "moderate",
            "reason_values": {"soil_moisture_pct": round(soil_pct, 1), "rain24_mm": round(rain24, 1), "et0_mm": et0},
        }
    return {
        "code": "MONITOR_IRRIGATION",
        "urgency": "low",
        "reason_values": {"soil_moisture_pct": soil_pct, "rain24_mm": round(rain24, 1), "et0_mm": et0},
    }


async def get_weather(latitude: float, longitude: float):
    """Farmer-friendly weather centre used by Farm, Dashboard, spray planning and risk assessment."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,rain,weather_code,"
            "cloud_cover,pressure_msl,wind_speed_10m,wind_direction_10m,wind_gusts_10m,is_day"
        ),
        "hourly": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,precipitation,"
            "weather_code,cloud_cover,pressure_msl,visibility,wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
            "soil_temperature_0cm,soil_moisture_0_to_1cm,et0_fao_evapotranspiration,uv_index,is_day"
        ),
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,"
            "precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,"
            "sunrise,sunset,et0_fao_evapotranspiration,uv_index_max"
        ),
        "forecast_days": 7,
        "timezone": "auto",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(FORECAST, params=params)
        response.raise_for_status()
        data = response.json()

    current = data.get("current") or {}
    daily = data.get("daily") or {}
    hourly = data.get("hourly") or {}
    hourly_times = hourly.get("time") or []
    current_time = current.get("time")
    current_idx = 0
    if current_time and hourly_times:
        try:
            current_idx = min(range(len(hourly_times)), key=lambda i: abs((_iso_hour(hourly_times[i]) - _iso_hour(current_time)).total_seconds()))
        except Exception:
            current_idx = 0

    soil_raw = _safe(hourly.get("soil_moisture_0_to_1cm") or [], current_idx)
    soil_pct = round(_num(soil_raw) * 100, 1) if soil_raw is not None else None
    soil_temp = _safe(hourly.get("soil_temperature_0cm") or [], current_idx)
    current_uv = _safe(hourly.get("uv_index") or [], current_idx)
    visibility_m = _safe(hourly.get("visibility") or [], current_idx)
    et0_today = _safe(daily.get("et0_fao_evapotranspiration") or [], 0)
    rain24 = _num(_safe(daily.get("precipitation_sum") or [], 0, 0), 0)

    daily_rows = []
    for i, date in enumerate(daily.get("time") or []):
        daily_rows.append(
            {
                "date": date,
                "weather_code": _safe(daily.get("weather_code") or [], i),
                "max_c": _safe(daily.get("temperature_2m_max") or [], i),
                "min_c": _safe(daily.get("temperature_2m_min") or [], i),
                "apparent_max_c": _safe(daily.get("apparent_temperature_max") or [], i),
                "apparent_min_c": _safe(daily.get("apparent_temperature_min") or [], i),
                "rain_mm": _safe(daily.get("precipitation_sum") or [], i),
                "rain_probability_pct": _safe(daily.get("precipitation_probability_max") or [], i),
                "wind_max_kmh": _safe(daily.get("wind_speed_10m_max") or [], i),
                "gust_max_kmh": _safe(daily.get("wind_gusts_10m_max") or [], i),
                "sunrise": _safe(daily.get("sunrise") or [], i),
                "sunset": _safe(daily.get("sunset") or [], i),
                "et0_mm": _safe(daily.get("et0_fao_evapotranspiration") or [], i),
                "uv_index_max": _safe(daily.get("uv_index_max") or [], i),
            }
        )

    hourly_preview = []
    for i in range(min(24, len(hourly_times))):
        hourly_preview.append(
            {
                "time": hourly_times[i],
                "temperature_c": _safe(hourly.get("temperature_2m") or [], i),
                "humidity_pct": _safe(hourly.get("relative_humidity_2m") or [], i),
                "rain_probability_pct": _safe(hourly.get("precipitation_probability") or [], i),
                "precipitation_mm": _safe(hourly.get("precipitation") or [], i),
                "wind_kmh": _safe(hourly.get("wind_speed_10m") or [], i),
                "gust_kmh": _safe(hourly.get("wind_gusts_10m") or [], i),
                "weather_code": _safe(hourly.get("weather_code") or [], i),
                "is_day": _safe(hourly.get("is_day") or [], i),
            }
        )

    snapshot = {
        # Keys kept for the existing farm-risk engine.
        "temperature_c": current.get("temperature_2m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "current_precipitation_mm": current.get("precipitation"),
        "weather_code": current.get("weather_code"),
        "rainfall_next_24h_mm": round(rain24, 2),
        "soil_moisture_pct": soil_pct,
        "et0_mm": round(_num(et0_today), 2) if et0_today is not None else None,
        # Farmer-facing weather-centre fields.
        "latitude": data.get("latitude", latitude),
        "longitude": data.get("longitude", longitude),
        "timezone": data.get("timezone"),
        "current": {
            "time": current.get("time"),
            "temperature_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity_pct": current.get("relative_humidity_2m"),
            "precipitation_mm": current.get("precipitation"),
            "rain_mm": current.get("rain"),
            "weather_code": current.get("weather_code"),
            "cloud_cover_pct": current.get("cloud_cover"),
            "pressure_hpa": current.get("pressure_msl"),
            "wind_kmh": current.get("wind_speed_10m"),
            "wind_direction_deg": current.get("wind_direction_10m"),
            "wind_gust_kmh": current.get("wind_gusts_10m"),
            "is_day": current.get("is_day"),
            "uv_index": current_uv,
            "visibility_km": round(_num(visibility_m) / 1000, 1) if visibility_m is not None else None,
            "soil_temperature_c": soil_temp,
            "soil_moisture_pct": soil_pct,
        },
        "daily": daily_rows,
        "hourly_preview": hourly_preview,
        "spray_window": _spray_window(hourly),
        "alerts": _farm_alerts(hourly, daily),
        "irrigation_advice": _irrigation_advice(
            soil_pct=soil_pct,
            rain24=rain24,
            et0=_num(et0_today) if et0_today is not None else None,
            temp=current.get("temperature_2m"),
        ),
        "data_note": "Weather and modeled soil variables are forecast/model data, not an on-farm sensor measurement.",
    }
    return snapshot
