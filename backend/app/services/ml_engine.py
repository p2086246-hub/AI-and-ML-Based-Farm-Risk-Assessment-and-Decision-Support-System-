from pathlib import Path
import joblib
import numpy as np
from app.core.config import settings

_model = None


def stage_code(stage: str) -> int:
    s = (stage or "").lower()
    if any(k in s for k in ["seed", "germ", "sow", "plant", "sprout", "nursery"]):
        return 0
    if any(k in s for k in ["veget", "tiller", "growth", "elong", "rosette"]):
        return 1
    if any(k in s for k in ["flower", "heading", "tassel", "silk", "squar", "panicle"]):
        return 2
    if any(k in s for k in ["fruit", "pod", "tuber", "boll", "grain", "seed filling", "bulb", "ripen", "matur", "harvest"]):
        return 3
    return 1


def load_model():
    global _model
    if _model is None:
        path = Path(settings.model_path)
        if path.exists():
            _model = joblib.load(path)
    return _model


def predict_ml_risk(*, temperature_c, humidity_pct, rainfall_mm, soil_moisture_pct, disease_pct, et0_mm, crop_stage):
    model = load_model()
    if model is None:
        return None
    x = np.array([[
        float(temperature_c),
        float(humidity_pct),
        float(rainfall_mm),
        float(soil_moisture_pct if soil_moisture_pct is not None else 24),
        float(disease_pct if disease_pct is not None else 25),
        float(et0_mm if et0_mm is not None else 4),
        float(stage_code(crop_stage)),
    ]])
    probs = model.predict_proba(x)[0]
    score = float(probs[0] * 20 + probs[1] * 55 + probs[2] * 85)
    return {
        "score": round(score, 1),
        "max_probability": round(float(probs.max()) * 100, 1),
        "probabilities": probs.tolist(),
    }
