import pytest

from app.models_stat.baseline import frequency_baseline


def test_frequency_baseline_sums_to_one():
    outcomes = ["H"] * 45 + ["D"] * 25 + ["A"] * 30
    baseline = frequency_baseline(outcomes)
    assert sum(baseline.values()) == pytest.approx(1.0)
    assert baseline["H"] == pytest.approx(0.45)
    assert baseline["D"] == pytest.approx(0.25)
    assert baseline["A"] == pytest.approx(0.30)


def test_frequency_baseline_rejects_empty_input():
    with pytest.raises(ValueError):
        frequency_baseline([])
