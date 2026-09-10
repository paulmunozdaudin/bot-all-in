# Data Architecture

## 1. Source-of-truth principle

Every fact stored in this system keeps four things, no exceptions
(brief Section 3):

```
source      -- which provider/feed produced this value
timestamp   -- when the value became known/observed (NOT when we ingested it,
               if the provider tells us the real observation time; otherwise
               ingestion time is used and flagged as such)
match_id    -- which match this fact relates to (nullable for team/player-level
               facts not tied to one match)
value       -- the actual data, typed per table
```

This is implemented as `observed_at` + `ingested_at` + `source` columns on
every fact table (see `db/migrations/001_init.sql`), so both "when did this
become true" and "when did we learn about it" are recoverable — they are not
the same thing (a lineup announced at T-60min is *observed* then, even if a
retry ingests it a minute later).

## 2. Core entities

### Match data
`match`, `match_stats` — date, competition, season, home/away team, goals,
shots, shots on target, corners, cards, possession, xG, xGA. One row per
match per stat-snapshot-time where relevant (e.g., in-play stats are
timestamped, not just a final-state row).

### Team data
`team_rating` (time series) — Elo, form (rolling), home/away split
performance, attack/defense strength, xG/xGA, strength of schedule. Always
timestamped so "Elo entering match X" is reconstructable exactly.

### Player data
`player`, `player_match_stat`, `player_availability` — minutes, goals,
assists, xG, xA, injury/suspension status with `reported_at` and
`effective_from`/`effective_to` validity windows (so we know exactly when an
injury became known, not just when it started).

### Context
`match_context` — rest days since last match, matches played in trailing N
days (congestion), travel distance, competition, round/stage, a computed
"stakes" score (e.g., relegation/title/knockout).

### Market
`market_odds_snapshot` — bookmaker, market, selection, decimal odds,
`observed_at`. Append-only time series per bookmaker/market/selection so
opening/current/closing and full movement are all just queries over this
table, never separate mutable fields.

## 3. Ingestion layer

`backend/app/services/ingestion/<provider>_adapter.py` — one adapter per
external source (see `docs/research/DATA_PROVIDERS.md` for the chosen
sources). Each adapter:

1. Calls the provider's API/feed.
2. Writes the raw response, unmodified, to a `raw_landing` table/object
   store, keyed by `(source, endpoint, fetched_at)` — nothing is normalized
   in place, so a normalization bug is always replayable from raw data.
2. A separate `normalizer` step maps raw payloads to the core entities above,
   stamping `source` and the provider's own `observed_at` when available.

No adapter is wired to a paid provider yet (Phase 2 starts against the free
sources identified in Phase 0). The adapter interface is provider-agnostic
by design so swapping football-data.org → Sportmonks later touches one file.

## 4. Data leakage — enforcement, not just a guideline

This is flagged CRITICAL in the brief (Section 4) and is treated as a hard
invariant, not a best-effort convention:

- Every feature-building query takes a mandatory `as_of: datetime` parameter.
- `tests/test_leakage.py` builds features for a fixture "as of T-48h" twice —
  once against a database state truncated at T-48h, once against the full
  database including post-match data — and asserts identical output.
- Odds features use the **last snapshot at or before `as_of`**, never
  "closing odds", when the prediction is meant to simulate a pre-match
  decision point.
- Backtesting (see `BACKTESTING.md`) replays history match-by-match in date
  order and only exposes the backtester to rows with `observed_at <= as_of`
  for the simulated prediction time — the same code path production uses.

## 5. Reconstructability requirement

For any historical prediction row, the system must answer: *"what
information did the model have when it predicted this?"* This is why
predictions store a `feature_snapshot` (the exact feature vector used) and a
`data_cutoff_at` timestamp alongside the probability output — not just the
final probability. See `db/migrations/001_init.sql` (`prediction` table) and
`API.md`.

## 6. Data quality tests (brief Section 24)

`backend/tests/test_data_quality.py` covers:
- missing required fields
- duplicate `(source, match_id, timestamp)` facts
- impossible values (e.g., probability outside [0,1], negative minutes
  played, goals not a non-negative integer, odds < 1.0)
- timestamp ordering (kickoff time must be after fixture announcement, etc.)
