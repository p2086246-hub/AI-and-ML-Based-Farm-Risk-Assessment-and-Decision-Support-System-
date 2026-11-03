from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import create_db_and_tables
from app.api.routes import auth, farms, weather, assessments, disease, research, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.uploads_dir).mkdir(parents=True, exist_ok=True)
    create_db_and_tables()
    yield


app = FastAPI(title=settings.app_name, version="7.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for router in [health.router, auth.router, farms.router, weather.router, assessments.router, disease.router, research.router]:
    app.include_router(router, prefix=settings.api_v1_prefix if router is not health.router else "")


@app.get("/")
def root():
    return {"message":"AgriTech API","docs":"/docs","version":"7.0.0","features":["farm-risk","auto-weather-centre","easy-location-search","google-map-preview","weather-alerts","spray-window","smart-irrigation","what-if-simulator","camera","gallery","plant-part-visual-ai","leaf-specific-ai","detailed-treatment-guidance","disease-progress-tracker","what-changed-analysis","smart-action-calendar","multilingual","voice-guidance"]}
