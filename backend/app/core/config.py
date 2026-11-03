from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]   # project root
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "AgriTech"
    api_v1_prefix: str = "/api/v1"
    database_path: str = str(BACKEND_DIR / "agritech_v7.db")
    secret_key: str = "agritech-v7-change-me-for-production"
    access_token_hours: int = 48
    verification_token_minutes: int = 10
    otp_expire_minutes: int = 5
    otp_resend_seconds: int = 45

    sms_mode: str = "console"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""

    model_path: str = str(BASE_DIR / "models" / "multifactor_xgb.joblib")
    disease_model_path: str = str(BASE_DIR / "models" / "cropguard.onnx")
    disease_classes_path: str = str(BASE_DIR / "models" / "cropguard_classes.json")
    uploads_dir: str = str(BACKEND_DIR / "uploads")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
