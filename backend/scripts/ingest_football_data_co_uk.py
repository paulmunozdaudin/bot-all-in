"""Runnable ingestion job: pulls real historical results + closing odds from
Football-Data.co.uk (free, no key) and upserts them into Postgres via the
schema in db/migrations/001_init.sql (docs/DATA.md, docs/ROADMAP.md Phase 2).

This has to run somewhere with real internet egress -- this sandboxed dev
session's network policy blocks arbitrary outbound domains (confirmed: even
WebFetch gets EGRESS_BLOCKED for football-data.co.uk), so this script is
written to be run from a normal environment (a laptop, CI, or a Render job)
rather than from here. See docs/DEPLOYMENT.md "Real data ingestion" for the
exact steps to run it against a hosted Postgres.

Usage:
    python -m scripts.ingest_football_data_co_uk --league E0 --seasons 2223 2324 2425 2526

League codes and season codes follow football-data.co.uk's own URL scheme,
e.g. E0 = Premier League, SP1 = La Liga, D1 = Bundesliga, I1 = Serie A,
F1 = Ligue 1; season '2425' = 2024/25.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Competition, Match, MatchStats, MarketOddsSnapshot, Season, Team
from app.db.session import SessionLocal
from app.services.ingestion.football_data_co_uk_adapter import FootballDataCoUkAdapter

LEAGUE_NAMES = {
    "E0": "Premier League",
    "SP1": "La Liga",
    "D1": "Bundesliga",
    "I1": "Serie A",
    "F1": "Ligue 1",
}


def get_or_create_competition(db: Session, league_code: str) -> Competition:
    name = LEAGUE_NAMES.get(league_code, league_code)
    existing = db.scalar(
        select(Competition).where(
            Competition.source == "football_data_co_uk", Competition.external_ref == league_code
        )
    )
    if existing:
        return existing
    competition = Competition(name=name, external_ref=league_code, source="football_data_co_uk")
    db.add(competition)
    db.flush()
    return competition


def get_or_create_season(db: Session, competition: Competition, label: str) -> Season:
    existing = db.scalar(
        select(Season).where(Season.competition_id == competition.id, Season.label == label)
    )
    if existing:
        return existing
    season = Season(competition_id=competition.id, label=label)
    db.add(season)
    db.flush()
    return season


def get_or_create_team(db: Session, name: str) -> Team:
    existing = db.scalar(
        select(Team).where(Team.source == "football_data_co_uk", Team.external_ref == name)
    )
    if existing:
        return existing
    team = Team(name=name, external_ref=name, source="football_data_co_uk")
    db.add(team)
    db.flush()
    return team


def ingest_match_row(db: Session, competition: Competition, row: dict) -> None:
    season = get_or_create_season(db, competition, row["season_label"])
    home_team = get_or_create_team(db, row["home_team"])
    away_team = get_or_create_team(db, row["away_team"])

    external_ref = (
        f"{row['league_code']}-{row['season_label'].replace('/', '-')}-"
        f"{row['kickoff_at'].date()}-{row['home_team']}-vs-{row['away_team']}"
    )

    match = db.scalar(
        select(Match).where(Match.source == "football_data_co_uk", Match.external_ref == external_ref)
    )
    if match is None:
        match = Match(
            competition_id=competition.id,
            season_id=season.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            kickoff_at=row["kickoff_at"],
            status="finished",
            external_ref=external_ref,
            source="football_data_co_uk",
        )
        db.add(match)
        db.flush()
    else:
        return  # already ingested -- idempotent re-run, nothing else to do

    db.add(
        MatchStats(
            match_id=match.id,
            home_goals=row["home_goals"],
            away_goals=row["away_goals"],
            home_shots=row["home_shots"],
            away_shots=row["away_shots"],
            home_shots_on_target=row["home_shots_on_target"],
            away_shots_on_target=row["away_shots_on_target"],
            home_corners=row["home_corners"],
            away_corners=row["away_corners"],
            home_cards=row["home_cards"],
            away_cards=row["away_cards"],
            is_final=True,
            source="football_data_co_uk",
            observed_at=row["kickoff_at"],
            ingested_at=row["fetched_at"],
        )
    )

    # Closing-line odds, one snapshot per bookmaker per selection (docs/DATA.md #2).
    # observed_at = kickoff_at: this source gives no finer timestamp -- see
    # the adapter module docstring for why that is stated explicitly here
    # rather than implied to be more precise than it is.
    for bookmaker, prices in row["odds"].items():
        for selection, decimal_odds in prices.items():
            db.add(
                MarketOddsSnapshot(
                    match_id=match.id,
                    bookmaker=bookmaker,
                    market="1x2",
                    selection=selection,
                    decimal_odds=decimal_odds,
                    observed_at=row["kickoff_at"],
                    source="football_data_co_uk",
                    ingested_at=row["fetched_at"],
                )
            )


def run(league_code: str, seasons: list[str]) -> None:
    adapter = FootballDataCoUkAdapter()
    total_rows = 0

    with SessionLocal() as db:
        competition = get_or_create_competition(db, league_code)
        db.commit()

        for season in seasons:
            print(f"Fetching {league_code} season {season} from football-data.co.uk...")
            raw = adapter.fetch_raw(league_code, season=season)
            rows = adapter.normalize(raw, fetched_at=datetime.now(timezone.utc))
            print(f"  {len(rows)} matches parsed")

            for row in rows:
                ingest_match_row(db, competition, row)
            db.commit()
            total_rows += len(rows)

    print(f"Done. {total_rows} matches processed across {len(seasons)} season(s).")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--league", default="E0", help="football-data.co.uk league code (default: E0)")
    parser.add_argument(
        "--seasons",
        nargs="+",
        default=["2223", "2324", "2425", "2526"],
        help="football-data.co.uk season codes, e.g. 2425 for 2024/25",
    )
    args = parser.parse_args()

    try:
        run(args.league, args.seasons)
    except Exception as exc:  # pragma: no cover -- operational script, not unit tested
        print(f"Ingestion failed: {exc}", file=sys.stderr)
        sys.exit(1)
