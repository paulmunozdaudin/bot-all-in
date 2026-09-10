import numpy as np

from app.models_stat.calibration import IsotonicCalibrator, PlattCalibrator


def _synthetic_miscalibrated_data(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    true_prob = rng.uniform(0, 1, size=n)
    # raw score is a monotonic but "overconfident" transform of true probability
    raw_score = np.clip(0.5 + 1.5 * (true_prob - 0.5), 0, 1)
    outcomes = (rng.random(n) < true_prob).astype(int)
    return raw_score, outcomes, true_prob


def test_platt_calibrator_improves_calibration():
    raw_score, outcomes, true_prob = _synthetic_miscalibrated_data()
    calibrator = PlattCalibrator().fit(raw_score, outcomes)
    calibrated = calibrator.predict(raw_score)

    raw_error = np.mean(np.abs(raw_score - true_prob))
    calibrated_error = np.mean(np.abs(calibrated - true_prob))
    assert calibrated_error < raw_error


def test_isotonic_calibrator_improves_calibration():
    raw_score, outcomes, true_prob = _synthetic_miscalibrated_data()
    calibrator = IsotonicCalibrator().fit(raw_score, outcomes)
    calibrated = calibrator.predict(raw_score)

    raw_error = np.mean(np.abs(raw_score - true_prob))
    calibrated_error = np.mean(np.abs(calibrated - true_prob))
    assert calibrated_error < raw_error


def test_calibrators_raise_if_predict_before_fit():
    import pytest

    with pytest.raises(RuntimeError):
        PlattCalibrator().predict([0.5])
    with pytest.raises(RuntimeError):
        IsotonicCalibrator().predict([0.5])
