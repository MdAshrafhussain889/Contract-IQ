"""
Database configuration and initialization for SQLite.
"""

import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import inspect, text
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


def _run_lightweight_migrations():
    """
    Add columns that exist on the models but not yet in an existing table.

    SQLModel/SQLAlchemy's create_all() only creates missing tables; it never
    alters existing ones. This keeps older databases usable without Alembic.
    """
    inspector = inspect(engine)

    # Imported here to avoid an import cycle at module load time.
    from models.contract_extract import ContractExtract

    table_name = ContractExtract.__tablename__
    if table_name not in inspector.get_table_names():
        return

    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}

    with engine.begin() as conn:
        for column in ContractExtract.__table__.columns:
            if column.name in existing_columns:
                continue
            if not column.nullable and column.default is None:
                print(
                    f"WARNING: Skipping non-nullable column without default: "
                    f"{table_name}.{column.name}"
                )
                continue
            column_type = column.type.compile(engine.dialect)
            conn.execute(
                text(f'ALTER TABLE {table_name} ADD COLUMN "{column.name}" {column_type}')
            )
            print(f"Added missing column: {table_name}.{column.name}")


def init_db():
    """Initialize database, create tables, and apply lightweight migrations."""
    try:
        SQLModel.metadata.create_all(engine)
        _run_lightweight_migrations()
        print(f"Database initialized at: {DATABASE_PATH}")
        return True
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False


def get_session():
    """Get database session for queries."""
    with Session(engine) as session:
        yield session
