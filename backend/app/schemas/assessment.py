from typing import Optional
from pydantic import BaseModel, Field


class AssessmentCreate(BaseModel):
    farm_id: int
    use_live_weather: bool = True
    temperature_c: Optional[float] = Field(default=None, ge=-10, le=60)
    humidity_pct: Optional[float] = Field(default=None, ge=0, le=100)
    rainfall_next_24h_mm: Optional[float] = Field(default=None, ge=0, le=1000)
    soil_moisture_pct: Optional[float] = Field(default=None, ge=0, le=100)
    et0_mm: Optional[float] = Field(default=None, ge=0, le=100)
    disease_probability_pct: Optional[float] = Field(default=None, ge=0, le=100)


class RiskContributor(BaseModel):
    factor: str
    contribution: float
    reason: str


class RecommendedAction(BaseModel):
    code: str
    priority: str
    title: str
    why: str
    when: str


class AssessmentResult(BaseModel):
    assessment_id: int | None = None
    farm_id: int
    overall_risk: float
    status: str
    confidence: float
    rule_risk: float
    ml_risk: float
    risks: dict[str, float]
    contributors: list[RiskContributor]
    actions: list[RecommendedAction]
    weather_snapshot: dict | None = None
    engine_type: str = "hybrid-xgboost-v2"
    disease_source: str = "default"
    latest_scan: dict | None = None
