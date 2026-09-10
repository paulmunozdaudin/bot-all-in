"""Data quality checks (docs/DATA.md #6, brief Section 24): missing data,
duplicate facts, impossible values, timestamp ordering.
"""
from __future__ import annotations

from datetime import datetime

from app.services.feature_builder import Fact


class DataQualityError(ValueError):
    pass


def check_probability_valid(value: float, field_name: str = "probability") -> None:
    if not (0.0 <= value <= 1.0):
        raise DataQualityError(f"{field_name} must be in [0, 1], got {value}")


def check_probabilities_sum_to_one(values: list[float], tolerance: float = 1e-6) -> None:
    total = sum(values)
    if abs(total - 1.0) > tolerance:
        raise DataQualityError(f"probabilities must sum to 1.0, got {total}")


def check_decimal_odds_valid(decimal_odds: float) -> None:
    if decimal_odds < 1.0:
        raise DataQualityError(f"decimal odds must be >= 1.0, got {decimal_odds}")


def check_goals_valid(goals: int, field_name: str = "goals") -> None:
    if goals < 0:
        raise DataQualityError(f"{field_name} cannot be negative, got {goals}")


def check_minutes_played_valid(minutes: int) -> None:
    if not (0 <= minutes <= 120):
        raise DataQualityError(f"minutes_played must be in [0, 120], got {minutes}")


def check_no_duplicate_facts(facts: list[Fact]) -> None:
    """A duplicate (source, match_id, fact_type, observed_at) is either a
    double-ingest bug or a provider sending the same fact twice -- both must
    be caught before it reaches feature building."""
    seen: set[tuple] = set()
    for fact in facts:
        key = (fact.source, fact.match_id, fact.fact_type, fact.observed_at)
        if key in seen:
            raise DataQualityError(f"duplicate fact detected: {key}")
        seen.add(key)


def check_kickoff_after_announcement(announced_at: datetime, kickoff_at: datetime) -> None:
    if kickoff_at <= announced_at:
        raise DataQualityError(
            f"kickoff_at ({kickoff_at}) must be after announced_at ({announced_at})"
        )
