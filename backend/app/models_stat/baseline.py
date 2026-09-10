"""Frequency baseline (docs/MODEL.md #2) -- the bar every other model must clear."""
from __future__ import annotations

from collections import Counter


def frequency_baseline(historical_outcomes: list[str]) -> dict[str, float]:
    """Base-rate probabilities from historical 'H'/'D'/'A' outcomes.

    Any model that cannot beat this out-of-sample (docs/BACKTESTING.md) does not ship.
    """
    if not historical_outcomes:
        raise ValueError("historical_outcomes must be non-empty")
    counts = Counter(historical_outcomes)
    n = len(historical_outcomes)
    return {outcome: count / n for outcome, count in counts.items()}
