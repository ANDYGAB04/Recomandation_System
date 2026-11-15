import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=tmp_path / "test.db", secret_key="test")


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c
