"""docs/API.md - Matches. No data ingestion (Phase 2) has run yet, so these
endpoints honestly report that rather than fabricating fixtures or odds --
see docs/ROADMAP.md for what is and isn't implemented."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.common import NoDataResponse

router = APIRouter(prefix="/matches", tags=["matches"])


@router.get("/today", response_model=list)
def matches_today() -> list:
    """Section 19 (Home page). Returns an empty list -- not fabricated
    fixtures -- until Phase 2 (data ingestion) populates the `match` table."""
    return []


@router.get("/{match_id}", response_model=NoDataResponse)
def match_detail(match_id: int) -> NoDataResponse:
    """Section 20 (Match page). No match data has been ingested yet."""
    return NoDataResponse(
        reason=(
            f"No ingested data for match_id={match_id}. Data ingestion (Phase 2) "
            "has not been connected to a live provider in this environment -- "
            "see docs/research/DATA_PROVIDERS.md and docs/ROADMAP.md."
        )
    )
