import pytest

from app.models_stat.dixon_coles import score_matrix as dc_matrix
from app.models_stat.monte_carlo import simulate_from_matrix, simulate_joint_selection_probability, summarize_outcomes
from app.models_stat.poisson import outcome_probabilities, score_matrix


def test_simulation_converges_to_analytical_outcome_probabilities():
    matrix = score_matrix(1.6, 1.1, max_goals=12)
    analytical = outcome_probabilities(matrix)

    simulated = simulate_from_matrix(matrix, n_simulations=50_000, seed=42)
    empirical = summarize_outcomes(simulated)

    for outcome in ("home", "draw", "away"):
        assert empirical[outcome] == pytest.approx(analytical[outcome], abs=0.01)


def test_simulate_from_matrix_rejects_invalid_distribution():
    import numpy as np

    with pytest.raises(ValueError):
        simulate_from_matrix(np.array([[0.3, 0.3], [0.3, 0.3]]))  # sums to 1.2


def test_joint_selection_probability_matches_analytical_dixon_coles():
    matrix = dc_matrix(1.5, 1.2, rho=-0.1, max_goals=12)
    # P(Home Win & Over 1.5 total goals)
    predicates = [lambda h, a: h > a, lambda h, a: h + a > 1.5]

    from app.models_stat.correlation import joint_probability_same_match

    analytical = joint_probability_same_match(matrix, predicates)
    empirical = simulate_joint_selection_probability(matrix, predicates, n_simulations=50_000, seed=1)

    assert empirical == pytest.approx(analytical, abs=0.01)
