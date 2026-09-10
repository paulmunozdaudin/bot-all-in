"""docs/API.md - Opportunities (Market Scanner, brief Section 21)."""
from __future__ import annotations

from fastapi import APIRouter, Query

router = APIRouter(prefix="/opportunities", tags=["opportunities"])


@router.get("")
def list_opportunities(
    league: str | None = Query(default=None),
    market: str | None = Query(default=None),
    min_edge: float | None = Query(default=None),
    min_confidence: float | None = Query(default=None),
    date: str | None = Query(default=None),
    bookmaker: str | None = Query(default=None),
) -> dict:
    """Runs the Market Edge Engine (app.services.market_edge_engine) over
    currently-ingested matches and odds. Returns an empty result set --
    never fabricated edges -- because no odds/match data has been ingested
    yet (Phase 2) and the signal thresholds are still placeholders pending
    real backtest data (docs/MARKET_ENGINE.md #3, docs/ROADMAP.md Phase 9).
    """
    return {
        "opportunities": [],
        "reason": "No ingested odds/match data yet, and signal thresholds are unvalidated placeholders.",
        "filters_applied": {
            "league": league,
            "market": market,
            "min_edge": min_edge,
            "min_confidence": min_confidence,
            "date": date,
            "bookmaker": bookmaker,
        },
    }
