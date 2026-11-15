from app.config import BACKEND_DIR, Settings


def test_relative_database_path_is_inside_backend_dir():
    settings = Settings(database_path="data/x.db")
    assert settings.database_file == BACKEND_DIR / "data" / "x.db"


def test_cors_origins_are_parsed_from_a_comma_separated_list(monkeypatch):
    monkeypatch.setenv("HOBBYSHOP_CORS_ORIGINS", "http://a.test, http://b.test,")
    assert Settings().cors_origin_list == ["http://a.test", "http://b.test"]
