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
    """Creează tabelele care lipsesc. Tabelele existente nu se modifică."""
    from . import models  # noqa: F401  (înregistrează modelele în SQLModel.metadata)

    SQLModel.metadata.create_all(engine)


def session_scope(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session
