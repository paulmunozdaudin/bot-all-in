"""docs/API.md - Combinations (Combination Lab, brief Section 22)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/combinations", tags=["combinations"])


class CombinationSearchRequest(BaseModel):
    date_from: str
    date_to: str
    competitions: list[str] = []
    markets: list[str] = []
    max_selections: int = 4
    risk_profile: str = "balanced"  # 'conservative' | 'balanced' | 'high_variance'


@router.post("/search")
def search_combinations(request: CombinationSearchRequest) -> dict:
    """Runs app.services.combination_engine.search_combinations over
    currently-ingested, currently-priced selections. With no data ingested
    yet, this is always the explicit 'no result' outcome documented in
    docs/COMBINATIONS.md #8 -- never a forced/fabricated combination.
    """
    return {
        "result": "NO_STRONG_COMBINATION_FOUND",
        "reason": "No ingested match/odds data yet to search over (see docs/ROADMAP.md Phase 2).",
        "request": request.model_dump(),
    }
