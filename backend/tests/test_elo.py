import pytest

from app.models_stat.elo import expected_score, goal_diff_multiplier, update_ratings


def test_expected_score_equal_ratings_is_half():
    assert expected_score(1500, 1500) == pytest.approx(0.5)


def test_expected_score_higher_rating_favored():
    assert expected_score(1700, 1500) > 0.5
    assert expected_score(1500, 1700) < 0.5


def test_expected_score_symmetric():
    a = expected_score(1600, 1400)
    b = expected_score(1400, 1600)
    assert a + b == pytest.approx(1.0)


def test_goal_diff_multiplier_matches_known_bands():
    assert goal_diff_multiplier(0) == 1.0
    assert goal_diff_multiplier(1) == 1.0
    assert goal_diff_multiplier(2) == 1.5
    assert goal_diff_multiplier(3) == pytest.approx((11 + 3) / 8.0)


def test_update_ratings_zero_sum():
    # rating gained by one side must equal rating lost by the other
    result = update_ratings(1500, 1500, home_goals=2, away_goals=0, k=20, home_advantage=0)
    delta_home = result.new_home_rating - 1500
    delta_away = result.new_away_rating - 1500
    assert delta_home == pytest.approx(-delta_away)
    assert delta_home > 0  # home team won, rating should rise


def test_update_ratings_draw_with_home_advantage_favors_away():
    # a draw against a team you were favored to beat should reduce your rating
    result = update_ratings(1600, 1500, home_goals=1, away_goals=1, k=20, home_advantage=100)
    assert result.new_home_rating < 1600
    assert result.new_away_rating > 1500
