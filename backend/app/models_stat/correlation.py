"""Correlation-aware joint probability for the Combination Engine (docs/COMBINATIONS.md #3-4).

The core rule this module exists to enforce: never compute P(A and B) as
P(A) * P(B) when A and B come from the same match. Same-match markets share
one underlying scoreline distribution, so their true joint probability is
read directly off that distribution instead of assumed independent.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

ScorePredicate = Callable[[int, int], bool]


@dataclass(frozen=True)
class Selection:
    match_id: int
    market: str
    label: str
    probability: float  # marginal probability, as already computed by the model pipeline
    predicate: ScorePredicate | None = None  # how this selection maps onto a score matrix


def joint_probability_same_match(matrix: np.ndarray, predicates: list[ScorePredicate]) -> float:
    """Exact joint probability of several same-match selections, from the score matrix."""
    total = 0.0
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            if all(predicate(i, j) for predicate in predicates):
                total += matrix[i, j]
    return float(total)


def combined_probability(selections: list[Selection], same_match_matrix: np.ndarray | None = None) -> tuple[float, str]:
    """Combined probability for a set of selections plus a note on the method used.

    - If every selection belongs to the same match and carries a predicate,
      and a score matrix is supplied, the exact joint probability is used.
    - Otherwise, falls back to the independence product -- and says so
      explicitly, per docs/COMBINATIONS.md #3 ("that fallback is logged as
      such in the combination's output, not hidden").
    """
    if not selections:
        raise ValueError("selections must be non-empty")

    same_match = len({s.match_id for s in selections}) == 1
    all_have_predicates = all(s.predicate is not None for s in selections)

    if same_match and all_have_predicates and same_match_matrix is not None:
        predicates = [s.predicate for s in selections]  # type: ignore[list-item]
        prob = joint_probability_same_match(same_match_matrix, predicates)
        return prob, "exact_joint_same_match"

    product = 1.0
    for s in selections:
        product *= s.probability
    method = "independence_assumed_same_match" if same_match else "independence_assumed_cross_match"
    return product, method


def flag_derived_market_conflict(market_a: str, market_b: str) -> bool:
    """True if two markets are (near-)deterministic functions of each other and
    should never both appear in one combination (docs/COMBINATIONS.md #3).
    """
    conflict_groups = [
        {"1x2_home", "double_chance_1x", "double_chance_12"},
        {"1x2_away", "double_chance_x2", "double_chance_12"},
        {"1x2_draw", "double_chance_1x", "double_chance_x2"},
        {"over_2.5", "under_2.5"},
        {"btts_yes", "btts_no"},
    ]
    return any(market_a in group and market_b in group for group in conflict_groups)
