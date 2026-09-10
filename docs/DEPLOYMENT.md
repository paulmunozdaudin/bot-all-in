# Deployment

No production infrastructure exists yet (Phase 14 of `ROADMAP.md`). This
document describes the intended path so later phases don't have to
re-derive it, and so `infra/docker-compose.yml` is written toward a
consistent target.

## Real data ingestion — why it can't run from a dev sandbox

The development environment this project was built in has outbound network
access restricted to a small allowlist (package registries, GitHub) by
organization policy — it cannot reach football-data.co.uk, football-data.org,
or any other external data provider. This was confirmed directly: both a
raw HTTP request and the web-fetch tool returned an explicit
`EGRESS_BLOCKED` error for football-data.co.uk. This isn't a bug to route
around; it means Phase 2 ingestion must run somewhere with real internet
egress — a laptop, CI runner, or a hosted platform like Render below —
never assumed to have "just worked" from inside a locked-down dev session.

## Getting real data live: Postgres (Supabase) + backend (Render) + frontend (Vercel)

This is the fastest path to a fully real, live deployment using only free
tiers and no new paid contracts (consistent with `docs/research/DATA_PROVIDERS.md`'s
"prove it before paying for anything" conclusion):

1. **Database — a free Supabase Postgres project.** Create one at
   supabase.com, open its SQL Editor, paste the full contents of
   `db/migrations/001_init.sql`, and run it once. Copy the project's
   connection string (Settings → Database → Connection string, "URI" /
   session pooler form) — this is your `DATABASE_URL`.
2. **Backend — Render, via the `render.yaml` blueprint at the repo root.**
   In Render: New → Blueprint → point at this repo. It defines a web
   service (the FastAPI app, `backend/Dockerfile`) and a weekly cron job
   that keeps the current season topped up. When prompted, set:
   - `DATABASE_URL` — from step 1
   - `CORS_ALLOW_ORIGINS` — your Vercel frontend's URL, once you have it
   Render's servers have normal outbound internet access, so
   `backend/scripts/ingest_football_data_co_uk.py` — which cannot run from
   this dev sandbox — runs there without issue.
3. **Backfill historical seasons once.** After the web service is live,
   open its Shell tab in Render (or run the cron job's "Run Job Now") and
   run:
   ```
   python -m scripts.ingest_football_data_co_uk --league E0 --seasons 2223 2324 2425 2526
   ```
   This is real Football-Data.co.uk data — actual results and closing
   odds — landing in the actual schema, not synthetic fixtures. Swap
   `--league` for `SP1` (La Liga), `D1` (Bundesliga), `I1` (Serie A), or
   `F1` (Ligue 1) to add more competitions.
4. **Connect the frontend.** On the Vercel project, set
   `NEXT_PUBLIC_API_BASE_URL` to the Render service's URL (Project Settings
   → Environment Variables), then redeploy. The frontend's honest
   "no data yet" states (`components/EmptyState.tsx`) will now show real
   ingested matches instead, wherever a real prediction/backtest exists —
   and will keep showing an honest empty state for anything that still
   doesn't (no ML model is trained yet even once this data lands; see
   `ROADMAP.md`).

None of this — real ingested data, a live backend, or a model trained on
real history — existed as of the initial scaffold in this repo. Once
someone runs the steps above, `ROADMAP.md` and this section should be
updated to say so, with real numbers, not "should work."

## Local development

```
cp .env.example .env   # fill in nothing required yet — no live provider keys exist
docker compose -f infra/docker-compose.yml up --build
```

Brings up: Postgres, the FastAPI backend (`uvicorn` with reload), and the
Next.js frontend (`next dev`). See `infra/docker-compose.yml`.

## Migrations

Raw SQL migrations in `db/migrations/`, applied in filename order. No ORM
auto-migration is used in production paths — schema changes are explicit,
reviewed SQL, because the prediction/leakage invariants in `DATA.md` depend
on exact column semantics (e.g. `observed_at` vs `ingested_at`) that an
auto-generated migration could silently get wrong.

## Environments (target, not yet stood up)

- **staging**: mirrors production configuration against a smaller/synthetic
  dataset, used to validate a new model version's serving path (not its
  statistical validity — that's the backtester's job) before promotion.
- **production**: containerized backend + frontend behind a reverse proxy,
  managed Postgres with automated backups (prediction history is
  effectively an audit log — brief Section 15 — and must not be lossy),
  secrets injected via environment variables from the platform's secret
  store, never committed (see `.env.example` — no key ever has a real
  value in version control).

## Model promotion

A new model version is only deployed to serve live predictions after:
1. It has a walk-forward backtest report (`BACKTESTING.md`) showing
   out-of-sample improvement over the currently-served version on the
   metrics in `BACKTESTING.md` §2.
2. Leakage tests pass against its exact feature set.
3. It is recorded in `EXPERIMENTS.md` with a decision (ship / don't ship)
   and the reasoning.

This gate is a process requirement now and a CI-enforced one once the admin
promotion workflow (Phase 13/14) exists.

## Monitoring (Phase 13 target)

- Data freshness per source (last successful ingestion timestamp vs.
  expected cadence).
- Prediction pipeline error rate.
- Live calibration drift: rolling Brier Score/Log Loss on recently-resolved
  predictions compared against the backtested expectation for the deployed
  model version — a persistent gap is a signal to investigate before it's a
  signal to retrain.
