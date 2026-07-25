"""
PRISM Voice Assistant — Database Session & Initialization
Provides SQLAlchemy engine, session factory, and schema bootstrap.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_URL
from app.db.models import Base
from app.utils.logger import get_logger

logger = get_logger(__name__)

is_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}

# ── Engine ──────────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

if is_sqlite:
    # Enable WAL mode for better concurrent read performance with SQLite
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_con, _connection_record):
        cursor = dbapi_con.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Create all tables if they don't exist. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized at %s", DATABASE_URL)

    # Seed a default user + preferences if the DB is brand new
    with get_session() as session:
        from app.db.repository import UserRepository
        if not UserRepository.get_default_user(session):
            UserRepository.create_default_user(session)
            logger.info("Default user and preferences seeded.")


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
