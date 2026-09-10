"""Walk-forward backtesting framework (docs/BACKTESTING.md).

This module implements the fold-generation and metric-aggregation
machinery generically over dates, so it is unit-testable against synthetic
data without a database. Wiring it against real historical data (running it
end-to-end against ingested matches) is Phase 7's remaining work per
docs/ROADMAP.md -- that requires the Phase 2 data ingestion this session
does not perform.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np

from app.models_stat.metrics import brier_score, expected_calibration_error, log_loss


@dataclass(frozen=True)
class Fold:
    train_start: date
    train_end: date  # exclusive
    test_start: date
    test_end: date  # exclusive


def expanding_window_folds(
    overall_start: date, fold_boundaries: list[date], overall_end: date
) -> list[Fold]:
    """Builds expanding-window folds from a list of test-window boundaries.

    Example: expanding_window_folds(2018-01-01, [2023-01-01, 2024-01-01, 2025-01-01], 2026-01-01)
    -> Fold(train 2018-2023, test 2023-2024), Fold(train 2018-2024, test 2024-2025),
       Fold(train 2018-2025, test 2025-2026)

    Train windows always start at overall_start and expand -- they never
    slide -- and a fold's test window never overlaps its own train window,
    matching docs/BACKTESTING.md #1's explicit ban on random/shuffled splits.
    """
    if len(fold_boundaries) < 2:
        raise ValueError("need at least two boundaries to form one fold")
    boundaries = sorted(fold_boundaries)
    folds = []
    for i in range(len(boundaries) - 1):
        folds.append(
            Fold(
                train_start=overall_start,
                train_end=boundaries[i],
                test_start=boundaries[i],
                test_end=boundaries[i + 1],
            )
        )
    if boundaries[-1] < overall_end:
        folds.append(
            Fold(
                train_start=overall_start,
                train_end=boundaries[-1],
                test_start=boundaries[-1],
                test_end=overall_end,
            )
        )
    return folds


@dataclass(frozen=True)
class FoldReport:
    fold: Fold
    n_predictions: int
    brier: float
    log_loss: float
    ece: float


def score_fold(fold: Fold, probabilities: np.ndarray, outcomes: np.ndarray) -> FoldReport:
    """Scores one fold's predictions. probabilities/outcomes are (n, n_classes)."""
    if len(probabilities) == 0:
        raise ValueError("cannot score an empty fold -- report zero predictions explicitly upstream")
    # ECE is computed per-class-as-binary and averaged, since it is defined
    # for a binary event; for a 3-way market we average the home/draw/away
    # binary calibration errors.
    class_eces = [
        expected_calibration_error(probabilities[:, k], outcomes[:, k])
        for k in range(probabilities.shape[1])
    ]
    return FoldReport(
        fold=fold,
        n_predictions=len(probabilities),
        brier=brier_score(probabilities, outcomes),
        log_loss=log_loss(probabilities, outcomes),
        ece=float(np.mean(class_eces)),
    )


def is_out_of_sample_improvement(
    candidate_reports: list[FoldReport], baseline_reports: list[FoldReport]
) -> bool:
    """A model only ships if its aggregate out-of-sample Brier Score beats the
    baseline's, across the same folds (docs/BACKTESTING.md #5, docs/MODEL.md #2).
    """
    if len(candidate_reports) != len(baseline_reports):
        raise ValueError("candidate and baseline must be scored on the same folds")
    candidate_weighted_brier = _weighted_mean(
        [r.brier for r in candidate_reports], [r.n_predictions for r in candidate_reports]
    )
    baseline_weighted_brier = _weighted_mean(
        [r.brier for r in baseline_reports], [r.n_predictions for r in baseline_reports]
    )
    return candidate_weighted_brier < baseline_weighted_brier


def _weighted_mean(values: list[float], weights: list[int]) -> float:
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("total weight must be positive")
    return sum(v * w for v, w in zip(values, weights)) / total_weight
