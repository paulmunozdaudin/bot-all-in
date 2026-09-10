import numpy as np
import pytest

from app.models_stat.metrics import (
    brier_score,
    calibration_curve,
    expected_calibration_error,
    log_loss,
)


def test_brier_score_hand_computed_example():
    # p=[0.5,0.3,0.2], one-hot true class 0 -> (0.5-1)^2+(0.3-0)^2+(0.2-0)^2 = 0.38
    probs = np.array([[0.5, 0.3, 0.2]])
    outcomes = np.array([[1, 0, 0]])
    assert brier_score(probs, outcomes) == pytest.approx(0.38)


def test_brier_score_zero_for_perfect_prediction():
    probs = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    outcomes = np.array([[1, 0, 0], [0, 1, 0]])
    assert brier_score(probs, outcomes) == pytest.approx(0.0)


def test_log_loss_hand_computed_example():
    probs = np.array([[0.5, 0.3, 0.2]])
    outcomes = np.array([[1, 0, 0]])
    expected = -np.log(0.5)
    assert log_loss(probs, outcomes) == pytest.approx(expected)


def test_log_loss_penalizes_confident_wrong_prediction_more():
    correct_confident = log_loss(np.array([[0.9, 0.1]]), np.array([[1, 0]]))
    wrong_confident = log_loss(np.array([[0.1, 0.9]]), np.array([[1, 0]]))
    assert wrong_confident > correct_confident


def test_calibration_curve_perfectly_calibrated_input():
    rng = np.random.default_rng(0)
    predicted = np.repeat([0.2, 0.8], 1000)
    outcomes = np.array([rng.random() < p for p in predicted]).astype(float)
    centers, mean_pred, observed = calibration_curve(predicted, outcomes, n_bins=10)
    assert len(centers) > 0
    # observed frequencies should track predicted probabilities reasonably closely
    assert np.allclose(mean_pred, observed, atol=0.1)


def test_expected_calibration_error_zero_when_perfectly_calibrated():
    # every prediction of 0.5 resolves true exactly half the time
    predicted = np.array([0.5] * 100)
    outcomes = np.array([1.0] * 50 + [0.0] * 50)
    ece = expected_calibration_error(predicted, outcomes, n_bins=10)
    assert ece == pytest.approx(0.0)
