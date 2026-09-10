"""Independent Poisson goals model (docs/MODEL.md #2)."""
from __future__ import annotations

import numpy as np
from scipy.stats import poisson


def score_matrix(lambda_home: float, lambda_away: float, max_goals: int = 10) -> np.ndarray:
    """P(home_goals=i, away_goals=j) for i,j in [0, max_goals], independent Poisson."""
    if lambda_home <= 0 or lambda_away <= 0:
        raise ValueError("expected goals must be positive")
    home_pmf = poisson.pmf(np.arange(max_goals + 1), lambda_home)
    away_pmf = poisson.pmf(np.arange(max_goals + 1), lambda_away)
    return np.outer(home_pmf, away_pmf)


def outcome_probabilities(matrix: np.ndarray) -> dict[str, float]:
    """1X2 probabilities from a score matrix (rows=home goals, cols=away goals)."""
    home_win = float(np.sum(np.tril(matrix, -1)))
    draw = float(np.sum(np.diag(matrix)))
    away_win = float(np.sum(np.triu(matrix, 1)))
    return {"home": home_win, "draw": draw, "away": away_win}


def over_under_probability(matrix: np.ndarray, line: float) -> dict[str, float]:
    """P(total goals > line) / P(total goals < line), for a half-integer line (e.g. 2.5)."""
    n = matrix.shape[0]
    total_goals = np.add.outer(np.arange(n), np.arange(n))
    over = float(np.sum(matrix[total_goals > line]))
    under = float(np.sum(matrix[total_goals < line]))
    return {"over": over, "under": under}


def btts_probability(matrix: np.ndarray) -> dict[str, float]:
    """P(both teams score) / P(at least one team fails to score)."""
    yes = float(np.sum(matrix[1:, 1:]))
    return {"yes": yes, "no": 1.0 - yes}


def correct_score_probabilities(matrix: np.ndarray, top_n: int | None = None) -> dict[str, float]:
    """{'i-j': probability} for every scoreline in the matrix, optionally top-N by probability."""
    scores = {
        f"{i}-{j}": float(matrix[i, j])
        for i in range(matrix.shape[0])
        for j in range(matrix.shape[1])
    }
    if top_n is None:
        return scores
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    return dict(ranked)


def team_goal_probability(matrix: np.ndarray, side: str, line: float) -> dict[str, float]:
    """P(one team's goals > / < line). side is 'home' or 'away'."""
    axis = 1 if side == "home" else 0  # sum out the other team's axis
    marginal = matrix.sum(axis=axis)
    n = len(marginal)
    over = float(np.sum(marginal[np.arange(n) > line]))
    under = float(np.sum(marginal[np.arange(n) < line]))
    return {"over": over, "under": under}
