-- Football AI — initial schema
-- Design invariants (see docs/DATA.md):
--   * every fact table carries source, observed_at, ingested_at
--   * market_odds_snapshot is append-only (never UPDATE a price, INSERT a new row)
--   * prediction is append-only / immutable once written (see trigger below)
--   * outcome is a separate table attached after the fact, never merged into prediction

CREATE TABLE IF NOT EXISTS competition (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    country         TEXT,
    external_ref    TEXT,               -- provider-specific id, for adapter mapping
    source          TEXT NOT NULL,
    UNIQUE (source, external_ref)
);

CREATE TABLE IF NOT EXISTS season (
    id              SERIAL PRIMARY KEY,
    competition_id  INTEGER NOT NULL REFERENCES competition(id),
    label           TEXT NOT NULL,       -- e.g. '2025/2026'
    start_date      DATE,
    end_date        DATE,
    UNIQUE (competition_id, label)
);

CREATE TABLE IF NOT EXISTS team (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    country         TEXT,
    external_ref    TEXT,
    source          TEXT NOT NULL,
    UNIQUE (source, external_ref)
);

CREATE TABLE IF NOT EXISTS match (
    id              SERIAL PRIMARY KEY,
    competition_id  INTEGER NOT NULL REFERENCES competition(id),
    season_id       INTEGER NOT NULL REFERENCES season(id),
    home_team_id    INTEGER NOT NULL REFERENCES team(id),
    away_team_id    INTEGER NOT NULL REFERENCES team(id),
    kickoff_at      TIMESTAMPTZ NOT NULL,
    status          TEXT NOT NULL DEFAULT 'scheduled', -- scheduled|live|finished|postponed|cancelled
    external_ref    TEXT,
    source          TEXT NOT NULL,
    UNIQUE (source, external_ref)
);
CREATE INDEX IF NOT EXISTS idx_match_kickoff ON match (kickoff_at);

-- Final/point-in-time match stats. Multiple rows per match are allowed
-- (e.g. a live-stat snapshot mid-match and a final one) — observed_at
-- disambiguates which is which; the as-of feature builder always picks the
-- latest row with observed_at <= as_of.
CREATE TABLE IF NOT EXISTS match_stats (
    id                  SERIAL PRIMARY KEY,
    match_id            INTEGER NOT NULL REFERENCES match(id),
    home_goals          SMALLINT,
    away_goals          SMALLINT,
    home_shots          SMALLINT,
    away_shots          SMALLINT,
    home_shots_on_target SMALLINT,
    away_shots_on_target SMALLINT,
    home_corners        SMALLINT,
    away_corners        SMALLINT,
    home_cards          SMALLINT,
    away_cards          SMALLINT,
    home_possession_pct NUMERIC(5,2),
    away_possession_pct NUMERIC(5,2),
    home_xg             NUMERIC(5,2),
    away_xg             NUMERIC(5,2),
    is_final            BOOLEAN NOT NULL DEFAULT FALSE,
    source              TEXT NOT NULL,
    observed_at         TIMESTAMPTZ NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_match_stats_match ON match_stats (match_id, observed_at);

-- Time series of team ratings (Elo, form, attack/defense strength, etc.)
-- One row per (team, as_of) — never mutated, new rating = new row.
CREATE TABLE IF NOT EXISTS team_rating (
    id              SERIAL PRIMARY KEY,
    team_id         INTEGER NOT NULL REFERENCES team(id),
    rating_type     TEXT NOT NULL,      -- 'elo' | 'attack_strength' | 'defense_strength' | ...
    value           NUMERIC(10,4) NOT NULL,
    as_of           TIMESTAMPTZ NOT NULL, -- point in time this rating is valid from
    source          TEXT NOT NULL,      -- 'internal_elo_model' for our own computed ratings
    observed_at     TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_team_rating_lookup ON team_rating (team_id, rating_type, as_of);

CREATE TABLE IF NOT EXISTS player (
    id              SERIAL PRIMARY KEY,
    team_id         INTEGER REFERENCES team(id),
    name            TEXT NOT NULL,
    position        TEXT,
    external_ref    TEXT,
    source          TEXT NOT NULL,
    UNIQUE (source, external_ref)
);

CREATE TABLE IF NOT EXISTS player_match_stat (
    id              SERIAL PRIMARY KEY,
    player_id       INTEGER NOT NULL REFERENCES player(id),
    match_id        INTEGER NOT NULL REFERENCES match(id),
    minutes_played  SMALLINT,
    goals           SMALLINT,
    assists         SMALLINT,
    xg              NUMERIC(5,2),
    xa              NUMERIC(5,2),
    source          TEXT NOT NULL,
    observed_at     TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Availability facts (injuries/suspensions) with an explicit validity
-- window and the moment the fact became known (reported_at) — this is the
-- table the leakage tests exercise most directly, since "reported_at" is
-- what must be compared against a prediction's data_cutoff_at.
CREATE TABLE IF NOT EXISTS player_availability (
    id              SERIAL PRIMARY KEY,
    player_id       INTEGER NOT NULL REFERENCES player(id),
    status          TEXT NOT NULL,      -- 'injured' | 'suspended' | 'available' | 'doubtful'
    reason          TEXT,
    reported_at     TIMESTAMPTZ NOT NULL,   -- when this became known
    effective_from  TIMESTAMPTZ,
    effective_to    TIMESTAMPTZ,
    source          TEXT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_player_availability_lookup ON player_availability (player_id, reported_at);

CREATE TABLE IF NOT EXISTS match_context (
    id                      SERIAL PRIMARY KEY,
    match_id                INTEGER NOT NULL REFERENCES match(id),
    home_rest_days          SMALLINT,
    away_rest_days          SMALLINT,
    home_matches_last_14d   SMALLINT,
    away_matches_last_14d   SMALLINT,
    stage_importance_score  NUMERIC(4,3),  -- 0..1, e.g. dead rubber vs. title decider
    source                  TEXT NOT NULL,
    observed_at             TIMESTAMPTZ NOT NULL,
    ingested_at             TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Append-only odds time series. Never UPDATE a row — every price change is
-- a new INSERT. Opening/current/closing/movement are all derived by query.
CREATE TABLE IF NOT EXISTS market_odds_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    match_id        INTEGER NOT NULL REFERENCES match(id),
    bookmaker       TEXT NOT NULL,
    market          TEXT NOT NULL,       -- '1x2' | 'over_under_2.5' | 'btts' | ...
    selection       TEXT NOT NULL,       -- 'home' | 'draw' | 'away' | 'over' | 'under' | ...
    decimal_odds    NUMERIC(8,3) NOT NULL CHECK (decimal_odds >= 1.0),
    observed_at     TIMESTAMPTZ NOT NULL,
    source          TEXT NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_odds_lookup
    ON market_odds_snapshot (match_id, bookmaker, market, selection, observed_at);

-- Predictions are logged before kickoff and never edited. feature_snapshot
-- is a JSON dump of the exact feature vector used, so "what did the model
-- know" (docs/DATA.md §5) is always reconstructable without re-querying
-- historical state that may have since changed.
CREATE TABLE IF NOT EXISTS prediction (
    id                  BIGSERIAL PRIMARY KEY,
    match_id            INTEGER NOT NULL REFERENCES match(id),
    market              TEXT NOT NULL,
    model_version       TEXT NOT NULL,
    probabilities       JSONB NOT NULL,   -- {"home": 0.537, "draw": 0.254, "away": 0.209}
    confidence          NUMERIC(5,2),     -- 0..100, model-agreement/data-quality score
    feature_snapshot    JSONB NOT NULL,
    data_cutoff_at      TIMESTAMPTZ NOT NULL, -- as_of used for feature building
    generated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (match_id, market, model_version, data_cutoff_at)
);
CREATE INDEX IF NOT EXISTS idx_prediction_match ON prediction (match_id, market);

-- Enforce immutability at the database level: once inserted, a prediction
-- row can never be updated or deleted (brief Section 15). Outcomes are
-- attached via a separate table instead.
CREATE OR REPLACE FUNCTION prevent_prediction_mutation() RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'prediction rows are append-only and cannot be updated or deleted (id=%)',
        COALESCE(OLD.id, NEW.id);
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prediction_no_update ON prediction;
CREATE TRIGGER trg_prediction_no_update
    BEFORE UPDATE OR DELETE ON prediction
    FOR EACH ROW EXECUTE FUNCTION prevent_prediction_mutation();

CREATE TABLE IF NOT EXISTS outcome (
    id              BIGSERIAL PRIMARY KEY,
    prediction_id   BIGINT NOT NULL REFERENCES prediction(id),
    actual_result   TEXT NOT NULL,   -- the realized selection/outcome for this market
    resolved_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (prediction_id)
);

-- Raw landing area: unmodified provider payloads, for full replay of the
-- normalization step (docs/DATA.md §3).
CREATE TABLE IF NOT EXISTS raw_landing (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    payload         JSONB NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_raw_landing_lookup ON raw_landing (source, endpoint, fetched_at);
