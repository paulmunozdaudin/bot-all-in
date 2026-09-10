# Football AI

A data-driven football predictive-analytics and market-edge system.
**Not** a chatbot that gives opinions, and never a source of guaranteed
picks — every number here is a probability, calibrated and backtested, and
every claim about performance comes from an immutable, publicly
reconstructable prediction log. See `docs/MODEL.md` #8 and `docs/API.md`
for how "no certainty language" is enforced in code, not just copy.

This repo mirrors the `football-ai/` work originally built on the
`claude/football-ai-predictive-system-whstji` branch of `SpeakUp-Web`
(an unrelated app) — pulled out into its own repo so it can be deployed
and browsed independently, e.g. on Vercel.

## Repo layout

Unlike the original location, **the Next.js frontend lives at the repo
root** here (not under `frontend/`), so Vercel can import this repo with
zero configuration:

```
/                app/, components/, lib/  — Next.js + TypeScript + Tailwind frontend
/backend         FastAPI + the statistical/ML core (Python)
/docs            architecture, data, model, backtesting, market-edge,
                  combinations, API, deployment, experiments docs
/docs/research   Phase 0 data-provider research
/db/migrations   Postgres schema (leakage-safe, append-only, immutable predictions)
/infra           docker-compose.yml
```

## Status

Phases 0–1 (research, architecture) are complete. Phases 3, 5, 7, 9, 10, 11,
12 are scaffolded with real, tested code that works today on synthetic
data. Phases 2, 6, 8's final model choice, and 13–14 are genuinely not
started — they require a live data contract or a trained model against real
history, neither of which exists yet. See `ROADMAP.md` for the exact
per-phase status. Nothing here is faked to look further along than it is.

## Deploy the frontend on Vercel

Import this repo directly — no root-directory override needed, the
Next.js app is already at the repo root. Vercel will detect it and deploy
on `npm run build`.

**Note:** no backend is hosted anywhere yet, so `NEXT_PUBLIC_API_BASE_URL`
has nothing to point at in a Vercel deployment. Every page will honestly
show a "could not reach the API" / "no data yet" state — that is the
intended behavior (this product never fabricates predictions to fill a
gap), not a bug. To see it with live (still-synthetic, since no real data
is ingested) responses, run the backend locally per below and set
`NEXT_PUBLIC_API_BASE_URL` in a `.env` to point at it, or deploy `backend/`
somewhere that can run a long-lived Python process (Vercel's serverless
model isn't a natural fit for FastAPI + Postgres).

## Run it locally

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                 # 70+ unit tests for every stat module + service
uvicorn app.main:app --reload
```

Frontend:

```bash
cp .env.example .env      # or set NEXT_PUBLIC_API_BASE_URL yourself
npm install
npm run dev
```

Or both plus Postgres via Docker:

```bash
docker compose -f infra/docker-compose.yml up --build
```

## What's real right now vs. what's a placeholder

**Real, tested, working today** (71 unit tests passing in `backend/tests/`):
- Elo, independent Poisson, Dixon-Coles score matrices and derived markets
- Odds↔probability conversion, overround, normalization, EV
- Brier Score, Log Loss, calibration curves, Expected Calibration Error
- Platt scaling and isotonic regression calibration
- Monte Carlo simulation from a fitted joint score distribution
- Correlation-aware same-match joint probability (vs. naive independence)
- Walk-forward fold generation + fold scoring for backtesting
- The leakage-safety mechanism (`as_of` feature building) and its test suite
- Data-quality validators (duplicate facts, impossible values, timestamp
  ordering)
- Market Edge Engine's gated signal classifier (mechanism is real; the
  classification *thresholds* are explicitly marked as placeholders)
- Combination Engine's correlation-aware search + explicit
  "no strong combination found" result

**Explicitly not real yet** (and the code says so, rather than faking it):
- No live provider is connected — `backend/.env.example` has no real keys
- No historical dataset has been ingested, so no backtest has actually run
  against real data, and Market Edge Engine / Combination Engine thresholds
  are unvalidated placeholders
- No ML model has been trained (Phase 6) — only the baselines exist
- The frontend renders honest empty states everywhere real data is missing
