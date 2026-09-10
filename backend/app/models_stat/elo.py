"""Elo rating system with home advantage and goal-difference-scaled K (docs/MODEL.md #2)."""
from __future__ import annotations

from dataclasses import dataclass


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that A beats/outperforms B, standard logistic Elo formula."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def goal_diff_multiplier(goal_difference: int) -> float:
    """K-factor multiplier scaled by margin of victory (World Football Elo method)."""
    gd = abs(goal_difference)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11 + gd) / 8.0


@dataclass(frozen=True)
class EloUpdateResult:
    new_home_rating: float
    new_away_rating: float


def update_ratings(
    home_rating: float,
    away_rating: float,
    home_goals: int,
    away_goals: int,
    k: float = 20.0,
    home_advantage: float = 100.0,
) -> EloUpdateResult:
    """One match update. home_advantage is added to home_rating only for the
    expected-score calculation, not persisted into the stored rating."""
    if home_goals > away_goals:
        actual_home = 1.0
    elif home_goals < away_goals:
        actual_home = 0.0
    else:
        actual_home = 0.5

    expected_home = expected_score(home_rating + home_advantage, away_rating)
    multiplier = goal_diff_multiplier(home_goals - away_goals)
    delta = k * multiplier * (actual_home - expected_home)

    return EloUpdateResult(
        new_home_rating=home_rating + delta,
        new_away_rating=away_rating - delta,
    )
