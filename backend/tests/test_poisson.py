import numpy as np
import pytest

from app.models_stat.poisson import (
    btts_probability,
    correct_score_probabilities,
    outcome_probabilities,
    over_under_probability,
    score_matrix,
    team_goal_probability,
)


def test_score_matrix_sums_to_one():
    matrix = score_matrix(1.5, 1.1, max_goals=15)
    assert matrix.sum() == pytest.approx(1.0, abs=1e-6)


def test_score_matrix_rejects_nonpositive_lambda():
    with pytest.raises(ValueError):
        score_matrix(0, 1.0)


def test_outcome_probabilities_sum_to_one():
    matrix = score_matrix(1.5, 1.1)
    outcomes = outcome_probabilities(matrix)
    assert sum(outcomes.values()) == pytest.approx(1.0, abs=1e-6)


def test_outcome_probabilities_favor_higher_lambda_team():
    matrix = score_matrix(2.2, 0.8)
    outcomes = outcome_probabilities(matrix)
    assert outcomes["home"] > outcomes["away"]


def test_symmetric_lambdas_give_equal_home_away_probability():
    matrix = score_matrix(1.3, 1.3)
    outcomes = outcome_probabilities(matrix)
    assert outcomes["home"] == pytest.approx(outcomes["away"], abs=1e-9)


def test_over_under_probability_sums_close_to_one_for_noninteger_line():
    matrix = score_matrix(1.5, 1.2, max_goals=20)
    ou = over_under_probability(matrix, 2.5)
    assert ou["over"] + ou["under"] == pytest.approx(1.0, abs=1e-6)


def test_btts_probability_complement():
    matrix = score_matrix(1.5, 1.2)
    btts = btts_probability(matrix)
    assert btts["yes"] + btts["no"] == pytest.approx(1.0, abs=1e-9)


def test_correct_score_probabilities_top_n():
    matrix = score_matrix(1.5, 1.2, max_goals=10)
    top3 = correct_score_probabilities(matrix, top_n=3)
    assert len(top3) == 3
    # sorted descending
    values = list(top3.values())
    assert values == sorted(values, reverse=True)


def test_team_goal_probability_matches_marginal():
    matrix = score_matrix(1.5, 1.2, max_goals=15)
    home_ou = team_goal_probability(matrix, "home", 1.5)
    # cross-check against the marginal distribution computed directly
    marginal_home = matrix.sum(axis=1)
    expected_over = float(np.sum(marginal_home[np.arange(len(marginal_home)) > 1.5]))
    assert home_ou["over"] == pytest.approx(expected_over)
