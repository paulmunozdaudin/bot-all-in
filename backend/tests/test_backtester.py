from datetime import date

import numpy as np
import pytest

from app.services.backtester import (
    expanding_window_folds,
    is_out_of_sample_improvement,
    score_fold,
)


def test_expanding_window_folds_matches_brief_example():
    folds = expanding_window_folds(
        overall_start=date(2018, 1, 1),
        fold_boundaries=[date(2023, 1, 1), date(2024, 1, 1), date(2025, 1, 1)],
        overall_end=date(2026, 1, 1),
    )
    assert len(folds) == 3
    assert folds[0].train_start == date(2018, 1, 1)
    assert folds[0].train_end == date(2023, 1, 1)
    assert folds[0].test_start == date(2023, 1, 1)
    assert folds[0].test_end == date(2024, 1, 1)
    # train window always starts at overall_start and expands, never slides
    assert folds[1].train_start == date(2018, 1, 1)
    assert folds[2].train_start == date(2018, 1, 1)
    assert folds[2].test_end == date(2026, 1, 1)


def test_folds_never_overlap_train_and_test():
    folds = expanding_window_folds(
        date(2018, 1, 1), [date(2023, 1, 1), date(2024, 1, 1)], date(2025, 1, 1)
    )
    for fold in folds:
        assert fold.train_end <= fold.test_start


def test_score_fold_rejects_empty_predictions():
    from app.services.backtester import Fold

    fold = Fold(date(2018, 1, 1), date(2023, 1, 1), date(2023, 1, 1), date(2024, 1, 1))
    with pytest.raises(ValueError):
        score_fold(fold, np.empty((0, 3)), np.empty((0, 3)))


def test_is_out_of_sample_improvement_detects_better_candidate():
    from app.services.backtester import Fold, FoldReport

    fold = Fold(date(2018, 1, 1), date(2023, 1, 1), date(2023, 1, 1), date(2024, 1, 1))
    baseline = [FoldReport(fold, n_predictions=100, brier=0.60, log_loss=1.0, ece=0.05)]
    better_candidate = [FoldReport(fold, n_predictions=100, brier=0.55, log_loss=0.95, ece=0.04)]
    worse_candidate = [FoldReport(fold, n_predictions=100, brier=0.65, log_loss=1.05, ece=0.06)]

    assert is_out_of_sample_improvement(better_candidate, baseline) is True
    assert is_out_of_sample_improvement(worse_candidate, baseline) is False
