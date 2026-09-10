"""Shared response schemas. No field here may encode certainty (brief
Section 16) -- there is deliberately no `will_win`, `guaranteed`, or
`sure_bet` field anywhere in this module.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class OutcomeProbabilities(BaseModel):
    """A market's probabilities. Must sum to 1 within floating-point tolerance."""

    probabilities: dict[str, float]

    @field_validator("probabilities")
    @classmethod
    def _validate(cls, value: dict[str, float]) -> dict[str, float]:
        for label, p in value.items():
            if not 0.0 <= p <= 1.0:
                raise ValueError(f"probability for '{label}' out of [0,1]: {p}")
        total = sum(value.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"probabilities must sum to 1.0, got {total}")
        return value


class ModelMeta(BaseModel):
    model_version: str
    generated_at: datetime
    data_cutoff_at: datetime


class NoDataResponse(BaseModel):
    """Explicit, honest empty state -- returned instead of fabricated numbers
    whenever real ingested/backtested data does not exist yet (brief Section 27:
    'if a model has insufficient confidence: NO SIGNAL', applied at the API layer
    to the current pre-ingestion state of this project)."""

    status: str = "NO_DATA"
    reason: str
