from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from PIL import Image, ImageDraw

from app.services.risk_engine import calculate
from app.services.disease import analyze_plant_image, specific_leaf_prediction
from app.services.ml_engine import load_model
from app.services.treatment import build_treatment_guidance
from app.services.weather import _spray_window, _farm_alerts, _irrigation_advice

print("[1/6] Loading farm-risk XGBoost model...")
assert load_model() is not None, "Bundled farm-risk model is missing"
print("      OK")

print("[2/6] Running farm-risk inference...")
result = calculate(
    farm_id=1,
    crop_stage="flowering",
    temperature_c=36,
    humidity_pct=48,
    rainfall_mm=1.5,
    soil_moisture_pct=18,
    disease_pct=68,
    et0_mm=6,
)
assert 0 <= result.overall_risk <= 100
assert result.actions
print(f"      OK: overall risk={result.overall_risk}, status={result.status}")

print("[3/6] Running universal plant-photo triage without any external model...")
img = Image.new("RGB", (480, 360), (245, 245, 235))
d = ImageDraw.Draw(img)
d.ellipse((70, 40, 410, 330), fill=(74, 142, 63))
d.ellipse((210, 120, 285, 190), fill=(125, 74, 35))
buf = BytesIO(); img.save(buf, format="JPEG")
scan = analyze_plant_image(buf.getvalue(), "Soybean", "flower", "brown spot")
assert scan["label"] and 0 <= scan["disease_risk_pct"] <= 100
print(f"      OK: {scan['label']} risk={scan['disease_risk_pct']} mode={scan['analysis_mode']}")

print("[4/6] Checking safe treatment guidance...")
scan_for_treatment = dict(scan)
scan_for_treatment["usable_for_risk"] = True
scan_for_treatment["confidence_pct"] = max(60, float(scan_for_treatment.get("confidence_pct") or 0))
treatment = build_treatment_guidance(scan_for_treatment, "Soybean", "flower")
assert treatment.get("action_codes"), "Treatment guidance returned no next steps"
assert "chemical" in treatment, "Treatment guidance returned no chemical decision"
assert treatment["chemical"].get("category_code"), "Chemical category is missing"
print(f"      OK: kind={treatment['kind']} chemical={treatment['chemical']['category_code']}")

print("[5/6] Checking offline weather decision-support helpers...")
base = datetime(2026, 1, 1, 8, 0)
times=[]; temps=[]; humidity=[]; probs=[]; precip=[]; wind=[]; gust=[]; is_day=[]
for i in range(48):
    hour = base + timedelta(hours=i)
    times.append(hour.isoformat())
    temps.append(27.0); humidity.append(55.0); probs.append(5.0); precip.append(0.0)
    wind.append(8.0); gust.append(12.0); is_day.append(1 if 6 <= hour.hour <= 18 else 0)
hourly = {
    "time": times, "temperature_2m": temps, "relative_humidity_2m": humidity,
    "precipitation_probability": probs, "precipitation": precip, "wind_speed_10m": wind,
    "wind_gusts_10m": gust, "is_day": is_day,
}
daily = {"precipitation_sum": [0.0]}
spray = _spray_window(hourly)
assert spray.get("status") in {"good", "caution", "avoid", "unavailable"}
alerts = _farm_alerts(hourly, daily)
irrigation = _irrigation_advice(soil_pct=15, rain24=0, et0=6, temp=36)
assert irrigation.get("code")
print(f"      OK: spray={spray.get('status')} irrigation={irrigation.get('code')} alerts={len(alerts)}")

print("[6/6] Checking optional leaf-specific model status...")
model = ROOT / "models" / "cropguard.onnx"
classes = ROOT / "models" / "cropguard_classes.json"
if model.exists() and classes.exists():
    pil = Image.open(BytesIO(buf.getvalue())).convert("RGB")
    specific = specific_leaf_prediction(pil, "Tomato")
    assert specific is not None and specific.get("available") is True, "Leaf-specific ONNX model could not run"
    print(f"      Installed and callable. prediction={specific.get('label')} confidence={specific.get('confidence_pct')}%")
else:
    print("      Not installed. This is optional: SETUP_WINDOWS.bat attempts to download it.")

print("\nAgriTech V7 backend self-test PASSED.")
