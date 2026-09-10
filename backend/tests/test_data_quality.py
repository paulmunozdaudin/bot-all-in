from datetime import datetime

import pytest

from app.services.data_quality import (
    DataQualityError,
    check_decimal_odds_valid,
    check_goals_valid,
    check_kickoff_after_announcement,
    check_minutes_played_valid,
    check_no_duplicate_facts,
    check_probabilities_sum_to_one,
    check_probability_valid,
)
from app.services.feature_builder import Fact


def test_probability_out_of_range_rejected():
    with pytest.raises(DataQualityError):
        check_probability_valid(1.2)
    with pytest.raises(DataQualityError):
        check_probability_valid(-0.1)
    check_probability_valid(0.5)  # does not raise


def test_probabilities_must_sum_to_one():
    with pytest.raises(DataQualityError):
        check_probabilities_sum_to_one([0.5, 0.3, 0.1])
    check_probabilities_sum_to_one([0.5, 0.3, 0.2])  # does not raise


def test_decimal_odds_below_one_rejected():
    with pytest.raises(DataQualityError):
        check_decimal_odds_valid(0.9)
    check_decimal_odds_valid(1.01)


def test_negative_goals_rejected():
    with pytest.raises(DataQualityError):
        check_goals_valid(-1)
    check_goals_valid(0)


def test_minutes_played_out_of_range_rejected():
    with pytest.raises(DataQualityError):
        check_minutes_played_valid(-5)
    with pytest.raises(DataQualityError):
        check_minutes_played_valid(200)
    check_minutes_played_valid(90)


def test_duplicate_fact_detected():
    facts = [
        Fact(1, "home_elo", 1500.0, datetime(2026, 1, 1), "internal_elo_model"),
        Fact(1, "home_elo", 1500.0, datetime(2026, 1, 1), "internal_elo_model"),
    ]
    with pytest.raises(DataQualityError):
        check_no_duplicate_facts(facts)


def test_same_fact_type_different_timestamp_is_not_a_duplicate():
    facts = [
        Fact(1, "home_elo", 1500.0, datetime(2026, 1, 1), "internal_elo_model"),
        Fact(1, "home_elo", 1510.0, datetime(2026, 1, 8), "internal_elo_model"),
    ]
    check_no_duplicate_facts(facts)  # does not raise


def test_kickoff_must_be_after_announcement():
    announced = datetime(2026, 1, 1, 12, 0)
    with pytest.raises(DataQualityError):
        check_kickoff_after_announcement(announced, datetime(2026, 1, 1, 11, 0))
    check_kickoff_after_announcement(announced, datetime(2026, 1, 5, 15, 0))  # does not raise
