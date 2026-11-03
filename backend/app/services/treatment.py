from __future__ import annotations

from typing import Any

OFFICIAL_PESTICIDE_PORTAL = "https://ppqs.gov.in/"


def _kind_from_result(result: dict[str, Any]) -> str:
    label = str(result.get("label") or "").lower()
    broad = str((result.get("broad_visual") or {}).get("label") or "").lower()
    combined = f"{label} {broad}"

    if "healthy" in combined:
        return "healthy"
    if "huanglongbing" in combined or "citrus greening" in combined:
        return "systemic_no_curative"
    if "virus" in combined or "mosaic" in combined or "yellow leaf curl" in combined:
        return "viral"
    if "bacterial" in combined:
        return "bacterial"
    if "spider mite" in combined or "mite" in combined:
        return "mite"
    if "powdery mildew" in combined:
        return "powdery_mildew"
    if "rust" in combined:
        return "rust"
    if any(x in combined for x in ["blight", "black rot", "scab", "leaf spot", "target spot", "septoria", "leaf mold", "esca", "scorch"]):
        return "fungal"
    if "rot_like" in combined or "rot-like" in combined:
        return "rot_like"
    if "chlorosis" in combined or "yellowing" in combined:
        return "chlorosis"
    if "water_stress" in combined or "water-stress" in combined:
        return "water_stress"
    if "physical_damage" in combined or "pest-damage" in combined:
        return "physical_damage"
    if "necrosis" in combined or "lesion" in combined:
        return "lesion_uncertain"
    return "uncertain"


DETAILS: dict[str, dict[str, Any]] = {
    "healthy": {
        "problem_code": "HEALTHY_OR_LOW_VISIBLE_STRESS",
        "cause_codes": ["NORMAL_VARIATION", "NO_STRONG_VISIBLE_DISEASE_SIGNAL"],
        "symptom_codes": ["NO_MAJOR_VISIBLE_LESION_PATTERN"],
        "prevention_codes": ["CONTINUE_MONITORING", "BALANCED_IRRIGATION", "FIELD_SANITATION"],
        "urgency": "routine",
        "action_codes": ["CONTINUE_MONITORING", "AVOID_UNNECESSARY_SPRAY", "CHECK_WATER_AND_NUTRITION"],
        "chemical": {"recommended": False, "category_code": "NO_CHEMICAL_NEEDED", "reason_code": "CHEMICAL_NOT_JUSTIFIED_LOW_RISK"},
    },
    "viral": {
        "problem_code": "VIRAL_LIKE_PATTERN",
        "cause_codes": ["POSSIBLE_VIRAL_INFECTION", "VECTOR_TRANSMISSION_POSSIBLE", "INFECTED_PLANT_MATERIAL_POSSIBLE"],
        "symptom_codes": ["MOSAIC_OR_CURL_PATTERN", "DISTORTION_OR_YELLOWING"],
        "prevention_codes": ["SANITIZE_TOOLS", "CONTROL_VECTORS_AFTER_IDENTIFICATION", "REMOVE_INFECTED_RESIDUE"],
        "urgency": "today",
        "action_codes": ["ISOLATE_SEVERELY_AFFECTED", "SANITIZE_TOOLS", "CHECK_VECTOR_PRESENCE", "REMOVE_INFECTED_RESIDUE"],
        "chemical": {"recommended": False, "category_code": "NO_CURATIVE_PESTICIDE_FOR_VIRUS", "reason_code": "VIRUS_HAS_NO_DIRECT_CURATIVE_PESTICIDE"},
    },
    "systemic_no_curative": {
        "problem_code": "SYSTEMIC_DISEASE_LIKE_PATTERN",
        "cause_codes": ["SYSTEMIC_INFECTION_POSSIBLE", "VECTOR_TRANSMISSION_POSSIBLE"],
        "symptom_codes": ["GENERAL_YELLOWING_OR_DECLINE", "UNEVEN_GROWTH_PATTERN"],
        "prevention_codes": ["REMOVE_INFECTED_RESIDUE", "CONTROL_VECTORS_AFTER_IDENTIFICATION", "USE_HEALTHY_PLANTING_MATERIAL"],
        "urgency": "today",
        "action_codes": ["ISOLATE_SEVERELY_AFFECTED", "CHECK_VECTOR_PRESENCE", "REMOVE_INFECTED_RESIDUE", "CONFIRM_DIAGNOSIS"],
        "chemical": {"recommended": False, "category_code": "NO_CURATIVE_CHEMICAL_FOR_SYSTEMIC_DISEASE", "reason_code": "SYSTEMIC_DISEASE_REQUIRES_CONFIRMATION_AND_SOURCE_CONTROL"},
    },
    "bacterial": {
        "problem_code": "BACTERIAL_DISEASE_LIKE_PATTERN",
        "cause_codes": ["BACTERIAL_INFECTION_POSSIBLE", "WET_LEAF_SURFACE_CAN_FAVOR_SPREAD", "SPLASH_OR_TOOL_SPREAD_POSSIBLE"],
        "symptom_codes": ["WATER_SOAKED_OR_DARK_LESIONS", "SPOT_OR_BLIGHT_PATTERN"],
        "prevention_codes": ["KEEP_FOLIAGE_DRY", "DISINFECT_TOOLS", "IMPROVE_AIRFLOW"],
        "urgency": "today",
        "action_codes": ["REMOVE_BADLY_AFFECTED_TISSUE", "AVOID_OVERHEAD_IRRIGATION", "IMPROVE_AIRFLOW", "DISINFECT_TOOLS"],
        "chemical": {"recommended": True, "category_code": "REGISTERED_COPPER_BASED_BACTERICIDE", "reason_code": "COPPER_CATEGORY_MAY_SUPPRESS_SOME_BACTERIAL_DISEASES_WHEN_REGISTERED"},
    },
    "mite": {
        "problem_code": "MITE_DAMAGE_LIKE_PATTERN",
        "cause_codes": ["MITE_INFESTATION_POSSIBLE", "HOT_DRY_DUSTY_CONDITIONS_CAN_FAVOR_MITES"],
        "symptom_codes": ["STIPPLING_OR_BRONZING", "UNDERSIDE_DAMAGE_POSSIBLE"],
        "prevention_codes": ["REDUCE_DUST", "CONSERVE_BENEFICIAL_INSECTS", "CHECK_LEAF_UNDERSIDES"],
        "urgency": "today",
        "action_codes": ["CHECK_LEAF_UNDERSIDES", "ISOLATE_HOTSPOTS", "REDUCE_DUST", "CONSERVE_BENEFICIAL_INSECTS"],
        "chemical": {"recommended": True, "category_code": "REGISTERED_MITICIDE_ACARICIDE", "reason_code": "MITICIDE_CATEGORY_IS_RELEVANT_ONLY_AFTER_MITE_CONFIRMATION"},
    },
    "powdery_mildew": {
        "problem_code": "POWDERY_MILDEW_LIKE_PATTERN",
        "cause_codes": ["FUNGAL_INFECTION_POSSIBLE", "DENSE_CANOPY_AND_HUMIDITY_CAN_FAVOR_DISEASE"],
        "symptom_codes": ["WHITE_POWDERY_GROWTH", "LEAF_YELLOWING_OR_CURLING"],
        "prevention_codes": ["IMPROVE_AIRFLOW", "AVOID_EXCESS_NITROGEN", "MONITOR_NEW_LEAVES"],
        "urgency": "today",
        "action_codes": ["REMOVE_HEAVILY_AFFECTED_TISSUE", "IMPROVE_AIRFLOW", "AVOID_EXCESS_NITROGEN", "KEEP_FOLIAGE_DRY"],
        "chemical": {"recommended": True, "category_code": "REGISTERED_SULFUR_OR_MILDEW_FUNGICIDE", "reason_code": "MILDEW_SPECIFIC_FUNGICIDE_CATEGORY_MAY_BE_APPROPRIATE_IF_REGISTERED"},
    },
    "rust": {
        "problem_code": "RUST_DISEASE_LIKE_PATTERN",
        "cause_codes": ["FUNGAL_RUST_INFECTION_POSSIBLE", "HUMIDITY_OR_LEAF_WETNESS_CAN_FAVOR_SPREAD"],
        "symptom_codes": ["RUST_COLORED_PUSTULES_OR_SPOTS", "LEAF_YELLOWING_POSSIBLE"],
        "prevention_codes": ["KEEP_FOLIAGE_DRY", "REMOVE_INFECTED_DEBRIS", "IMPROVE_AIRFLOW"],
        "urgency": "today",
        "action_codes": ["REMOVE_INFECTED_DEBRIS", "KEEP_FOLIAGE_DRY", "IMPROVE_AIRFLOW", "MONITOR_NEW_LEAVES"],
        "chemical": {"recommended": True, "category_code": "REGISTERED_RUST_FUNGICIDE", "reason_code": "RUST_FUNGICIDE_CATEGORY_MAY_LIMIT_FUNGAL_SPREAD_IF_REGISTERED"},
    },
    "fungal": {
        "problem_code": "FUNGAL_DISEASE_LIKE_PATTERN",
        "cause_codes": ["FUNGAL_INFECTION_POSSIBLE", "LEAF_WETNESS_CAN_FAVOR_FUNGAL_SPREAD", "INFECTED_RESIDUE_CAN_REINTRODUCE_DISEASE"],
        "symptom_codes": ["DARK_SPOTS_OR_LESIONS", "YELLOW_HALO_OR_BLIGHT_PATTERN", "TISSUE_NECROSIS_POSSIBLE"],
        "prevention_codes": ["KEEP_FOLIAGE_DRY", "REMOVE_INFECTED_DEBRIS", "IMPROVE_AIRFLOW", "CROP_SANITATION"],
        "urgency": "today",
        "action_codes": ["REMOVE_INFECTED_DEBRIS", "AVOID_LONG_LEAF_WETNESS", "IMPROVE_AIRFLOW", "MONITOR_SPREAD"],
        "chemical": {"recommended": True, "category_code": "REGISTERED_DISEASE_SPECIFIC_FUNGICIDE", "reason_code": "FUNGICIDE_CATEGORY_MAY_BE_RELEVANT_FOR_CONFIRMED_FUNGAL_DISEASE"},
    },
    "rot_like": {
        "problem_code": "ROT_LIKE_TISSUE_DAMAGE",
        "cause_codes": ["EXCESS_MOISTURE_OR_POOR_DRAINAGE_POSSIBLE", "FUNGAL_OR_BACTERIAL_ROT_POSSIBLE", "WOUND_ENTRY_POSSIBLE"],
        "symptom_codes": ["SOFT_OR_DARK_TISSUE", "COLLAPSED_OR_ROTTING_AREA"],
        "prevention_codes": ["IMPROVE_DRAINAGE", "AVOID_WOUNDING", "FIELD_SANITATION"],
        "urgency": "today",
        "action_codes": ["IMPROVE_DRAINAGE", "REMOVE_ROTTING_TISSUE", "AVOID_WOUNDING", "CONFIRM_CAUSE"],
        "chemical": {"recommended": False, "category_code": "CONFIRM_ROT_CAUSE_BEFORE_CHEMICAL", "reason_code": "ROT_CAN_HAVE_MULTIPLE_CAUSES_SO_CHEMICAL_CHOICE_IS_UNSAFE_WITHOUT_CONFIRMATION"},
    },
    "chlorosis": {
        "problem_code": "CHLOROSIS_OR_YELLOWING_PATTERN",
        "cause_codes": ["NUTRIENT_IMBALANCE_POSSIBLE", "ROOT_ZONE_STRESS_POSSIBLE", "PH_OR_WATER_STRESS_POSSIBLE"],
        "symptom_codes": ["GENERAL_OR_INTERVEINAL_YELLOWING", "PALE_TISSUE"],
        "prevention_codes": ["CHECK_NUTRIENT_STATUS", "CHECK_PH", "BALANCED_IRRIGATION"],
        "urgency": "monitor",
        "action_codes": ["CHECK_NUTRIENT_STATUS", "CHECK_ROOT_ZONE_MOISTURE", "CHECK_PH", "COMPARE_MULTIPLE_PLANTS"],
        "chemical": {"recommended": False, "category_code": "NO_PESTICIDE_FOR_UNCONFIRMED_CHLOROSIS", "reason_code": "YELLOWING_IS_NOT_ENOUGH_EVIDENCE_FOR_PESTICIDE"},
    },
    "water_stress": {
        "problem_code": "WATER_STRESS_LIKE_PATTERN",
        "cause_codes": ["LOW_ROOT_ZONE_MOISTURE_POSSIBLE", "HEAT_OR_HIGH_EVAPORATIVE_DEMAND_POSSIBLE", "IRRIGATION_DELIVERY_PROBLEM_POSSIBLE"],
        "symptom_codes": ["WILTING_OR_PALE_TISSUE", "EDGE_SCORCH_OR_DROOPING_POSSIBLE"],
        "prevention_codes": ["CHECK_SOIL_MOISTURE", "CHECK_IRRIGATION_SYSTEM", "MULCH_IF_APPROPRIATE"],
        "urgency": "today",
        "action_codes": ["CHECK_SOIL_MOISTURE", "CHECK_IRRIGATION_SYSTEM", "MULCH_IF_APPROPRIATE", "RECHECK_AFTER_IRRIGATION"],
        "chemical": {"recommended": False, "category_code": "NO_PESTICIDE_FOR_WATER_STRESS", "reason_code": "PESTICIDE_DOES_NOT_CORRECT_WATER_STRESS"},
    },
    "physical_damage": {
        "problem_code": "PHYSICAL_OR_PEST_DAMAGE_PATTERN",
        "cause_codes": ["CHEWING_OR_BORING_PEST_POSSIBLE", "MECHANICAL_DAMAGE_POSSIBLE", "WEATHER_INJURY_POSSIBLE"],
        "symptom_codes": ["HOLES_OR_TORN_TISSUE", "IRREGULAR_DAMAGE_PATTERN"],
        "prevention_codes": ["INSPECT_FOR_PESTS", "PROTECT_DAMAGED_TISSUE", "IDENTIFY_PEST_BEFORE_SPRAY"],
        "urgency": "today",
        "action_codes": ["INSPECT_FOR_PESTS", "CHECK_STEMS_AND_UNDERSIDES", "IDENTIFY_PEST_BEFORE_SPRAY", "PROTECT_DAMAGED_TISSUE"],
        "chemical": {"recommended": False, "category_code": "IDENTIFY_PEST_BEFORE_INSECTICIDE", "reason_code": "INSECTICIDE_CHOICE_REQUIRES_PEST_IDENTIFICATION"},
    },
    "lesion_uncertain": {
        "problem_code": "LESION_PATTERN_BUT_CAUSE_UNCERTAIN",
        "cause_codes": ["FUNGAL_OR_BACTERIAL_CAUSE_POSSIBLE", "PHYSICAL_INJURY_POSSIBLE", "PHOTO_EVIDENCE_INSUFFICIENT"],
        "symptom_codes": ["BROWN_OR_BLACK_LESION", "NECROTIC_TISSUE"],
        "prevention_codes": ["KEEP_FOLIAGE_DRY", "RETAKE_CLEAR_PHOTO", "FIELD_SANITATION"],
        "urgency": "today",
        "action_codes": ["RETAKE_CLOSE_PHOTOS", "REMOVE_SEVERELY_DAMAGED_TISSUE", "KEEP_FOLIAGE_DRY", "CONFIRM_DIAGNOSIS"],
        "chemical": {"recommended": False, "category_code": "NONE_UNTIL_CONFIRMED", "reason_code": "CAUSE_IS_UNCERTAIN_SO_CHEMICAL_IS_NOT_JUSTIFIED"},
    },
    "uncertain": {
        "problem_code": "UNCONFIRMED_PLANT_STRESS",
        "cause_codes": ["PHOTO_EVIDENCE_INSUFFICIENT", "MULTIPLE_CAUSES_POSSIBLE"],
        "symptom_codes": ["NON_SPECIFIC_VISIBLE_STRESS"],
        "prevention_codes": ["RETAKE_CLEAR_PHOTO", "INSPECT_MULTIPLE_PLANTS", "ADD_SYMPTOM_NOTES"],
        "urgency": "monitor",
        "action_codes": ["RETAKE_CLEAR_PHOTO", "INSPECT_MULTIPLE_PLANTS", "ADD_SYMPTOM_NOTES", "CONFIRM_BEFORE_CHEMICAL"],
        "chemical": {"recommended": False, "category_code": "NONE_UNTIL_CONFIRMED", "reason_code": "LOW_DIAGNOSTIC_CERTAINTY"},
    },
}


def build_treatment_guidance(result: dict[str, Any], crop_name: str, plant_part: str) -> dict[str, Any]:
    """Build farmer-facing treatment guidance from the image result.

    No pesticide dose is generated. Chemical guidance is limited to a category and the reason it
    may be relevant. The user must verify the current crop/problem registration and product label.
    """
    kind = _kind_from_result(result)
    risk = float(result.get("disease_risk_pct") or 0)
    confidence = float(result.get("confidence_pct") or 0)
    reliable = bool(result.get("usable_for_risk")) and confidence >= 45
    detail = DETAILS.get(kind, DETAILS["uncertain"])

    common = {
        "kind": kind,
        "crop_name": crop_name,
        "plant_part": plant_part,
        "risk_level": "high" if risk >= 70 else "moderate" if risk >= 40 else "low",
        "risk_pct": round(risk, 1),
        "confidence_pct": round(confidence, 1),
        "official_reference_url": OFFICIAL_PESTICIDE_PORTAL,
        "chemical_safety_code": "VERIFY_LABEL_AND_REGISTRATION",
        "avoid_spray_codes": [
            "AVOID_BEFORE_HEAVY_RAIN",
            "AVOID_DURING_STRONG_WIND",
            "AVOID_WITH_LOW_CONFIDENCE",
            "DO_NOT_EXCEED_PRODUCT_LABEL",
            "USE_PPE_AND_OBSERVE_WAITING_PERIOD",
        ],
    }

    if not reliable:
        return {
            **common,
            "problem_code": "DIAGNOSIS_NOT_RELIABLE_ENOUGH",
            "cause_codes": ["LOW_IMAGE_OR_MODEL_CONFIDENCE", "PHOTO_EVIDENCE_INSUFFICIENT"],
            "symptom_codes": detail.get("symptom_codes", []),
            "prevention_codes": ["RETAKE_CLEAR_PHOTO", "INSPECT_MULTIPLE_PLANTS"],
            "urgency": "today" if risk >= 60 else "monitor",
            "action_codes": ["RETAKE_CLEAR_PHOTO", "INSPECT_MULTIPLE_PLANTS", "CONFIRM_BEFORE_CHEMICAL"],
            "chemical": {
                "recommended": False,
                "category_code": "NONE_UNTIL_CONFIRMED",
                "reason_code": "LOW_DIAGNOSTIC_CERTAINTY",
            },
        }

    return {**common, **detail}
