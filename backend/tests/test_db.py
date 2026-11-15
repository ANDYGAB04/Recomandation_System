import sqlite3

import pytest
from sqlalchemy import text

from app.db import create_db_engine


def test_database_file_is_created_with_missing_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "app.db"
    engine = create_db_engine(path)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    assert path.exists()


def test_foreign_keys_are_enforced_on_every_connection(tmp_path):
    engine = create_db_engine(tmp_path / "fk.db")
    with engine.begin() as conn:
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1
        conn.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY)"))
        conn.execute(text("CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))"))
    with pytest.raises(Exception) as excinfo, engine.begin() as conn:
        conn.execute(text("INSERT INTO child (id, parent_id) VALUES (1, 999)"))
    assert isinstance(excinfo.value.orig, sqlite3.IntegrityError)
