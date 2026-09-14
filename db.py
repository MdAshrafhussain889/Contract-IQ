"""
Database configuration and initialization for SQLite.
"""

import os
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Database URL - Using SQLite for simplicity
DATABASE_DIR = Path(__file__).parent / "data"
DATABASE_DIR.mkdir(exist_ok=True)
DATABASE_PATH = DATABASE_DIR / "contracts.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for debugging SQL queries
    connect_args={"check_same_thread": False}  # Required for SQLite
)


def init_db():
    """Initialize database and create tables."""
    try:
        SQLModel.metadata.create_all(engine)
        print(f"✅ Database initialized at: {DATABASE_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False


def get_session():
    """Get database session for queries."""
    with Session(engine) as session:
        yield session
