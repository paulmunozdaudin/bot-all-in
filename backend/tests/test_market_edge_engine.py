from app.services.market_edge_engine import EdgeGates, SignalLevel, classify_signal

_GOOD_GATES = EdgeGates(
    data_quality_ok=True,
    min_sample_size_met=True,
    model_agreement=0.9,
    historical_calibration_ok=True,
    edge_stable_across_snapshots=True,
    cross_bookmaker_consensus=True,
)


def test_poor_data_quality_forces_no_signal_regardless_of_gap():
    gates = EdgeGates(**{**_GOOD_GATES.__dict__, "data_quality_ok": False})
    signal = classify_signal(0.90, 3.0, [0.30, 0.45, 0.25], gates)
    assert signal.level == SignalLevel.NO_SIGNAL
    assert "data_quality_insufficient" in signal.reasons


def test_insufficient_sample_size_forces_no_signal():
    gates = EdgeGates(**{**_GOOD_GATES.__dict__, "min_sample_size_met": False})
    signal = classify_signal(0.90, 3.0, [0.30, 0.45, 0.25], gates)
    assert signal.level == SignalLevel.NO_SIGNAL


def test_low_model_agreement_forces_no_signal():
    gates = EdgeGates(**{**_GOOD_GATES.__dict__, "model_agreement": 0.2})
    signal = classify_signal(0.90, 3.0, [0.30, 0.45, 0.25], gates)
    assert signal.level == SignalLevel.NO_SIGNAL


def test_negative_edge_is_no_signal_even_with_perfect_gates():
    # model thinks 20%, market implies (normalized) 40% -> no edge
    signal = classify_signal(0.20, 3.0, [0.40, 0.35, 0.25], _GOOD_GATES)
    assert signal.level == SignalLevel.NO_SIGNAL
    assert "no_positive_edge" in signal.reasons


def test_unstable_edge_capped_at_weak_even_with_large_gap():
    gates = EdgeGates(**{**_GOOD_GATES.__dict__, "edge_stable_across_snapshots": False})
    signal = classify_signal(0.90, 3.0, [0.30, 0.45, 0.25], gates)
    assert signal.level == SignalLevel.WEAK


def test_isolated_bookmaker_capped_at_weak():
    gates = EdgeGates(**{**_GOOD_GATES.__dict__, "cross_bookmaker_consensus": False})
    signal = classify_signal(0.90, 3.0, [0.30, 0.45, 0.25], gates)
    assert signal.level == SignalLevel.WEAK


def test_large_stable_consensus_edge_reaches_very_strong():
    # model 90% vs. normalized market 30% -> 60pp gap, all gates pass
    signal = classify_signal(0.90, 3.0, [0.30, 0.45, 0.25], _GOOD_GATES)
    assert signal.level == SignalLevel.VERY_STRONG
    assert signal.ev > 0
