"""docs/API.md - Track record (brief Section 15). Every number here must
come from the immutable `prediction`/`outcome` tables -- never computed
from anything other than logged, resolved predictions."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/track-record", tags=["track-record"])


@router.get("/summary")
def track_record_summary() -> dict:
    return {
        "total_predictions": 0,
        "resolved_predictions": 0,
        "correct_predictions": 0,
        "brier_score": None,
        "log_loss": None,
        "clv": None,
        "reason": (
            "No predictions have been logged yet -- this product does not show "
            "a track record until it has one. See docs/ROADMAP.md."
        ),
    }
