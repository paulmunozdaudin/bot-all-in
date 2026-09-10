"""Probability calibration (docs/MODEL.md #5): Platt scaling and isotonic regression.

Both are thin, explicit wrappers around scikit-learn so the calibration step
is a visible, swappable stage in the pipeline rather than buried inside a
model class. Fit only on a held-out calibration split -- never on the data
used to fit the base model or to evaluate final performance (see
docs/MODEL.md #5 and docs/BACKTESTING.md #4).
"""
from __future__ import annotations

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression


class PlattCalibrator:
    def __init__(self) -> None:
        self._model = LogisticRegression()
        self._fitted = False

    def fit(self, raw_scores: np.ndarray, binary_outcomes: np.ndarray) -> "PlattCalibrator":
        raw_scores = np.asarray(raw_scores, dtype=float).reshape(-1, 1)
        binary_outcomes = np.asarray(binary_outcomes, dtype=int)
        self._model.fit(raw_scores, binary_outcomes)
        self._fitted = True
        return self

    def predict(self, raw_scores: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("PlattCalibrator must be fit before predict")
        raw_scores = np.asarray(raw_scores, dtype=float).reshape(-1, 1)
        return self._model.predict_proba(raw_scores)[:, 1]


class IsotonicCalibrator:
    def __init__(self) -> None:
        self._model = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        self._fitted = False

    def fit(self, raw_scores: np.ndarray, binary_outcomes: np.ndarray) -> "IsotonicCalibrator":
        raw_scores = np.asarray(raw_scores, dtype=float)
        binary_outcomes = np.asarray(binary_outcomes, dtype=float)
        self._model.fit(raw_scores, binary_outcomes)
        self._fitted = True
        return self

    def predict(self, raw_scores: np.ndarray) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("IsotonicCalibrator must be fit before predict")
        return self._model.predict(np.asarray(raw_scores, dtype=float))
