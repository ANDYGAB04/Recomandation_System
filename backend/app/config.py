"""Configurarea aplicației, citită din variabile de mediu cu prefixul HOBBYSHOP_ sau din backend/.env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HOBBYSHOP_", env_file=BACKEND_DIR / ".env", extra="ignore")

    # Relativă la directorul backend/, ca aplicația să găsească aceeași bază de date indiferent de unde e pornită.
    database_path: Path = Path("data/hobbyshop.db")
    secret_key: str = "cheie-de-dezvoltare-schimba-o"
    # Adrese separate prin virgulă; implicit, serverul de dezvoltare Vite.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def database_file(self) -> Path:
        path = self.database_path
        return path if path.is_absolute() else BACKEND_DIR / path

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
