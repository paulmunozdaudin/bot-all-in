"""SQLAlchemy models mirroring db/migrations/001_init.sql. Column names and
constraints must stay in sync with that file -- it is the schema's source
of truth (docs/DEPLOYMENT.md), this module is a typed mapping onto it.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Competition(Base):
    __tablename__ = "competition"
    __table_args__ = (UniqueConstraint("source", "external_ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String)
    source: Mapped[str] = mapped_column(String, nullable=False)


class Team(Base):
    __tablename__ = "team"
    __table_args__ = (UniqueConstraint("source", "external_ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str | None] = mapped_column(String)
    external_ref: Mapped[str | None] = mapped_column(String)
    source: Mapped[str] = mapped_column(String, nullable=False)


class Season(Base):
    __tablename__ = "season"
    __table_args__ = (UniqueConstraint("competition_id", "label"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competition.id"), nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[datetime | None] = mapped_column(DateTime)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)


class Match(Base):
    __tablename__ = "match"
    __table_args__ = (UniqueConstraint("source", "external_ref"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competition.id"), nullable=False)
    season_id: Mapped[int] = mapped_column(ForeignKey("season.id"), nullable=False)
    home_team_id: Mapped[int] = mapped_column(ForeignKey("team.id"), nullable=False)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("team.id"), nullable=False)
    kickoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="scheduled")
    external_ref: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)


class MatchStats(Base):
    __tablename__ = "match_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match.id"), nullable=False)
    home_goals: Mapped[int | None] = mapped_column(SmallInteger)
    away_goals: Mapped[int | None] = mapped_column(SmallInteger)
    home_shots: Mapped[int | None] = mapped_column(SmallInteger)
    away_shots: Mapped[int | None] = mapped_column(SmallInteger)
    home_shots_on_target: Mapped[int | None] = mapped_column(SmallInteger)
    away_shots_on_target: Mapped[int | None] = mapped_column(SmallInteger)
    home_corners: Mapped[int | None] = mapped_column(SmallInteger)
    away_corners: Mapped[int | None] = mapped_column(SmallInteger)
    home_cards: Mapped[int | None] = mapped_column(SmallInteger)
    away_cards: Mapped[int | None] = mapped_column(SmallInteger)
    home_possession_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    away_possession_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
    home_xg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    away_xg: Mapped[float | None] = mapped_column(Numeric(5, 2))
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketOddsSnapshot(Base):
    """Append-only. No update()/delete() path should ever be called against
    this table in application code -- every price change is a new row
    (docs/DATA.md #2)."""

    __tablename__ = "market_odds_snapshot"
    __table_args__ = (CheckConstraint("decimal_odds >= 1.0"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match.id"), nullable=False)
    bookmaker: Mapped[str] = mapped_column(String, nullable=False)
    market: Mapped[str] = mapped_column(String, nullable=False)
    selection: Mapped[str] = mapped_column(String, nullable=False)
    decimal_odds: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Prediction(Base):
    """Append-only / immutable at the DB level -- see the
    prevent_prediction_mutation trigger in db/migrations/001_init.sql.
    Application code must never issue an UPDATE/DELETE against this table;
    the trigger exists precisely so that a bug here fails loudly instead of
    silently rewriting history (brief Section 15)."""

    __tablename__ = "prediction"
    __table_args__ = (UniqueConstraint("match_id", "market", "model_version", "data_cutoff_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match.id"), nullable=False)
    market: Mapped[str] = mapped_column(String, nullable=False)
    model_version: Mapped[str] = mapped_column(String, nullable=False)
    probabilities: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feature_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    data_cutoff_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Outcome(Base):
    __tablename__ = "outcome"
    __table_args__ = (UniqueConstraint("prediction_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("prediction.id"), nullable=False)
    actual_result: Mapped[str] = mapped_column(String, nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
