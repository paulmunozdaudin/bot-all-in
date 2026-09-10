"""Tests the CSV parsing logic against a small hand-built sample matching
football-data.co.uk's real column layout -- no network access needed."""
from datetime import datetime, timezone

from app.services.ingestion.football_data_co_uk_adapter import FootballDataCoUkAdapter

SAMPLE_CSV = """Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,HS,AS,HST,AST,HC,AC,HY,AY,HR,AR,B365H,B365D,B365A,AvgH,AvgD,AvgA
E0,16/08/2024,20:00,Arsenal,Wolves,2,0,H,18,6,7,2,8,3,1,2,0,0,1.30,5.50,9.00,1.28,5.40,9.20
E0,17/08/2024,15:00,Chelsea,Man City,1,1,D,10,14,4,6,4,7,2,3,0,0,3.80,3.60,1.90,3.70,3.55,1.95
E0,17/08/2024,15:00,,Everton,,,,,,,,,,,,,,,,,,,
"""


def _adapter_payload() -> dict:
    return {"league_code": "E0", "season": "2425", "csv_text": SAMPLE_CSV}


def test_normalize_parses_expected_number_of_valid_matches():
    adapter = FootballDataCoUkAdapter()
    rows = adapter.normalize(_adapter_payload(), fetched_at=datetime.now(timezone.utc))
    # the third row has missing team/score data and must be dropped, not
    # ingested as a garbage row (docs/DATA.md #6, data quality)
    assert len(rows) == 2


def test_normalize_maps_core_fields_correctly():
    adapter = FootballDataCoUkAdapter()
    rows = adapter.normalize(_adapter_payload(), fetched_at=datetime.now(timezone.utc))
    arsenal_row = next(r for r in rows if r["home_team"] == "Arsenal")

    assert arsenal_row["away_team"] == "Wolves"
    assert arsenal_row["home_goals"] == 2
    assert arsenal_row["away_goals"] == 0
    assert arsenal_row["home_shots"] == 18
    assert arsenal_row["home_shots_on_target"] == 7
    assert arsenal_row["home_cards"] == 1  # 1 yellow + 0 red
    assert arsenal_row["season_label"] == "2024/2025"
    assert arsenal_row["kickoff_at"] == datetime(2024, 8, 16, 20, 0, tzinfo=timezone.utc)


def test_normalize_extracts_both_bookmaker_odds_sets():
    adapter = FootballDataCoUkAdapter()
    rows = adapter.normalize(_adapter_payload(), fetched_at=datetime.now(timezone.utc))
    arsenal_row = next(r for r in rows if r["home_team"] == "Arsenal")

    assert arsenal_row["odds"]["bet365"] == {"home": 1.30, "draw": 5.50, "away": 9.00}
    assert arsenal_row["odds"]["football_data_co_uk_average"] == {
        "home": 1.28,
        "draw": 5.40,
        "away": 9.20,
    }


def test_normalize_handles_missing_odds_columns_gracefully():
    csv_without_odds = (
        "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR\n"
        "E0,16/08/2024,20:00,Arsenal,Wolves,2,0,H\n"
    )
    adapter = FootballDataCoUkAdapter()
    rows = adapter.normalize(
        {"league_code": "E0", "season": "2425", "csv_text": csv_without_odds},
        fetched_at=datetime.now(timezone.utc),
    )
    assert rows[0]["odds"] == {}


def test_normalize_rejects_no_matches_when_all_rows_incomplete():
    csv_all_bad = "Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR\nE0,16/08/2024,20:00,,,,,\n"
    adapter = FootballDataCoUkAdapter()
    rows = adapter.normalize(
        {"league_code": "E0", "season": "2425", "csv_text": csv_all_bad},
        fetched_at=datetime.now(timezone.utc),
    )
    assert rows == []
