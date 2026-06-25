"""SQLAlchemy engine and session for the Alpha runtime core loop."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SQLITE = _PROJECT_ROOT / "data" / "runtime_core.db"

Base = declarative_base()


def runtime_database_url() -> str:
    override = os.environ.get("RUNTIME_DATABASE_URL", "").strip()
    if override:
        return override
    _DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{_DEFAULT_SQLITE.as_posix()}"


def create_runtime_engine():
    url = runtime_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


engine = create_runtime_engine()
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def init_runtime_db() -> None:
    from src.runtime import models  # noqa: F401 — register mappers

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_runtime_engine(url: str, *, create_tables: bool = True) -> sessionmaker:
    """Test hook — point runtime ORM at an isolated database."""
    global engine, SessionLocal
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    engine = create_engine(url, connect_args=connect_args, future=True)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
    if create_tables:
        init_runtime_db()
    return SessionLocal
