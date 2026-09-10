"""docs/DATA.md #4 (CRITICAL): a feature vector built 'as of' a point in time
must be bit-for-bit identical whether or not later rows exist in the input.
This is the test the architecture doc promises exists.
"""
from datetime import datetime

from app.services.feature_builder import Fact, build_features_as_of, facts_as_of

MATCH_ID = 42
PREDICTION_TIME = datetime(2026, 3, 14, 12, 0)  # e.g. kickoff - 48h


def _past_facts() -> list[Fact]:
    return [
        Fact(MATCH_ID, "home_elo", 1532.0, datetime(2026, 3, 10, 9, 0), "internal_elo_model"),
        Fact(MATCH_ID, "away_elo", 1488.0, datetime(2026, 3, 10, 9, 0), "internal_elo_model"),
        Fact(MATCH_ID, "home_xg_avg_last5", 1.71, datetime(2026, 3, 12, 8, 0), "sportmonks"),
    ]


def _future_facts() -> list[Fact]:
    """Facts that only become known AFTER the simulated prediction time --
    e.g. the confirmed lineup announced ~60 minutes before kickoff, and the
    final result itself."""
    return [
        Fact(MATCH_ID, "lineup_confirmed", "yes", datetime(2026, 3, 16, 13, 0), "sportmonks"),
        Fact(MATCH_ID, "home_goals_final", 2.0, datetime(2026, 3, 16, 16, 50), "sportmonks"),
        # a later Elo update, computed only after this match's result exists
        Fact(MATCH_ID, "home_elo", 1541.0, datetime(2026, 3, 16, 17, 0), "internal_elo_model"),
    ]


def test_features_identical_with_or_without_future_rows_present():
    only_past = _past_facts()
    past_and_future = _past_facts() + _future_facts()

    features_from_past_only = build_features_as_of(only_past, MATCH_ID, PREDICTION_TIME)
    features_from_full_dataset = build_features_as_of(past_and_future, MATCH_ID, PREDICTION_TIME)

    assert features_from_past_only == features_from_full_dataset


def test_future_only_fact_types_never_appear_in_as_of_features():
    all_facts = _past_facts() + _future_facts()
    features = build_features_as_of(all_facts, MATCH_ID, PREDICTION_TIME)

    assert "lineup_confirmed" not in features
    assert "home_goals_final" not in features


def test_as_of_uses_the_latest_value_available_at_that_time_not_the_final_one():
    all_facts = _past_facts() + _future_facts()
    features = build_features_as_of(all_facts, MATCH_ID, PREDICTION_TIME)

    # the pre-match Elo (1532), not the post-match-updated Elo (1541)
    assert features["home_elo"] == 1532.0


def test_facts_as_of_excludes_a_fact_observed_exactly_after_the_cutoff():
    cutoff = datetime(2026, 3, 16, 12, 59, 59)
    all_facts = _past_facts() + _future_facts()
    visible = facts_as_of(all_facts, MATCH_ID, cutoff)

    assert all(f.observed_at <= cutoff for f in visible)
    assert not any(f.fact_type == "lineup_confirmed" for f in visible)


def test_facts_as_of_includes_a_fact_observed_exactly_at_the_cutoff():
    lineup_time = datetime(2026, 3, 16, 13, 0)
    all_facts = _past_facts() + _future_facts()
    visible = facts_as_of(all_facts, MATCH_ID, lineup_time)

    assert any(f.fact_type == "lineup_confirmed" for f in visible)
