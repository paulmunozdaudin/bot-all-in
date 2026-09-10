"""Provider-agnostic ingestion adapter interface (docs/DATA.md #3).

No concrete adapter is wired to a live paid provider yet -- see
docs/ROADMAP.md Phase 2. This interface exists so that adding a real
provider later (starting with the free sources chosen in
docs/research/DATA_PROVIDERS.md) means implementing this contract once,
not redesigning the ingestion layer.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class SourceAdapter(ABC):
    """One adapter per external source. `source_name` must match the
    `source` column value used everywhere else in the schema (docs/DATA.md #1)."""

    source_name: str

    @abstractmethod
    def fetch_raw(self, endpoint: str, **params: Any) -> dict:
        """Calls the provider and returns the raw, unmodified payload.
        Callers are responsible for writing this to `raw_landing` before
        any normalization happens (docs/DATA.md #3)."""

    @abstractmethod
    def normalize(self, raw_payload: dict, fetched_at: datetime) -> list[dict]:
        """Maps a raw payload to rows for the core entity tables
        (docs/DATA.md #2), stamping `source` and the provider's own
        `observed_at` when the provider supplies one -- falling back to
        `fetched_at` only when it does not."""
