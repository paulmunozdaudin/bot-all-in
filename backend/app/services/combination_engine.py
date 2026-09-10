"""Combination Engine (docs/COMBINATIONS.md).

Searches a pool of individually-scored selections for combinations that
clear explicit statistical bars, using the correlation-aware joint
probability in app.models_stat.correlation instead of naive independence.
Returns an explicit "no result" outcome when nothing clears the bar
(docs/COMBINATIONS.md #8) -- this is never relaxed to force a result.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from app.models_stat.correlation import Selection, combined_probability, flag_derived_market_conflict


class NoStrongCombinationFound(Exception):
    """Raised (and expected to be caught by the API layer) when no combination
    in the search space clears the configured bar."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class CombinationResult:
    selections: tuple[Selection, ...]
    combined_probability: float
    method: str
    expected_value: float
    score: float


def _has_market_conflict(selections: tuple[Selection, ...]) -> bool:
    for a, b in combinations(selections, 2):
        if a.match_id == b.match_id and flag_derived_market_conflict(a.market, b.market):
            return True
    return False


def _concentration_risk(selections: tuple[Selection, ...]) -> bool:
    """Flags combinations leaning repeatedly on the same match (docs/COMBINATIONS.md #3)."""
    match_ids = [s.match_id for s in selections]
    return len(set(match_ids)) < len(match_ids) and _has_market_conflict(selections)


def score_combination(
    combined_prob: float, expected_value: float, min_ev_weight: float = 0.5
) -> float:
    """Documented, versioned scoring function (docs/COMBINATIONS.md #7).

    Placeholder linear blend of EV and combined probability -- weights are to
    be fit against backtested combination outcomes (docs/BACKTESTING.md)
    before production use, exactly as docs/COMBINATIONS.md #7 requires.
    """
    return min_ev_weight * expected_value + (1 - min_ev_weight) * combined_prob


def search_combinations(
    selection_pool: list[Selection],
    max_selections: int = 4,
    min_combined_probability: float = 0.0,
    min_expected_value: float = 0.0,
    decimal_odds_by_selection: dict[str, float] | None = None,
    same_match_matrices: dict[int, np.ndarray] | None = None,
) -> list[CombinationResult]:
    """Brute-force search over selection subsets (size 2..max_selections),
    filtering by EV/probability/correlation-conflict gates, ranked by score.

    Returns an empty list (the API layer turns this into the explicit
    NO_STRONG_COMBINATION_FOUND response, docs/COMBINATIONS.md #8) rather
    than relaxing filters to force a result.
    """
    if max_selections < 2:
        raise ValueError("a combination needs at least 2 selections")
    decimal_odds_by_selection = decimal_odds_by_selection or {}
    same_match_matrices = same_match_matrices or {}

    results: list[CombinationResult] = []
    for size in range(2, min(max_selections, len(selection_pool)) + 1):
        for combo in combinations(selection_pool, size):
            if _has_market_conflict(combo):
                continue
            if _concentration_risk(combo):
                continue

            match_ids = {s.match_id for s in combo}
            matrix = same_match_matrices.get(next(iter(match_ids))) if len(match_ids) == 1 else None
            prob, method = combined_probability(list(combo), same_match_matrix=matrix)

            if prob < min_combined_probability:
                continue

            combined_decimal_odds = 1.0
            has_all_odds = True
            for s in combo:
                key = f"{s.match_id}:{s.market}:{s.label}"
                if key not in decimal_odds_by_selection:
                    has_all_odds = False
                    break
                combined_decimal_odds *= decimal_odds_by_selection[key]
            if not has_all_odds:
                continue

            ev = prob * combined_decimal_odds - 1.0
            if ev < min_expected_value:
                continue

            results.append(
                CombinationResult(
                    selections=combo,
                    combined_probability=prob,
                    method=method,
                    expected_value=ev,
                    score=score_combination(prob, ev),
                )
            )

    return sorted(results, key=lambda r: r.score, reverse=True)
