"""Evaluation metrics for probability forecasts (docs/MODEL.md #6)."""
from __future__ import annotations

import numpy as np


def brier_score(probabilities: np.ndarray, outcomes: np.ndarray) -> float:
    """Multi-class Brier score.

    probabilities: (n_samples, n_classes), rows sum to 1.
    outcomes: (n_samples, n_classes), one-hot.
    Returns mean over samples of sum over classes of (p - y)^2.
    """
    probabilities = np.asarray(probabilities, dtype=float)
    outcomes = np.asarray(outcomes, dtype=float)
    if probabilities.shape != outcomes.shape:
        raise ValueError("probabilities and outcomes must have the same shape")
    return float(np.mean(np.sum((probabilities - outcomes) ** 2, axis=1)))


def log_loss(probabilities: np.ndarray, outcomes: np.ndarray, eps: float = 1e-15) -> float:
    """Multi-class log loss: -mean(log(p assigned to the true class))."""
    probabilities = np.asarray(probabilities, dtype=float)
    outcomes = np.asarray(outcomes, dtype=float)
    if probabilities.shape != outcomes.shape:
        raise ValueError("probabilities and outcomes must have the same shape")
    clipped = np.clip(probabilities, eps, 1 - eps)
    true_class_probs = np.sum(clipped * outcomes, axis=1)
    return float(-np.mean(np.log(true_class_probs)))


def calibration_curve(
    predicted_probabilities: np.ndarray, binary_outcomes: np.ndarray, n_bins: int = 10
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Reliability-diagram data for one class at a time (binary framing).

    Returns (bin_centers, mean_predicted, observed_frequency) for non-empty bins.
    """
    predicted_probabilities = np.asarray(predicted_probabilities, dtype=float)
    binary_outcomes = np.asarray(binary_outcomes, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(predicted_probabilities, bins) - 1, 0, n_bins - 1)

    bin_centers, mean_predicted, observed_freq = [], [], []
    for b in range(n_bins):
        mask = bin_idx == b
        if not np.any(mask):
            continue
        bin_centers.append((bins[b] + bins[b + 1]) / 2)
        mean_predicted.append(float(np.mean(predicted_probabilities[mask])))
        observed_freq.append(float(np.mean(binary_outcomes[mask])))
    return np.array(bin_centers), np.array(mean_predicted), np.array(observed_freq)


def expected_calibration_error(
    predicted_probabilities: np.ndarray, binary_outcomes: np.ndarray, n_bins: int = 10
) -> float:
    """Weighted-average absolute gap between predicted and observed frequency per bin."""
    predicted_probabilities = np.asarray(predicted_probabilities, dtype=float)
    binary_outcomes = np.asarray(binary_outcomes, dtype=float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    bin_idx = np.clip(np.digitize(predicted_probabilities, bins) - 1, 0, n_bins - 1)

    n = len(predicted_probabilities)
    ece = 0.0
    for b in range(n_bins):
        mask = bin_idx == b
        count = int(np.sum(mask))
        if count == 0:
            continue
        mean_pred = float(np.mean(predicted_probabilities[mask]))
        observed = float(np.mean(binary_outcomes[mask]))
        ece += (count / n) * abs(mean_pred - observed)
    return ece
