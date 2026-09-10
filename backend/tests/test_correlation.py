import pytest

from app.models_stat.correlation import Selection, combined_probability, flag_derived_market_conflict
from app.models_stat.poisson import score_matrix


def test_same_match_correlated_selections_differ_from_independence_product():
    matrix = score_matrix(1.6, 1.1, max_goals=12)

    home_win = Selection(
        match_id=1, market="1x2", label="home", probability=0.5, predicate=lambda h, a: h > a
    )
    over_1_5 = Selection(
        match_id=1,
        market="over_1.5",
        label="over",
        probability=0.6,
        predicate=lambda h, a: h + a > 1.5,
    )

    joint_prob, method = combined_probability([home_win, over_1_5], same_match_matrix=matrix)
    naive_product = home_win.probability * over_1_5.probability

    assert method == "exact_joint_same_match"
    # Home win and Over 1.5 are positively correlated (winning often requires
    # scoring), so the true joint probability should exceed the naive product.
    assert joint_prob > naive_product


def test_cross_match_falls_back_to_independence_and_says_so():
    a = Selection(match_id=1, market="1x2", label="home", probability=0.5)
    b = Selection(match_id=2, market="1x2", label="away", probability=0.3)

    prob, method = combined_probability([a, b])
    assert method == "independence_assumed_cross_match"
    assert prob == pytest.approx(0.15)


def test_same_match_without_predicates_falls_back_explicitly():
    a = Selection(match_id=1, market="1x2", label="home", probability=0.5)
    b = Selection(match_id=1, market="btts", label="yes", probability=0.55)

    prob, method = combined_probability([a, b])
    assert method == "independence_assumed_same_match"
    assert prob == pytest.approx(0.275)


def test_flag_derived_market_conflict_detects_double_chance_overlap():
    assert flag_derived_market_conflict("1x2_home", "double_chance_1x") is True
    assert flag_derived_market_conflict("over_2.5", "under_2.5") is True
    assert flag_derived_market_conflict("1x2_home", "btts_yes") is False
