"""
Database engine and session management.
"""
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/storage_scraper.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite + FastAPI
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables if they don't exist, then run column migrations."""
    Base.metadata.create_all(bind=engine)
    _migrate()


def _migrate() -> None:
    """Add columns that may be missing from older DB schemas (SQLite-safe)."""
    _add_column_if_missing("listings", "auction_type", "VARCHAR")
    _add_column_if_missing("listings", "watched",      "BOOLEAN DEFAULT 0")
    _add_column_if_missing("listings", "notes",        "TEXT")


def _add_column_if_missing(table: str, column: str, col_type: str) -> None:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        existing = {row[1] for row in rows}
        if column not in existing:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
            conn.commit()


def get_db():
    """FastAPI dependency: yields a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
