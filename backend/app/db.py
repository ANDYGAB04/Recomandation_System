"""Conexiunea la SQLite prin SQLModel."""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine


def create_db_engine(database_file: Path) -> Engine:
    database_file.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{database_file}",
        # FastAPI poate folosi conexiunea din alt fir de execuție decât cel care a creat-o.
        connect_args={"check_same_thread": False},
    )

    # SQLite verifică cheile externe doar dacă sunt activate pe fiecare conexiune.
    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine


def init_db(engine: Engine) -> None:
    """Creează tabelele care lipsesc și adaugă coloanele noi din LATE_COLUMNS; datele existente rămân."""
    from . import models  # noqa: F401  (înregistrează modelele în SQLModel.metadata)

    SQLModel.metadata.create_all(engine)
    _add_missing_columns(engine)


# Coloane adăugate după ce tabela exista deja (nu folosim migrări): (tabela, coloana, definiția SQL).
LATE_COLUMNS = [
    ("survey_responses", "is_test_data", "BOOLEAN NOT NULL DEFAULT 0"),
]


def _add_missing_columns(engine: Engine) -> None:
    """Adaugă coloanele noi în bazele de date create înainte de ele, fără să piardă datele."""
    with engine.begin() as connection:
        for table, column, definition in LATE_COLUMNS:
            existing = {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")}
            if existing and column not in existing:
                connection.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def session_scope(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session
