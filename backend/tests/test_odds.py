import pytest

from app.models_stat.odds import (
    compare_to_market,
    decimal_to_implied_probability,
    expected_value,
    normalize_probabilities,
    overround,
)


def test_decimal_to_implied_probability():
    assert decimal_to_implied_probability(2.0) == pytest.approx(0.5)
    assert decimal_to_implied_probability(4.0) == pytest.approx(0.25)


def test_decimal_to_implied_probability_rejects_invalid_odds():
    with pytest.raises(ValueError):
        decimal_to_implied_probability(0.5)


def test_overround_positive_for_realistic_market():
    # 1.90 / 3.60 / 4.20 decimal odds -> implied sums to > 1 (bookmaker margin)
    implied = [decimal_to_implied_probability(o) for o in (1.90, 3.60, 4.20)]
    assert overround(implied) > 0


def test_normalize_probabilities_sums_to_one():
    implied = [decimal_to_implied_probability(o) for o in (1.90, 3.60, 4.20)]
    normalized = normalize_probabilities(implied)
    assert sum(normalized) == pytest.approx(1.0)


def test_expected_value_matches_example_from_brief():
    # EV = model_probability * decimal_odds - 1
    ev = expected_value(0.578, 2.0)
    assert ev == pytest.approx(0.578 * 2.0 - 1.0)


def test_expected_value_rejects_invalid_probability():
    with pytest.raises(ValueError):
        expected_value(1.5, 2.0)


def test_compare_to_market_example_from_brief():
    # Market probability 46.2%, model probability 57.8% -> diff +11.6pp (brief Section 8).
    # Full 3-way market implied probabilities summing to exactly 1.0 (no margin),
    # so normalization is a no-op and the target selection stays at 46.2%.
    decimal_odds = 1 / 0.462
    comparison = compare_to_market(0.578, decimal_odds, [0.462, 0.312, 0.226])
    assert comparison.diff_pp == pytest.approx(11.6, abs=0.1)
    assert comparison.ev == pytest.approx(0.578 * decimal_odds - 1.0)
