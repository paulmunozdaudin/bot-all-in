"""Market Edge Engine (docs/MARKET_ENGINE.md).

Implements the odds->comparison pipeline (steps 1-6) plus the gated signal
classifier (step 7 / docs/MARKET_ENGINE.md #3). The classifier takes its
gate inputs explicitly rather than reaching into a database, so it is
testable in isolation and reusable identically from the live API and the
backtester.

IMPORTANT: the level thresholds below are placeholders, clearly marked as
such. Per docs/MARKET_ENGINE.md #3, real thresholds must be fit and
validated against backtest data (docs/BACKTESTING.md) before this engine is
used to drive real product decisions -- this module ships the mechanism,
not tuned production thresholds, because no backtest has been run yet
(docs/ROADMAP.md, Phase 9 status).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.models_stat.odds import compare_to_market


class SignalLevel(str, Enum):
    NO_SIGNAL = "NO_SIGNAL"
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"
    VERY_STRONG = "VERY_STRONG"


@dataclass(frozen=True)
class EdgeGates:
    """Explicit inputs for every check docs/MARKET_ENGINE.md #3 requires before
    a raw probability gap is allowed to be shown as anything above NO_SIGNAL."""

    data_quality_ok: bool
    min_sample_size_met: bool
    model_agreement: float          # 0..1, higher = models agree more (less uncertainty)
    historical_calibration_ok: bool  # was this probability/market/league bucket well-calibrated historically?
    edge_stable_across_snapshots: bool
    cross_bookmaker_consensus: bool


@dataclass(frozen=True)
class EdgeSignal:
    level: SignalLevel
    diff_pp: float
    ev: float
    reasons: list[str]


# Placeholder thresholds (docs/MARKET_ENGINE.md #3) -- to be replaced with
# values fit against docs/BACKTESTING.md output before production use.
_MIN_AGREEMENT_FOR_ANY_SIGNAL = 0.6
_MODERATE_DIFF_PP = 5.0
_STRONG_DIFF_PP = 10.0
_VERY_STRONG_DIFF_PP = 15.0


def classify_signal(
    model_probability: float,
    decimal_odds: float,
    market_implied_probabilities: list[float],
    gates: EdgeGates,
) -> EdgeSignal:
    comparison = compare_to_market(model_probability, decimal_odds, market_implied_probabilities)
    reasons: list[str] = []

    if not gates.data_quality_ok:
        reasons.append("data_quality_insufficient")
        return EdgeSignal(SignalLevel.NO_SIGNAL, comparison.diff_pp, comparison.ev, reasons)

    if not gates.min_sample_size_met:
        reasons.append("insufficient_historical_sample_size")
        return EdgeSignal(SignalLevel.NO_SIGNAL, comparison.diff_pp, comparison.ev, reasons)

    if gates.model_agreement < _MIN_AGREEMENT_FOR_ANY_SIGNAL:
        reasons.append("model_disagreement_too_high")
        return EdgeSignal(SignalLevel.NO_SIGNAL, comparison.diff_pp, comparison.ev, reasons)

    if not gates.historical_calibration_ok:
        reasons.append("bucket_not_historically_well_calibrated")
        return EdgeSignal(SignalLevel.NO_SIGNAL, comparison.diff_pp, comparison.ev, reasons)

    if comparison.diff_pp <= 0:
        reasons.append("no_positive_edge")
        return EdgeSignal(SignalLevel.NO_SIGNAL, comparison.diff_pp, comparison.ev, reasons)

    if not gates.edge_stable_across_snapshots:
        reasons.append("edge_unstable_across_snapshots")
        return EdgeSignal(SignalLevel.WEAK, comparison.diff_pp, comparison.ev, reasons)

    if not gates.cross_bookmaker_consensus:
        reasons.append("isolated_to_single_bookmaker")
        return EdgeSignal(SignalLevel.WEAK, comparison.diff_pp, comparison.ev, reasons)

    if comparison.diff_pp >= _VERY_STRONG_DIFF_PP:
        level = SignalLevel.VERY_STRONG
    elif comparison.diff_pp >= _STRONG_DIFF_PP:
        level = SignalLevel.STRONG
    elif comparison.diff_pp >= _MODERATE_DIFF_PP:
        level = SignalLevel.MODERATE
    else:
        level = SignalLevel.WEAK
    reasons.append("all_gates_passed")
    return EdgeSignal(level, comparison.diff_pp, comparison.ev, reasons)
