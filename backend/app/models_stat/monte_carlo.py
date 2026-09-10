"""Monte Carlo simulation from a fitted joint score distribution (docs/MODEL.md #5,
docs/COMBINATIONS.md #5).

Sampling directly from the (Dixon-Coles or Poisson) score matrix -- rather
than drawing home/away goals independently -- preserves whatever
correlation the fitted matrix already encodes, and gives every derived
market for one simulated match the same underlying scoreline draw. That is
exactly the mechanism the Combination Engine relies on for same-match joint
probabilities.
"""
from __future__ import annotations

import numpy as np


def simulate_from_matrix(
    matrix: np.ndarray, n_simulations: int = 10_000, seed: int | None = None
) -> np.ndarray:
    """Draw n_simulations (home_goals, away_goals) pairs from a joint score matrix.

    Returns an (n_simulations, 2) integer array.
    """
    flat = matrix.flatten()
    total = flat.sum()
    if not np.isclose(total, 1.0, atol=1e-6):
        raise ValueError(f"matrix must be a valid probability distribution (sums to {total})")
    # Renormalize to exactly 1.0 for np.random.choice, which enforces a much
    # tighter tolerance than the sanity check above (truncating a Poisson's
    # infinite support to max_goals leaves a negligible but nonzero gap).
    flat = flat / total

    rng = np.random.default_rng(seed)
    n_away_values = matrix.shape[1]
    flat_indices = rng.choice(len(flat), size=n_simulations, p=flat)
    home_goals = flat_indices // n_away_values
    away_goals = flat_indices % n_away_values
    return np.stack([home_goals, away_goals], axis=1)


def summarize_outcomes(simulated_scores: np.ndarray) -> dict[str, float]:
    """1X2 frequencies from simulated (home, away) goal pairs."""
    n = len(simulated_scores)
    home_goals, away_goals = simulated_scores[:, 0], simulated_scores[:, 1]
    return {
        "home": float(np.mean(home_goals > away_goals)),
        "draw": float(np.mean(home_goals == away_goals)),
        "away": float(np.mean(home_goals < away_goals)),
    }


def simulate_joint_selection_probability(
    matrix: np.ndarray,
    predicates: list,
    n_simulations: int = 10_000,
    seed: int | None = None,
) -> float:
    """Monte Carlo estimate of P(all predicates true) for same-match selections,
    e.g. predicates=[lambda h, a: h > a, lambda h, a: h + a > 2.5] for
    'Home Win & Over 2.5'. Used as a cross-check against the exact analytical
    joint probability in models_stat/correlation.py.
    """
    simulated = simulate_from_matrix(matrix, n_simulations=n_simulations, seed=seed)
    mask = np.ones(len(simulated), dtype=bool)
    for predicate in predicates:
        mask &= np.array([predicate(h, a) for h, a in simulated])
    return float(np.mean(mask))
