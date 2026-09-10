import numpy as np
import pytest

from app.models_stat.dixon_coles import score_matrix, tau
from app.models_stat.poisson import score_matrix as independent_poisson_matrix


def test_rho_zero_reduces_to_independent_poisson():
    dc = score_matrix(1.4, 1.1, rho=0.0, max_goals=10)
    poisson = independent_poisson_matrix(1.4, 1.1, max_goals=10)
    assert np.allclose(dc, poisson, atol=1e-9)


def test_tau_matches_dixon_coles_1997_formula():
    lam, mu, rho = 1.3, 1.0, -0.1
    assert tau(0, 0, lam, mu, rho) == pytest.approx(1 - lam * mu * rho)
    assert tau(0, 1, lam, mu, rho) == pytest.approx(1 + lam * rho)
    assert tau(1, 0, lam, mu, rho) == pytest.approx(1 + mu * rho)
    assert tau(1, 1, lam, mu, rho) == pytest.approx(1 - rho)
    assert tau(2, 2, lam, mu, rho) == pytest.approx(1.0)


def test_score_matrix_sums_to_one_after_renormalization():
    matrix = score_matrix(1.4, 1.1, rho=-0.13, max_goals=10)
    assert matrix.sum() == pytest.approx(1.0, abs=1e-6)


def test_negative_rho_shifts_mass_toward_low_scoring_draws():
    # Dixon-Coles' documented effect: negative rho increases P(0-0) and P(1-1)
    # relative to independent Poisson, for typical football-scale lambdas.
    lam, mu = 1.3, 1.1
    independent = independent_poisson_matrix(lam, mu, max_goals=10)
    adjusted = score_matrix(lam, mu, rho=-0.13, max_goals=10)
    assert adjusted[0, 0] > independent[0, 0]
    assert adjusted[1, 1] > independent[1, 1]
