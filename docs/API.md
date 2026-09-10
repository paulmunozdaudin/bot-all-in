# API

FastAPI backend, versioned under `/api/v1`. This document tracks intended
surface area; only endpoints actually implemented in `backend/app/api/routers/`
are marked **[implemented]** — everything else is the Phase 11 target shape,
not a promise of current behavior.

## Conventions

- All probabilities are floats in `[0, 1]`; probabilities over a market's
  outcomes sum to 1 (± floating point tolerance), enforced by Pydantic
  validators on the response schemas.
- No response field encodes certainty (no `will_win`, no `guaranteed`
  fields exist anywhere in the schema — brief Section 16).
- Every prediction-bearing response includes `generated_at` and
  `data_cutoff_at` timestamps and a `model_version` string.
- Errors use standard HTTP status codes + a JSON `{"detail": "..."}` body.

## Health / Admin

- `GET /api/v1/health` **[implemented]** — liveness + DB connectivity check.
- `GET /api/v1/admin/status` — API status, data freshness per source, model
  version, last backtest run, error log summary (Section 23).

## Matches

- `GET /api/v1/matches/today` — today's matches with model summary
  (Section 19: Home page).
- `GET /api/v1/matches/{match_id}` — full match page payload (Section 20):
  prediction, probabilities, expected goals, form, injuries, context,
  model explanation, market analysis, edge analysis, historical model
  performance for this bucket, timestamp.

## Predictions

- `POST /api/v1/predict/{match_id}` — internal/admin trigger to (re)compute
  and log a prediction for a match ahead of kickoff (idempotent per
  `data_cutoff_at`; never overwrites an already-logged prediction — brief
  Section 15).
- `GET /api/v1/predictions/{prediction_id}` — the immutable historical
  prediction record, exactly as logged.

## Opportunities (Market Scanner, Section 21)

- `GET /api/v1/opportunities` — matches/markets where model probability
  exceeds normalized market-implied probability, passing the Market Edge
  Engine's gates (`MARKET_ENGINE.md`), ordered by signal quality. Query
  params: `league`, `market`, `min_edge`, `min_confidence`, `date`,
  `bookmaker`. Returns an empty list (not fabricated rows) when nothing
  clears the bar for the given filters, including when historical sample
  size is insufficient for a bucket.

## Combinations (Combination Lab, Section 22)

- `POST /api/v1/combinations/search` — body: date range, competitions,
  markets, max selections, risk profile. Returns ranked combinations
  (`COMBINATIONS.md`) or an explicit
  `{"result": "NO_STRONG_COMBINATION_FOUND", "reason": "..."}` payload.

## Track record (Section 15)

- `GET /api/v1/track-record/summary` — total predictions, correct
  predictions, Brier Score, Log Loss, calibration summary, CLV, breakdowns
  by confidence/league/market.
- `GET /api/v1/track-record/predictions` — paginated, filterable list of
  every historical prediction with its logged probability and (once known)
  outcome — never edited after the fact.

## Backtesting / Experiments (admin-only, Section 23/EXPERIMENTS.md)

- `GET /api/v1/admin/backtests` — list of backtest runs + summary metrics.
- `GET /api/v1/admin/backtests/{run_id}` — full fold-by-fold report.
- `GET /api/v1/admin/experiments` — ablation/experiment log (`EXPERIMENTS.md`).

## Auth

Not yet designed in detail — Phase 11 target is: public read access to
match/opportunity/track-record data (this product's credibility depends on
public visibility of the track record, brief Section 15), admin routes
behind authenticated access. No auth is implemented in the current
scaffold; admin routers are not mounted publicly by default.
