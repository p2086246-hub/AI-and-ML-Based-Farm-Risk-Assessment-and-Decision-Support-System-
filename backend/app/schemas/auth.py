import re
from pydantic import BaseModel, Field, field_validator


def normalize_mobile(value: str) -> str:
    raw = (value or "").strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 10:
        digits = "91" + digits
    if not (10 <= len(digits) <= 15):
        raise ValueError("Enter a valid mobile number")
    return "+" + digits


class OTPRequest(BaseModel):
    mobile_no: str
    purpose: str = Field(default="forgot_password", pattern="^forgot_password$")

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        return normalize_mobile(value)


class OTPVerifyRequest(BaseModel):
    mobile_no: str
    purpose: str = Field(default="forgot_password", pattern="^forgot_password$")
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        return normalize_mobile(value)


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    mobile_no: str
    password: str = Field(min_length=6, max_length=100)
    preferred_language: str = "en"

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        return normalize_mobile(value)


class LoginRequest(BaseModel):
    mobile_no: str
    password: str

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        return normalize_mobile(value)


class ResetPasswordRequest(BaseModel):
    mobile_no: str
    new_password: str = Field(min_length=6, max_length=100)
    verification_token: str

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile(cls, value: str) -> str:
        return normalize_mobile(value)
