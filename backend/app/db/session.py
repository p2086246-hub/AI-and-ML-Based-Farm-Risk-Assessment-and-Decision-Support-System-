import sqlite3
from pathlib import Path
from app.core.config import settings


def _connect() -> sqlite3.Connection:
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    conn = _connect()
    try:
        yield conn
    finally:
        conn.close()


def create_db_and_tables():
    conn = _connect()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                mobile_no TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                preferred_language TEXT NOT NULL DEFAULT 'en',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mobile_no TEXT NOT NULL,
                purpose TEXT NOT NULL,
                code_hash TEXT NOT NULL,
                created_at_unix INTEGER NOT NULL,
                expires_at_unix INTEGER NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                attempts INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_otp_mobile ON otp_codes(mobile_no, purpose, id DESC);

            CREATE TABLE IF NOT EXISTS farms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                crop TEXT NOT NULL,
                crop_stage TEXT NOT NULL,
                area_acres REAL NOT NULL,
                soil_type TEXT NOT NULL,
                irrigation_type TEXT NOT NULL,
                irrigation_source TEXT,
                sowing_date TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_farms_owner ON farms(owner_id, id DESC);

            CREATE TABLE IF NOT EXISTS disease_scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                crop_name TEXT NOT NULL,
                plant_part TEXT NOT NULL,
                analysis_mode TEXT NOT NULL,
                label TEXT NOT NULL,
                confidence_pct REAL NOT NULL,
                disease_risk_pct REAL NOT NULL,
                image_quality_pct REAL NOT NULL,
                usable_for_risk INTEGER NOT NULL DEFAULT 1,
                specific_label TEXT,
                specific_confidence_pct REAL,
                warnings_json TEXT NOT NULL DEFAULT '[]',
                top_predictions_json TEXT NOT NULL DEFAULT '[]',
                metrics_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(farm_id) REFERENCES farms(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_scans_farm ON disease_scans(farm_id, id DESC);

            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id INTEGER NOT NULL,
                source TEXT NOT NULL DEFAULT 'manual',
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                rainfall_next_24h_mm REAL NOT NULL,
                soil_moisture_pct REAL,
                et0_mm REAL,
                disease_probability_pct REAL,
                weather_risk REAL NOT NULL,
                water_stress_risk REAL NOT NULL,
                disease_risk REAL NOT NULL,
                crop_health_risk REAL NOT NULL,
                rule_risk REAL NOT NULL,
                ml_risk REAL NOT NULL,
                overall_risk REAL NOT NULL,
                confidence REAL NOT NULL,
                status TEXT NOT NULL,
                explanation_json TEXT NOT NULL DEFAULT '[]',
                actions_json TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(farm_id) REFERENCES farms(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_assessments_farm ON assessments(farm_id, id ASC);

            CREATE TABLE IF NOT EXISTS action_task_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id INTEGER NOT NULL,
                task_key TEXT NOT NULL,
                task_date TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(farm_id, task_key, task_date),
                FOREIGN KEY(farm_id) REFERENCES farms(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_action_task_status_farm ON action_task_status(farm_id, task_date DESC);
            """
        )
        conn.commit()
    finally:
        conn.close()
