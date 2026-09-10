"""docs/API.md - Admin (brief Section 23). Not mounted with authentication
yet -- see docs/API.md 'Auth' section. Included in the app for local/dev
visibility only."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
def admin_status() -> dict:
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "data_sources": {
            "football_data_org": "not_connected",
            "sportmonks": "not_connected",
            "the_odds_api": "not_connected",
            "betfair": "not_connected",
        },
        "model_version": "unversioned (no model trained on real data yet)",
        "last_backtest_run": None,
        "last_ingestion_run": None,
    }


@router.get("/backtests")
def list_backtests() -> dict:
    return {"runs": [], "reason": "No backtest has been run against real ingested data yet."}


@router.get("/experiments")
def list_experiments() -> dict:
    return {"experiments": [], "reason": "See docs/EXPERIMENTS.md -- log is currently empty."}
