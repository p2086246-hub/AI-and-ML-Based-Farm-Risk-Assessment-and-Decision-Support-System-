from typing import Optional
from pydantic import Field, field_validator
from pydantic import BaseModel


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=2, max_length=300)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    crop: str = Field(min_length=2, max_length=100)
    crop_stage: str = Field(default="vegetative", min_length=2, max_length=120)
    area_acres: float = Field(default=1.0, gt=0, le=100000)
    soil_type: str = Field(default="Unknown", max_length=120)
    irrigation_type: str = Field(default="Rainfed", max_length=120)
    irrigation_source: Optional[str] = Field(default=None, max_length=120)
    sowing_date: Optional[str] = None

    @field_validator("name", "location", "crop", "crop_stage", "soil_type", "irrigation_type")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise ValueError("This field is required")
        return value
