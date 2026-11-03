# Central catalogue used only for suggestions. Crop names themselves remain free text.

GENERIC_STAGES = [
    "sowing_planting", "germination_emergence", "seedling", "vegetative",
    "flowering", "fruit_pod_tuber_development", "grain_seed_filling",
    "ripening", "maturity", "harvest",
]

KNOWN_STAGES = {
    "soybean": ["germination_emergence", "vegetative", "flowering", "pod_formation", "seed_filling", "maturity", "harvest"],
    "wheat": ["germination_emergence", "tillering", "stem_elongation", "booting", "heading_flowering", "grain_seed_filling", "maturity", "harvest"],
    "rice": ["germination_emergence", "seedling", "tillering", "panicle_initiation", "flowering", "grain_seed_filling", "maturity", "harvest"],
    "maize": ["germination_emergence", "vegetative", "tasseling", "silking", "grain_seed_filling", "maturity", "harvest"],
    "tomato": ["nursery_seedling", "vegetative", "flowering", "fruit_set", "fruit_development", "ripening", "harvest"],
    "potato": ["sprouting", "vegetative", "tuber_initiation", "tuber_bulking", "maturity", "harvest"],
    "cotton": ["germination_emergence", "vegetative", "squaring", "flowering", "boll_development", "boll_opening", "harvest"],
    "onion": ["germination_emergence", "vegetative", "bulb_initiation", "bulb_development", "maturity", "harvest"],
    "chickpea": ["germination_emergence", "vegetative", "flowering", "pod_formation", "seed_filling", "maturity", "harvest"],
    "mustard": ["germination_emergence", "rosette", "stem_elongation", "flowering", "pod_formation", "maturity", "harvest"],
    "sugarcane": ["germination_emergence", "tillering", "grand_growth", "maturity", "harvest"],
}

IRRIGATION_TYPES = [
    "Rainfed", "Drip", "Subsurface drip", "Micro-sprinkler", "Sprinkler",
    "Furrow", "Flood", "Basin", "Check basin", "Border strip",
    "Alternate wetting and drying", "Center pivot", "Lateral move",
    "Manual hose/watering can", "Other",
]

IRRIGATION_SOURCES = [
    "Rainfall", "Canal", "Borewell/Tube well", "Open well", "Farm pond",
    "River/Stream", "Tank/Reservoir", "Treated reuse water", "Other",
]

SOIL_TYPES = [
    "Black soil", "Red soil", "Alluvial soil", "Sandy soil", "Loamy soil",
    "Clay soil", "Silty soil", "Peaty soil", "Chalky soil", "Mixed/Unknown",
]

PLANT_PARTS = ["leaf", "flower", "fruit_pod", "stem", "root", "whole_plant", "seed_grain", "other"]


def normalize_crop(value: str) -> str:
    raw = (value or "").strip().lower().replace("-", " ").replace("_", " ")
    raw = " ".join(raw.split())
    aliases = {
        "soyabean": "soybean", "soy bean": "soybean",
        "corn": "maize", "makka": "maize", "mक्का": "maize",
        "capsicum": "bell pepper", "bellpepper": "bell pepper", "pepper bell": "bell pepper",
        "paddy": "rice",
    }
    return aliases.get(raw, raw)


def stages_for_crop(crop: str) -> list[str]:
    return KNOWN_STAGES.get(normalize_crop(crop), GENERIC_STAGES)
