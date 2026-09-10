"""Real adapter for Football-Data.co.uk (docs/research/DATA_PROVIDERS.md #2,
#5): free, no signup, no API key -- historical results + closing odds as
plain CSV per league/season, e.g.
https://www.football-data.co.uk/mmz4281/2425/E0.csv (Premier League, 2024/25).

Chosen as the first real source specifically because it needs no account
and no key, so it's the fastest path to a real historical dataset for
backtesting (docs/BACKTESTING.md) -- see docs/ROADMAP.md Phase 2.

Known, documented limitation (be explicit rather than pretend precision we
don't have): this source gives one odds figure per bookmaker per match with
no timestamp finer than the match itself -- it is effectively a *closing*
line, not a time series. We stamp it with observed_at = kickoff_at, which
is honest about what we actually know (a pre-kickoff price existed) and
deliberately NOT used to claim pre-match movement or CLV analysis -- that
needs a real timestamped feed (The Odds API / Betfair, per the research
doc) and is out of scope for this adapter.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd

from app.services.ingestion.base_adapter import SourceAdapter

BASE_URL = "https://www.football-data.co.uk/mmz4281"

# Odds columns to try, in preference order: Bet365, then the cross-bookmaker
# average column football-data.co.uk publishes on newer seasons.
ODDS_COLUMN_SETS: list[tuple[str, tuple[str, str, str]]] = [
    ("bet365", ("B365H", "B365D", "B365A")),
    ("football_data_co_uk_average", ("AvgH", "AvgD", "AvgA")),
]


class FootballDataCoUkAdapter(SourceAdapter):
    source_name = "football_data_co_uk"

    def fetch_raw(self, endpoint: str, **params: Any) -> dict:
        """endpoint is the league code (e.g. 'E0' for the Premier League,
        'SP1' for La Liga); params must include `season` as a 4-digit code
        (e.g. '2425' for 2024/25), matching football-data.co.uk's own URL scheme.
        """
        season = params["season"]
        url = f"{BASE_URL}/{season}/{endpoint}.csv"
        response = httpx.get(url, timeout=30.0, follow_redirects=True)
        response.raise_for_status()
        return {"league_code": endpoint, "season": season, "csv_text": response.text, "url": url}

    def normalize(self, raw_payload: dict, fetched_at: datetime) -> list[dict]:
        df = pd.read_csv(io.StringIO(raw_payload["csv_text"]))
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTHG", "FTAG"])

        rows = []
        for _, r in df.iterrows():
            kickoff_at = _parse_kickoff(r.get("Date"), r.get("Time"))
            if kickoff_at is None:
                continue

            odds = _extract_odds(r)

            rows.append(
                {
                    "source": self.source_name,
                    "league_code": raw_payload["league_code"],
                    "season_label": _season_label(raw_payload["season"]),
                    "home_team": str(r["HomeTeam"]).strip(),
                    "away_team": str(r["AwayTeam"]).strip(),
                    "kickoff_at": kickoff_at,
                    "home_goals": int(r["FTHG"]),
                    "away_goals": int(r["FTAG"]),
                    "home_shots": _safe_int(r.get("HS")),
                    "away_shots": _safe_int(r.get("AS")),
                    "home_shots_on_target": _safe_int(r.get("HST")),
                    "away_shots_on_target": _safe_int(r.get("AST")),
                    "home_corners": _safe_int(r.get("HC")),
                    "away_corners": _safe_int(r.get("AC")),
                    "home_cards": _safe_int(r.get("HY"), default=0) + _safe_int(r.get("HR"), default=0)
                    if pd.notna(r.get("HY")) or pd.notna(r.get("HR"))
                    else None,
                    "away_cards": _safe_int(r.get("AY"), default=0) + _safe_int(r.get("AR"), default=0)
                    if pd.notna(r.get("AY")) or pd.notna(r.get("AR"))
                    else None,
                    "odds": odds,  # {bookmaker: {"home": x, "draw": y, "away": z}} or {}
                    "fetched_at": fetched_at,
                }
            )
        return rows


def _season_label(season_code: str) -> str:
    start = f"20{season_code[:2]}"
    end = f"20{season_code[2:]}"
    return f"{start}/{end}"


def _parse_kickoff(date_val: Any, time_val: Any) -> datetime | None:
    if pd.isna(date_val):
        return None
    date_str = str(date_val).strip()
    time_str = str(time_val).strip() if time_val is not None and pd.notna(time_val) else "15:00"
    for date_fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", f"{date_fmt} %H:%M")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _safe_int(value: Any, default: int | None = None) -> int | None:
    if value is None or pd.isna(value):
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _extract_odds(row: pd.Series) -> dict[str, dict[str, float]]:
    odds: dict[str, dict[str, float]] = {}
    for bookmaker, (h_col, d_col, a_col) in ODDS_COLUMN_SETS:
        if h_col not in row or pd.isna(row.get(h_col)):
            continue
        try:
            home, draw, away = float(row[h_col]), float(row[d_col]), float(row[a_col])
        except (ValueError, TypeError):
            continue
        if home >= 1.0 and draw >= 1.0 and away >= 1.0:
            odds[bookmaker] = {"home": home, "draw": draw, "away": away}
    return odds
