# Deployment

No production infrastructure exists yet (Phase 14 of `ROADMAP.md`). This
document describes the intended path so later phases don't have to
re-derive it, and so `infra/docker-compose.yml` is written toward a
consistent target.

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
