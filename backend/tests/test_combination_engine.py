from app.models_stat.correlation import Selection
from app.services.combination_engine import search_combinations


def test_no_strong_combination_found_is_a_valid_empty_result():
    # Two mediocre, negative-EV selections with no odds data supplied at all
    # should never be forced into a result (docs/COMBINATIONS.md #8).
    pool = [
        Selection(match_id=1, market="1x2", label="home", probability=0.35),
        Selection(match_id=2, market="1x2", label="away", probability=0.30),
        Selection(match_id=3, market="1x2", label="draw", probability=0.28),
    ]
    results = search_combinations(pool, max_selections=3, min_expected_value=0.05)
    assert results == []


def test_combination_conflicting_derived_markets_excluded():
    pool = [
        Selection(match_id=1, market="1x2_home", label="home", probability=0.55),
        Selection(match_id=1, market="double_chance_1x", label="1x", probability=0.78),
        Selection(match_id=2, market="1x2_home", label="home", probability=0.5),
    ]
    odds = {
        "1:1x2_home:home": 1.9,
        "1:double_chance_1x:1x": 1.25,
        "2:1x2_home:home": 2.0,
    }
    results = search_combinations(
        pool, max_selections=3, min_expected_value=-1.0, decimal_odds_by_selection=odds
    )
    # no result should combine selections 1's 1x2_home with its own double_chance_1x
    for r in results:
        markets_in_match_1 = {s.market for s in r.selections if s.match_id == 1}
        assert not {"1x2_home", "double_chance_1x"}.issubset(markets_in_match_1)


def test_positive_ev_combination_is_found_when_it_exists():
    pool = [
        Selection(match_id=1, market="1x2", label="home", probability=0.6),
        Selection(match_id=2, market="1x2", label="away", probability=0.6),
    ]
    # combined prob (independent, cross-match) = 0.36, odds give EV > 0
    odds = {"1:1x2:home": 2.0, "2:1x2:away": 3.5}
    results = search_combinations(
        pool, max_selections=2, min_expected_value=0.0, decimal_odds_by_selection=odds
    )
    assert len(results) == 1
    assert results[0].expected_value > 0
