from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import admin, combinations, health, matches, opportunities, track_record
from app.core.config import settings

app = FastAPI(
    title="Football AI API",
    description=(
        "Predictive football analytics and market-edge detection. "
        "No output field or generated text in this API claims certainty -- "
        "see docs/MODEL.md #8 and docs/API.md."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(matches.router, prefix=settings.api_v1_prefix)
app.include_router(opportunities.router, prefix=settings.api_v1_prefix)
app.include_router(combinations.router, prefix=settings.api_v1_prefix)
app.include_router(track_record.router, prefix=settings.api_v1_prefix)
app.include_router(admin.router, prefix=settings.api_v1_prefix)
