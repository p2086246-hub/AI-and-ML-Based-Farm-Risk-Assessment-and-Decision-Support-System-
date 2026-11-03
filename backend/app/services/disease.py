from __future__ import annotations

import json
import math
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter, ImageOps, ImageStat

from app.core.config import settings
from app.data_crop_catalog import normalize_crop

_session = None
_classes: list[str] | None = None


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return round(max(low, min(high, float(value))), 1)


def _load_image(content: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(content))
        image = ImageOps.exif_transpose(image).convert("RGB")
        if image.width < 64 or image.height < 64:
            raise ValueError("Image is too small. Use a clearer close-up photo.")
        return image
    except Exception as exc:
        raise ValueError(f"Invalid image: {exc}") from exc


def _rgb_features(image: Image.Image) -> dict[str, float]:
    sample = image.copy()
    sample.thumbnail((512, 512))
    arr = np.asarray(sample, dtype=np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    mx = arr.max(axis=2)
    mn = arr.min(axis=2)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0)
    bright = (r + g + b) / 3.0

    green = (g > r * 1.08) & (g > b * 1.05) & (g > 0.20)
    yellow = (r > 0.45) & (g > 0.40) & (b < 0.42) & (np.abs(r - g) < 0.30)
    brown = (r > g * 1.05) & (g > b * 1.12) & (r > 0.18) & (r < 0.78)
    dark = bright < 0.20
    pale = (bright > 0.55) & (sat < 0.22)
    very_bright = bright > 0.90

    gray = ImageOps.grayscale(sample)
    contrast = float(ImageStat.Stat(gray).stddev[0]) / 128.0
    edge_img = gray.filter(ImageFilter.FIND_EDGES)
    edge_mean = float(ImageStat.Stat(edge_img).mean[0]) / 255.0

    return {
        "green_ratio": round(float(green.mean()) * 100, 2),
        "yellow_ratio": round(float(yellow.mean()) * 100, 2),
        "brown_ratio": round(float(brown.mean()) * 100, 2),
        "dark_ratio": round(float(dark.mean()) * 100, 2),
        "pale_ratio": round(float(pale.mean()) * 100, 2),
        "white_background_ratio": round(float(very_bright.mean()) * 100, 2),
        "brightness": round(float(bright.mean()) * 100, 2),
        "saturation": round(float(sat.mean()) * 100, 2),
        "contrast": round(contrast * 100, 2),
        "edge_strength": round(edge_mean * 100, 2),
        "width": image.width,
        "height": image.height,
    }


def _quality(features: dict[str, float]) -> tuple[float, list[str]]:
    score = 100.0
    warnings: list[str] = []
    if min(features["width"], features["height"]) < 224:
        score -= 20
        warnings.append("low_resolution")
    if features["brightness"] < 20:
        score -= 25
        warnings.append("too_dark")
    elif features["brightness"] > 88:
        score -= 18
        warnings.append("too_bright")
    if features["contrast"] < 12:
        score -= 18
        warnings.append("low_contrast_or_blur")
    if features["white_background_ratio"] > 88:
        score -= 20
        warnings.append("subject_may_be_too_small")
    return clamp(score, 20, 100), warnings


def _symptom_boost(symptoms: str) -> dict[str, float]:
    text = (symptoms or "").lower()
    boosts = {k: 0.0 for k in ["healthy_like", "chlorosis_like", "necrosis_lesion_like", "rot_like", "water_stress_like", "physical_damage_like", "uncertain"]}
    groups = {
        "chlorosis_like": ["yellow", "pale", "chlorosis", "पीला", "पील", "पिवळ", "પીળ"],
        "necrosis_lesion_like": ["spot", "brown", "black spot", "lesion", "धब्ब", "भूर", "डाग", "કાળો", "ડાઘ"],
        "rot_like": ["rot", "soft", "smell", "सड़", "गल", "कुज", "સડ"],
        "water_stress_like": ["wilt", "droop", "dry", "curl", "मुरझ", "सूख", "कोरड", "વિલ્ટ", "સૂક"],
        "physical_damage_like": ["hole", "cut", "bite", "insect", "कीट", "छेद", "किड", "ભૂંગળ", "જીવાત"],
        "healthy_like": ["healthy", "normal", "स्वस्थ", "निरोग", "તંદુરસ્ત"],
    }
    for key, words in groups.items():
        for word in words:
            if word in text:
                boosts[key] += 32
    return boosts


def broad_visual_triage(image: Image.Image, plant_part: str, symptoms: str = "") -> dict[str, Any]:
    f = _rgb_features(image)
    quality, warnings = _quality(f)
    boost = _symptom_boost(symptoms)

    scores = {
        "healthy_like": 35 + 0.75 * f["green_ratio"] - 0.55 * f["yellow_ratio"] - 0.75 * f["brown_ratio"] - 0.65 * f["dark_ratio"],
        "chlorosis_like": 15 + 1.45 * f["yellow_ratio"] + 0.30 * f["pale_ratio"] - 0.18 * f["green_ratio"],
        "necrosis_lesion_like": 12 + 1.35 * f["brown_ratio"] + 0.85 * f["dark_ratio"] + 0.22 * f["edge_strength"],
        "rot_like": 8 + 1.15 * f["dark_ratio"] + 0.95 * f["brown_ratio"] + max(0, 35 - f["brightness"]) * 0.7,
        "water_stress_like": 12 + 0.55 * f["pale_ratio"] + max(0, 28 - f["saturation"]) * 0.8 + 0.20 * f["brown_ratio"],
        "physical_damage_like": 8 + 0.45 * f["edge_strength"] + 0.28 * f["dark_ratio"],
        "uncertain": 22,
    }
    for key, value in boost.items():
        scores[key] += value

    # Roots, stems and fruits naturally contain less green; reduce the healthy-green bias.
    if plant_part in {"root", "stem", "fruit_pod", "seed_grain", "flower"}:
        scores["healthy_like"] += 12
        scores["chlorosis_like"] -= 6

    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best_label, best_raw = ordered[0]
    second_raw = ordered[1][1]
    margin = max(0, best_raw - second_raw)
    confidence = clamp(48 + margin * 1.1 + (quality - 60) * 0.18, 35, 88)

    risk_base = {
        "healthy_like": 14,
        "chlorosis_like": 52,
        "necrosis_lesion_like": 68,
        "rot_like": 78,
        "water_stress_like": 55,
        "physical_damage_like": 50,
        "uncertain": 38,
    }[best_label]
    disease_risk = clamp(risk_base * (0.65 + confidence / 200.0), 8, 88)

    if quality < 55:
        warnings.append("low_image_quality")
        confidence = min(confidence, 55)
        disease_risk = min(disease_risk, 65)

    top = [
        {"label": label, "confidence_pct": clamp(42 + max(0, raw - second_raw) * 0.9, 20, 85)}
        for label, raw in ordered[:3]
    ]
    top[0]["confidence_pct"] = confidence

    return {
        "label": best_label,
        "confidence_pct": confidence,
        "disease_risk_pct": disease_risk,
        "top_predictions": top,
        "image_quality_pct": quality,
        "warnings": list(dict.fromkeys(warnings)),
        "metrics": f,
    }


def _read_classes() -> list[str] | None:
    global _classes
    if _classes is not None:
        return _classes
    path = Path(settings.disease_classes_path)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        _classes = [str(x) for x in data]
    elif isinstance(data, dict):
        # Support both {"0":"label"} and {"label":0} formats.
        if all(str(k).isdigit() for k in data.keys()):
            _classes = [str(data[str(i)]) for i in range(len(data))]
        else:
            pairs = sorted(((int(v), str(k)) for k, v in data.items()), key=lambda x: x[0])
            _classes = [label for _, label in pairs]
    else:
        return None
    return _classes


def _get_onnx_session():
    global _session
    if _session is not None:
        return _session
    model_path = Path(settings.disease_model_path)
    if not model_path.exists():
        return None
    try:
        import onnxruntime as ort
        _session = ort.InferenceSession(str(model_path), providers=["CPUExecutionProvider"])
        return _session
    except Exception:
        return None


def _crop_from_model_label(label: str) -> str:
    crop = label.split("___", 1)[0]
    crop = crop.replace("Corn_(maize)", "maize").replace("Pepper,_bell", "bell pepper")
    crop = crop.replace("_", " ").replace("(", " ").replace(")", " ")
    crop = re.sub(r"\s+", " ", crop).strip()
    return normalize_crop(crop)


def _pretty_model_label(label: str) -> str:
    text = label.replace("___", " — ").replace("_", " ")
    text = text.replace("(including sour)", "").replace("Corn (maize)", "Maize")
    return re.sub(r"\s+", " ", text).strip()


def _preprocess_cropguard(image: Image.Image) -> np.ndarray:
    w, h = image.size
    if w < h:
        new_w, new_h = 256, int(round(h * 256 / w))
    else:
        new_h, new_w = 256, int(round(w * 256 / h))
    img = image.resize((new_w, new_h), Image.Resampling.BILINEAR)
    left = max(0, (new_w - 224) // 2)
    top = max(0, (new_h - 224) // 2)
    img = img.crop((left, top, left + 224, top + 224))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    return np.transpose(arr, (2, 0, 1))[None].astype(np.float32)


def specific_leaf_prediction(image: Image.Image, crop_name: str) -> dict[str, Any] | None:
    session = _get_onnx_session()
    classes = _read_classes()
    if session is None or not classes:
        return None

    normalized = normalize_crop(crop_name)
    crop_classes = [label for label in classes if _crop_from_model_label(label) == normalized]
    # One-class crops (e.g. soybean healthy only in PlantVillage) are not useful for diagnosis.
    if len(crop_classes) < 2:
        return {"available": False, "reason": "crop_not_supported_for_specific_diagnosis"}

    batch = _preprocess_cropguard(image)
    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: batch})
    logits = np.asarray(outputs[0]).reshape(-1)
    # Published CropGuard model recommends temperature scaling T=0.591.
    z = logits / 0.591
    z = z - z.max()
    probs = np.exp(z) / np.exp(z).sum()

    order = np.argsort(probs)[::-1]
    top_all = [(classes[int(i)], float(probs[int(i)])) for i in order[:10]]
    top_same = [(label, p) for label, p in top_all if _crop_from_model_label(label) == normalized]
    if not top_same:
        forced = top_all[0]
        return {
            "available": True,
            "crop_match": False,
            "label": _pretty_model_label(forced[0]),
            "confidence_pct": round(forced[1] * 100, 2),
            "top3": [{"label": _pretty_model_label(x), "confidence_pct": round(p * 100, 2)} for x, p in top_all[:3]],
        }

    best_label, best_prob = top_same[0]
    crop_match = _crop_from_model_label(top_all[0][0]) == normalized
    return {
        "available": True,
        "crop_match": crop_match,
        "label_raw": best_label,
        "label": _pretty_model_label(best_label),
        "confidence_pct": round(best_prob * 100, 2),
        "top3": [{"label": _pretty_model_label(x), "confidence_pct": round(p * 100, 2)} for x, p in top_same[:3]],
    }


def analyze_plant_image(content: bytes, crop_name: str, plant_part: str, symptoms: str = "") -> dict[str, Any]:
    image = _load_image(content)
    broad = broad_visual_triage(image, plant_part, symptoms)
    warnings = list(broad["warnings"])
    specific = None
    analysis_mode = "broad_visual_triage"
    final_label = broad["label"]
    final_confidence = broad["confidence_pct"]
    final_risk = broad["disease_risk_pct"]
    top_predictions = broad["top_predictions"]

    if plant_part == "leaf":
        specific = specific_leaf_prediction(image, crop_name)
        if specific is None:
            warnings.append("leaf_specific_model_not_installed")
        elif not specific.get("available", False):
            warnings.append(specific.get("reason", "leaf_specific_model_unavailable"))
        elif not specific.get("crop_match", False):
            warnings.append("leaf_model_crop_mismatch")
        else:
            analysis_mode = "leaf_specific_plus_visual"
            final_label = specific["label"]
            final_confidence = specific["confidence_pct"]
            top_predictions = specific["top3"]
            raw_label = specific.get("label_raw", "").lower()
            if "healthy" in raw_label:
                final_risk = clamp(100 - specific["confidence_pct"], 5, 45)
            else:
                final_risk = clamp(45 + specific["confidence_pct"] * 0.55, 45, 96)

    usable = broad["image_quality_pct"] >= 45 and final_confidence >= 38
    if not usable:
        warnings.append("not_reliable_enough_for_risk")

    return {
        "analysis_mode": analysis_mode,
        "label": final_label,
        "confidence_pct": round(final_confidence, 2),
        "disease_risk_pct": round(final_risk, 2),
        "image_quality_pct": broad["image_quality_pct"],
        "usable_for_risk": usable,
        "top_predictions": top_predictions,
        "broad_visual": {
            "label": broad["label"],
            "confidence_pct": broad["confidence_pct"],
            "disease_risk_pct": broad["disease_risk_pct"],
        },
        "specific_leaf": specific,
        "warnings": list(dict.fromkeys(warnings)),
        "metrics": broad["metrics"],
        "model": "CropGuard ResNet50 (leaf-specific) + AgriTech visual triage" if analysis_mode == "leaf_specific_plus_visual" else "AgriTech visual triage",
    }
