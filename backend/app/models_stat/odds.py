"""Odds <-> probability conversion and EV math (docs/MARKET_ENGINE.md)."""
from __future__ import annotations

from dataclasses import dataclass


def decimal_to_implied_probability(decimal_odds: float) -> float:
    """Convert a decimal price to its raw (margin-included) implied probability."""
    if decimal_odds < 1.0:
        raise ValueError("decimal_odds must be >= 1.0")
    return 1.0 / decimal_odds


def overround(implied_probabilities: list[float]) -> float:
    """Bookmaker margin for a full market: sum(implied) - 1."""
    return sum(implied_probabilities) - 1.0


def normalize_probabilities(implied_probabilities: list[float]) -> list[float]:
    """Proportional (multiplicative) de-vigging so probabilities sum to 1."""
    total = sum(implied_probabilities)
    if total <= 0:
        raise ValueError("sum of implied probabilities must be positive")
    return [p / total for p in implied_probabilities]


def expected_value(model_probability: float, decimal_odds: float) -> float:
    """Theoretical EV of a unit stake: EV = p * decimal_odds - 1."""
    if not 0.0 <= model_probability <= 1.0:
        raise ValueError("model_probability must be in [0, 1]")
    return model_probability * decimal_odds - 1.0


@dataclass(frozen=True)
class EdgeComparison:
    model_probability: float
    market_probability: float  # normalized (margin removed)
    diff_pp: float             # percentage points, model - market
    ev: float                  # against the raw decimal odds actually available


def compare_to_market(
    model_probability: float, decimal_odds: float, market_implied_probabilities: list[float]
) -> EdgeComparison:
    """Full Section 8 pipeline for one selection: normalize the market, diff, EV."""
    normalized = normalize_probabilities(market_implied_probabilities)
    # assumes the caller passes market_implied_probabilities ordered so that
    # this selection's normalized probability is normalized[0]
    market_probability = normalized[0]
    diff_pp = (model_probability - market_probability) * 100.0
    ev = expected_value(model_probability, decimal_odds)
    return EdgeComparison(
        model_probability=model_probability,
        market_probability=market_probability,
        diff_pp=diff_pp,
        ev=ev,
    )
