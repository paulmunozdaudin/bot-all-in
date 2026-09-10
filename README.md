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
/render.yaml     Render Blueprint to deploy the backend for real
```

## Status

Phases 0–1 (research, architecture) are complete. Phases 3, 5, 7, 9, 10, 11,
12 are scaffolded with real, tested code that works today on synthetic
data. Phase 2's ingestion code is written and unit-tested but has not yet
pulled live data (see below — this dev environment has no open internet
access). Phases 6, 8's final model choice, and 13–14 are genuinely not
started — they require a trained model against real history, which doesn't
exist yet. See `ROADMAP.md` for the exact per-phase status. Nothing here is
faked to look further along than it is.

## Deploy the frontend on Vercel

Import this repo directly — no root-directory override needed, the
Next.js app is already at the repo root. Vercel will detect it and deploy
on `npm run build`. A `.vercelignore` keeps the Python backend out of
Vercel's project scanner, since Vercel's serverless model isn't a fit for
a long-lived FastAPI process — that's what `render.yaml` is for (below).

**Without a live backend, every page honestly shows "could not reach the
API" / "no data yet"** — intended behavior (this product never fabricates
predictions to fill a gap), not a bug. Follow "Getting real data live"
below to see it with actually-ingested matches.

## Getting real data live: Postgres (Supabase) + backend (Render) + this Vercel frontend

The fastest path to a fully real, live deployment, free-tier only:

1. **Database — a free Supabase Postgres project.** Create one at
   supabase.com, open its SQL Editor, paste the full contents of
   `db/migrations/001_init.sql`, and run it once. Copy the connection
   string (Settings → Database → Connection string) as `DATABASE_URL`.
2. **Backend — Render, via `render.yaml` at this repo's root.** In Render:
   New → Blueprint → point at this repo. Set `DATABASE_URL` (from step 1)
   and `CORS_ALLOW_ORIGINS` (this Vercel URL) when prompted.
3. **Backfill historical seasons once**, from Render's Shell tab:
   ```
   python -m scripts.ingest_football_data_co_uk --league E0 --seasons 2223 2324 2425 2526
   ```
   Real Football-Data.co.uk results and closing odds — no signup needed
   for that source. Swap `--league` for `SP1`/`D1`/`I1`/`F1` for other
   leagues.
4. **Connect this frontend** — set `NEXT_PUBLIC_API_BASE_URL` on this
   Vercel project to the Render service's URL, then redeploy.

Full details and the reasoning behind each choice: `docs/DEPLOYMENT.md`.

## Run it locally

Backend:

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                 # 76 unit tests for every stat module + service
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

**Real, tested, working today** (76 unit tests passing in `backend/tests/`):
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
- A real Football-Data.co.uk ingestion adapter + runnable script
  (`backend/app/services/ingestion/football_data_co_uk_adapter.py`,
  `backend/scripts/ingest_football_data_co_uk.py`) — CSV parsing is
  unit-tested against real column layouts, but has not been run against
  live data from the dev environment that built this (see below)

**Explicitly not real yet** (and the code says so, rather than faking it):
- No live provider has actually been ingested from yet. The adapter code
  is real and tested, but the dev sandbox that built this had no outbound
  internet access to external data providers at all (confirmed directly).
  "Getting real data live" above gives the exact steps to run it for real
- Until that's run, no backtest has actually run against real data, and
  Market Edge Engine / Combination Engine thresholds are unvalidated
  placeholders
- No ML model has been trained (Phase 6) — only the baselines exist
- The frontend renders honest empty states everywhere real data is missing
