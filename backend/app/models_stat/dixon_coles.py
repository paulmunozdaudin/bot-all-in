"""Dixon-Coles low-score correlation adjustment (Dixon & Coles, 1997) -- docs/MODEL.md #2."""
from __future__ import annotations

import numpy as np

from app.models_stat.poisson import score_matrix as independent_poisson_matrix


def tau(x: int, y: int, lambda_home: float, lambda_away: float, rho: float) -> float:
    """The Dixon-Coles correction factor, nonzero only for low scorelines."""
    if x == 0 and y == 0:
        return 1.0 - (lambda_home * lambda_away * rho)
    if x == 0 and y == 1:
        return 1.0 + (lambda_home * rho)
    if x == 1 and y == 0:
        return 1.0 + (lambda_away * rho)
    if x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def score_matrix(
    lambda_home: float, lambda_away: float, rho: float = 0.0, max_goals: int = 10
) -> np.ndarray:
    """Dixon-Coles-adjusted joint scoreline distribution, renormalized to sum to 1.

    rho=0 reduces exactly to the independent Poisson matrix (tau=1 everywhere).
    """
    base = independent_poisson_matrix(lambda_home, lambda_away, max_goals=max_goals)
    adjusted = base.copy()
    for x in range(min(2, max_goals + 1)):
        for y in range(min(2, max_goals + 1)):
            adjusted[x, y] *= tau(x, y, lambda_home, lambda_away, rho)
    adjusted = np.clip(adjusted, 0.0, None)
    total = adjusted.sum()
    if total <= 0:
        raise ValueError("rho produced a degenerate (non-positive) distribution")
    return adjusted / total
