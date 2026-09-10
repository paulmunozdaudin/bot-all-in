# Backtesting Framework

## 1. Walk-forward validation, not random splits

Brief Section 13 is explicit: never mix future and past randomly. The
backtester (`backend/app/services/backtester.py`) implements expanding-window
walk-forward validation:

```
Fold 1:  Train 2018-2022        Test 2023
Fold 2:  Train 2018-2023        Test 2024
Fold 3:  Train 2018-2024        Test 2025
```

Each fold:
1. Trains/fits every model **only** on matches with kickoff before the test
   window's start.
2. For every match in the test window, builds features using the as-of
   feature builder with `as_of = kickoff_time - prediction_lead_time`
   (configurable, e.g. 48h before kickoff) — reusing the exact same
   leakage-safe code path as production (`DATA.md` §4).
3. Generates predictions for every market in scope.
4. Scores predictions once the true outcome is known.

A single global train/test split, or k-fold cross-validation with shuffling,
is explicitly disallowed for model selection here — both would leak future
information into training via arbitrary fold membership.

## 2. What gets measured, per fold and in aggregate

- Accuracy
- Brier Score
- Log Loss
- Calibration (reliability diagram + Expected Calibration Error)
- ROI (using either flat staking or a defined staking plan — configurable,
  always logged) against the historical odds available **at prediction
  time**, never closing odds, when simulating a betting decision
- Maximum drawdown of the simulated bankroll
- CLV (Closing Line Value): the difference between the price taken and the
  closing price, signed so positive CLV means we beat the closing line
- Breakdowns: performance by market, by league, by season, by confidence
  bucket, by edge-size bucket (deciles)

## 3. Backtest report artifact

Every backtest run writes a versioned report (JSON + a rendered summary) to
`backend/app/services/backtester_reports/` (git-ignored in production, but
the schema is fixed) including: model version, feature set version, date
range, fold boundaries, and every metric above. This is the artifact
`EXPERIMENTS.md` and the admin dashboard (`docs/API.md` admin routes) read
from — there is exactly one source of truth for "did this model actually
work," and it's this report, not a claim in a commit message.

## 4. No peeking

- Calibration fitting (`MODEL.md` §5) uses a split strictly inside the
  training window of each fold, never touching the test window.
- Hyperparameter tuning uses a validation split *inside* the training
  window (e.g., last season of the training window held out), never the
  test window.
- Any reported "backtest result" that used the test window for anything
  other than final scoring is invalid by definition and must be discarded,
  not adjusted.

## 5. Rule about negative results (brief Section 27)

If a fold's out-of-sample Brier Score is worse than the frequency baseline,
that is reported as-is. The system is explicitly required to be able to
conclude "this model/edge does not hold up" and stop recommending it — this
is a feature, not something to smooth over. `EXPERIMENTS.md` tracks these
outcomes, including negative ones, as the historical experiment log.
