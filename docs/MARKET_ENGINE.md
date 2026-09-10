# Market Edge Engine

## 1. Purpose

Compare the system's own calibrated probabilities against market-implied
probabilities and classify the discrepancy — never claim a guaranteed
opportunity from a raw number gap (brief Section 8).

## 2. Pipeline

1. **Ingest odds** — decimal odds per bookmaker/market/selection with
   `observed_at` (`DATA.md` §2, market table).
2. **Convert odds → implied probability**: `implied = 1 / decimal_odds`.
3. **Estimate the overround (bookmaker margin)**: sum of implied
   probabilities across all selections in a market, minus 1
   (`overround = sum(implied) - 1`).
4. **Normalize** implied probabilities to remove the margin, so they sum to
   1 and are comparable to model probabilities:
   `normalized_i = implied_i / sum(implied)`. (This uses the simple
   proportional/multiplicative method by default; the module is structured
   to allow swapping in Shin's method later if backtesting shows it tracks
   true probabilities better for favorite-longshot-biased markets — that
   choice is itself decided empirically, not assumed.)
5. **Compare**: `diff = model_probability - normalized_market_probability`,
   reported in percentage points.
6. **Expected value**: `EV = model_probability * decimal_odds - 1`, computed
   against the **raw** (non-normalized) decimal odds actually available to
   bet, since that's the price that determines real returns.

## 3. Signal classification — not just "big gap = good"

A raw probability gap is a candidate signal, not a conclusion. Before a
signal is shown as anything above `NO SIGNAL`, the engine checks, all
implemented as explicit, backtested gates in
`backend/app/services/market_edge_engine.py`:

- **Data quality** — are the inputs (both model features and odds) complete
  and recent enough? Stale or partial data forces `NO SIGNAL`.
- **Model uncertainty** — how much do the ensemble's constituent models
  agree with each other for this specific match? High disagreement caps the
  signal level regardless of the raw gap.
- **Historical calibration in this exact bucket** — has the model been
  well-calibrated, historically, for predictions in this probability range,
  this market, this league? (Pulled from the backtest report, `BACKTESTING.md`.)
- **Sample size** — how many historical predictions exist in this
  league/market/confidence combination? Below a configured minimum, the
  signal is capped at `NO SIGNAL` — insufficient evidence is not evidence of
  an edge.
- **Edge stability** — has the gap persisted across the last N odds
  snapshots, or is it a one-tick anomaly likely to be a data error or about
  to be corrected by the market?
- **Cross-bookmaker consensus** — does the gap exist against most books, or
  is it isolated to one (more likely a pricing error/stale line at that
  specific book, not real market inefficiency)?
- **Market movement direction** (`MARKET_ENGINE.md` §4 below) — is the line
  moving toward or away from the model's view?

Only after these gates does the engine assign a level:

```
NO SIGNAL   < MODEL_UNCERTAINTY or sample-size gate fails
WEAK        small, unstable gap
MODERATE    moderate gap, passes stability + sample-size gates
STRONG      large gap, passes all gates, cross-book consensus
VERY STRONG large gap, all gates pass with wide margin, historically
            well-calibrated bucket
```

The exact thresholds between these levels are **fit and validated against
backtest data** (`BACKTESTING.md`), not chosen by feel, and are versioned
alongside the model version they were calibrated for.

## 4. Market movement

`market_movement.py` tracks, per bookmaker/market/selection, from the
append-only `market_odds_snapshot` table:
- opening price (earliest snapshot)
- current/live price (latest snapshot ≤ now)
- closing price (latest snapshot before kickoff)
- direction and magnitude of movement over time
- degree of consensus across bookmakers (dispersion of current prices)

**Closing Line Value (CLV)**: for every signal the engine has historically
generated, the backtester checks whether the price at signal time beat the
closing price. A model whose signals systematically anticipate favorable
line movement (positive average CLV) is doing something a model with
negative CLV is not — this is one of the strongest available proxies for
real predictive skill, since closing lines are famously efficient.

**No lookahead**: the live engine only ever sees snapshots up to "now"; the
backtested version of the same code only ever sees snapshots up to the
simulated `as_of` (`DATA.md` §4) — never the actual closing price when
"now" is meant to simulate a pre-close decision point.

## 5. What this engine explicitly does not do

- It does not stake or place bets.
- It does not promise a result (brief Section 16).
- It does not surface a signal when historical sample size in that bucket is
  insufficient — it returns `NO SIGNAL` and says so, which is treated as a
  correct, useful answer, not a failure of the system.
