"""SQLAlchemy engine/session setup. The schema itself is owned by the raw
SQL migrations in db/migrations/ (docs/DEPLOYMENT.md #Migrations) -- these
models are a typed read/write layer over that schema, not the source of
truth for it.
"""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
