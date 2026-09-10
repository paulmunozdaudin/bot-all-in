"""As-of feature building (docs/DATA.md #4-5, docs/ARCHITECTURE.md #5).

This is the ONLY place "as-of" logic is allowed to live per
docs/ARCHITECTURE.md #5: every feature-building call takes a mandatory
`as_of` timestamp and only ever reads facts observed at or before it. It is
written against a generic `Fact` shape (not a live SQLAlchemy session) so it
can be unit-tested for leakage without a database, and so the exact same
function can later be pointed at either live DB rows or a backtest's
historical replay (docs/BACKTESTING.md #1) -- the leakage guarantee does not
change based on which caller invokes it.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Fact:
    match_id: int
    fact_type: str      # e.g. 'home_elo', 'away_elo', 'home_xg_avg', 'injury_status:PLAYER_123'
    value: float | str
    observed_at: datetime
    source: str


def facts_as_of(facts: list[Fact], match_id: int, as_of: datetime) -> list[Fact]:
    """Every fact for this match observed at or before `as_of`. Nothing later
    is ever returned, regardless of what else exists in `facts`."""
    return [f for f in facts if f.match_id == match_id and f.observed_at <= as_of]


def build_features_as_of(facts: list[Fact], match_id: int, as_of: datetime) -> dict[str, float | str]:
    """Latest known value per fact_type, as of `as_of`.

    If the same fact_type has multiple observations before `as_of` (e.g. Elo
    updated after each prior match), the most recent one wins -- this is
    what "as of" means: the best information available at that moment, not
    the eventual final value.
    """
    visible = facts_as_of(facts, match_id, as_of)
    latest_by_type: dict[str, Fact] = {}
    for fact in visible:
        current = latest_by_type.get(fact.fact_type)
        if current is None or fact.observed_at > current.observed_at:
            latest_by_type[fact.fact_type] = fact
    return {fact_type: fact.value for fact_type, fact in latest_by_type.items()}
