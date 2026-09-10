# Roadmap

Phases match the brief exactly (Section 26) and are gated: a phase does not
start with known, unresolved errors in the previous one (Section 27/"REGLA
ABSOLUTA").

| Phase | Scope | Status |
|---|---|---|
| 0 | Research data providers, compare, choose with justification | **Done** — `docs/research/DATA_PROVIDERS.md` |
| 1 | Architecture (this doc set) | **Done** — `docs/ARCHITECTURE.md`, `docs/DATA.md`, `docs/MODEL.md`, `docs/BACKTESTING.md`, `docs/MARKET_ENGINE.md`, `docs/COMBINATIONS.md`, `docs/API.md`, `docs/DEPLOYMENT.md`, `docs/EXPERIMENTS.md` |
| 2 | Data ingestion (real adapters against the free sources chosen in Phase 0) | **Not started** — requires provider signup decisions outside this session's scope; adapter interface is scaffolded in `backend/app/services/ingestion/` |
| 3 | Database | **Scaffolded** — `db/migrations/001_init.sql`, SQLAlchemy models in `backend/app/db/` |
| 4 | Feature engineering (as-of, leakage-safe) | **Scaffolded** — interface + leakage test defined, real feature set depends on Phase 2 data |
| 5 | Baseline models | **Implemented + tested** — `backend/app/models_stat/{baseline,elo,poisson,dixon_coles}.py` |
| 6 | ML models | Not started — needs a real historical dataset (Phase 2) to train against; stubbed module with the intended interface |
| 7 | Backtesting | **Framework implemented** — `backend/app/services/backtester.py`, exercised by unit tests against synthetic data; not yet run against real history (needs Phase 2) |
| 8 | Ensemble + calibration | Calibration utilities implemented (`models_stat/calibration.py`); ensemble selection needs real backtest data to decide between approaches per `MODEL.md` §4 |
| 9 | Market Edge Engine | **Core logic implemented** — `backend/app/services/market_edge_engine.py`; signal thresholds are placeholders pending real backtest data per `MARKET_ENGINE.md` §3 |
| 10 | Combination Engine | **Core logic implemented** — `backend/app/services/combination_engine/`; correlation model for same-match markets works today (derived from the joint Dixon-Coles distribution), cross-match correlation needs real data |
| 11 | Prediction API | **Scaffolded** — FastAPI skeleton with routers per `docs/API.md`; endpoints needing real data return explicit "no data yet" states, never fabricated numbers |
| 12 | Frontend | **Scaffolded** — Next.js app with the pages from Section 18-23 of the brief; honest empty states where no real prediction exists yet |
| 13 | Monitoring | Not started |
| 14 | Production | Not started |

## What "done" means at each phase in this repo right now

Every "Implemented" item above ships with unit tests and works correctly
**today**, on synthetic/example data, with zero fabrication — Elo, Poisson,
Dixon-Coles, odds↔probability conversion, EV, calibration, Brier/Log Loss,
Monte Carlo simulation, and correlation-aware combination probability are
real, tested code, not mocked output. What's explicitly **not** done is
anything that requires either (a) a live paid data contract (Phase 2's real
adapters) or (b) a trained model against real historical results (Phases 6,
8's final ensemble choice, 9's real thresholds) — those are correctly left
undone rather than faked, per the brief's Section 27 rule.

## Immediate next steps (not done in this session)

1. Decide and sign up for the Phase 0 recommended free-tier sources
   (football-data.org, Football-Data.co.uk CSV download) to get a first real
   historical dataset into `db/`.
2. Run the ingestion adapters against that data, populate Postgres.
3. Run the backtester for real (Phase 7) against baselines only, and record
   the first real `EXPERIMENTS.md` entries — including if baselines
   underperform, which is expected and fine at this stage.
4. Only then start Phase 6 (ML models), per the brief's explicit ordering.
