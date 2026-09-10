# Modeling

## 1. Pipeline (brief Section 17)

```
RAW DATA → FEATURE ENGINEERING → STATISTICAL MODELS → ML MODELS → ENSEMBLE
→ CALIBRATION → FINAL PROBABILITIES → MARKET COMPARISON → LLM EXPLANATION
```

The LLM sits **only** at the last step. It receives already-computed
probabilities, edges, and factor summaries as structured input and produces
natural-language explanation — it never generates or adjusts a number
(brief Section 17). This boundary is enforced in code: the LLM
service (`app/services/llm_explainer.py`) takes a frozen, already-serialized
`PredictionResult` object and has no access to the database or model code.

## 2. Baselines (implemented first, in `backend/app/models_stat/`)

- **Home/Draw/Away frequency** (`baseline.py`) — the naive base-rate model.
  Every other model must beat this out-of-sample or it doesn't ship.
- **Elo** (`elo.py`) — standard Elo with home advantage and goal-difference
  scaled K-factor, updated match-by-match in date order.
- **Poisson** (`poisson.py`) — independent Poisson goal models for home/away
  expected goals, derived from attack/defense strength ratings; match outcome
  and score-line probabilities computed from the resulting bivariate
  distribution.
- **Dixon-Coles** (`dixon_coles.py`) — Poisson model with the low-score
  correlation adjustment (the ρ term) from Dixon & Coles (1997), which
  corrects the independent-Poisson model's known bias on 0-0/1-0/0-1/1-1
  scorelines.

These four are implemented as pure functions/classes operating on
`numpy`/`pandas` inputs, with no I/O, so they are unit-testable against known
closed-form results (see `backend/tests/`).

## 3. Machine learning models (Phase 6)

Once baselines exist and are backtested, evaluate, don't assume:

- Logistic Regression (multinomial, for 1X2)
- Random Forest
- Gradient Boosting (sklearn)
- XGBoost
- LightGBM, only if it earns its place empirically (brief explicitly warns
  against assuming more complexity is better — Section 5)

All ML models are trained on the **same feature set** produced by the
as-of feature builder (`DATA.md` §4), so comparisons are apples-to-apples.

## 4. Ensembling (Phase 8)

Compare, with results logged, not assumed:
- best single model
- weighted average ensemble (weights tuned on a validation fold, not the
  test fold)
- stacking (meta-learner on out-of-fold predictions)

The **selection between these is made exclusively by out-of-sample walk-forward
results** (`BACKTESTING.md`), never by which one looks more sophisticated.

## 5. Calibration (Phase 8)

Raw model outputs — especially from tree ensembles — are not automatically
well-calibrated probabilities. Two standard techniques, chosen per-model by
which improves calibration metrics out-of-sample:
- **Platt scaling** (logistic fit of true outcome on raw score) — preferred
  when the raw score is roughly monotonic and data is limited.
- **Isotonic regression** — more flexible, needs more data to avoid
  overfitting the calibration curve itself.

Calibration is fit on a held-out calibration split, never on the same data
used to fit the base model or to evaluate final performance (that would leak
information about the test set into the calibration curve).

## 6. Evaluation metrics

- **Brier Score** — mean squared error of the predicted probability vector
  against the one-hot outcome; primary scoring rule for calibration quality.
- **Log Loss** — penalizes confident wrong predictions harder; secondary
  scoring rule.
- **Calibration curves / reliability diagrams** — predicted probability
  bucket vs. observed frequency; a well-calibrated model's points sit on the
  diagonal.
- **Accuracy** — reported for interpretability only; never used alone to
  select a model, since a model can be "accurate" (picks the most likely
  outcome) while being poorly calibrated (bad for EV-based decisions).

All four are implemented in `backend/app/models_stat/metrics.py` and unit
tested against hand-computed values.

## 7. Markets covered

- Match result (1X2)
- Expected home/away goals, total expected goals
- Over/Under (per line, e.g. 2.5)
- BTTS (both teams to score)
- Clean sheet
- Correct score (from the fitted Dixon-Coles score matrix)
- Double chance (derived from 1X2, not independently modeled — it's a
  deterministic function of P(Home), P(Draw), P(Away))
- Team goals (over/under per team, from the marginal Poisson distributions)

Every market probability is produced by the same pipeline above — there is
no separate "Correct Score model" invented ad hoc; correct score comes
directly from the Dixon-Coles joint distribution, over/under and BTTS from
the same joint distribution's marginals/derived events, so all markets for a
match are internally consistent with each other (this consistency is exactly
what the Combination Engine's correlation handling in `COMBINATIONS.md`
depends on).

## 8. Language rules

No output field or generated text may claim certainty. `PredictionResult`
schema (`API.md`) has no boolean "will_win" field — only probabilities,
confidence scores (a measure of model agreement/data quality, not
outcome certainty), and historical performance stats. This is enforced by
the Pydantic response schema itself, not just a copywriting convention.
