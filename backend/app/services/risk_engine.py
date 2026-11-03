from app.schemas.assessment import AssessmentResult, RecommendedAction, RiskContributor
from app.services.ml_engine import predict_ml_risk

def clamp(v, lo=0.0, hi=100.0): return round(max(lo, min(hi, float(v))), 1)

def status(score):
    return "HIGH" if score >= 70 else "MODERATE" if score >= 40 else "LOW"

def calculate(*, farm_id, crop_stage, temperature_c, humidity_pct, rainfall_mm, soil_moisture_pct=None, disease_pct=None, et0_mm=None, weather_snapshot=None):
    temp = float(temperature_c); hum = float(humidity_pct); rain = float(rainfall_mm)
    soil = soil_moisture_pct; disease = 25 if disease_pct is None else float(disease_pct)
    et0 = 4 if et0_mm is None else float(et0_mm)

    heat = max(0, temp - 30) * 5.0
    humid_stress = max(0, hum - 85) * 1.2
    heavy_rain = max(0, rain - 35) * 1.2
    weather = clamp(15 + heat + humid_stress + heavy_rain)

    if soil is None:
        water = clamp(34 + max(0, temp - 30) * 4 + max(0, et0 - 4) * 4 - min(rain, 20) * 1.2)
    else:
        water = clamp(12 + max(0, 24 - float(soil)) * 3.0 + max(0, temp - 30) * 3.0 + max(0, et0 - 4) * 3.5 - min(rain, 20) * 1.3)

    disease_risk = clamp(disease)
    stage_factor = 8 if crop_stage.lower() in {"flowering", "fruiting"} else 3 if crop_stage.lower() in {"growing", "vegetative"} else 0
    crop_health = clamp(0.30 * weather + 0.35 * water + 0.30 * disease_risk + stage_factor)
    rule_risk = clamp(0.25 * weather + 0.30 * water + 0.25 * disease_risk + 0.20 * crop_health)

    ml = predict_ml_risk(
        temperature_c=temp, humidity_pct=hum, rainfall_mm=rain,
        soil_moisture_pct=soil, disease_pct=disease_pct, et0_mm=et0_mm,
        crop_stage=crop_stage,
    )
    ml_risk = ml["score"] if ml else rule_risk
    overall = clamp(0.55 * rule_risk + 0.45 * ml_risk)

    completeness = 70
    if soil is not None: completeness += 10
    if disease_pct is not None: completeness += 10
    if et0_mm is not None: completeness += 5
    model_conf = ml["max_probability"] if ml else 70
    confidence = clamp(0.55 * completeness + 0.45 * model_conf, 45, 96)

    raw = [
        ("water_stress", water, "Water availability, heat and evapotranspiration affect crop stress."),
        ("weather", weather, "Temperature, humidity and rainfall conditions contribute to weather stress."),
        ("disease", disease_risk, "Plant-image evidence or the supplied disease probability contributes to risk."),
        ("crop_health", crop_health, "Crop stage and combined stress signals affect crop-health risk."),
    ]
    raw.sort(key=lambda x: x[1], reverse=True)
    total = sum(max(x[1], 1) for x in raw)
    contributors = [RiskContributor(factor=f, contribution=round(s/total*100,1), reason=r) for f,s,r in raw]

    actions=[]
    if water >= 70:
        actions.append(RecommendedAction(code="IRRIGATE", priority="IMMEDIATE", title="Review irrigation requirement", why="Water-stress indicators are high.", when="Within 12–24 hours"))
    elif water >= 40:
        actions.append(RecommendedAction(code="MONITOR_WATER", priority="TODAY", title="Check moisture and irrigation need", why="Water-stress indicators are moderate.", when="Today"))
    if disease_risk >= 65:
        actions.append(RecommendedAction(code="INSPECT_DISEASE", priority="TODAY", title="Inspect affected crop areas", why="Disease probability is elevated.", when="Today"))
    elif disease_risk >= 40:
        actions.append(RecommendedAction(code="MONITOR_DISEASE", priority="NEXT_2_3_DAYS", title="Monitor disease progression", why="Disease risk is moderate.", when="Next 2–3 days"))
    if weather >= 65:
        actions.append(RecommendedAction(code="WEATHER_OPERATION", priority="TODAY", title="Adjust field operations for weather stress", why="Weather variables indicate elevated stress.", when="Before the next field operation"))
    if not actions:
        actions.append(RecommendedAction(code="ROUTINE", priority="ROUTINE", title="Continue routine crop monitoring", why="No major factor is above the action threshold.", when="Daily"))

    return AssessmentResult(
        farm_id=farm_id, overall_risk=overall, status=status(overall), confidence=confidence,
        rule_risk=rule_risk, ml_risk=ml_risk,
        risks={"weather": weather, "water_stress": water, "disease": disease_risk, "crop_health": crop_health},
        contributors=contributors, actions=actions, weather_snapshot=weather_snapshot,
    )
