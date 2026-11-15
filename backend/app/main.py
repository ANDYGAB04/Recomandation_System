"""Aplicația FastAPI HobbyShop.

    uvicorn app.main:app --reload        # documentația interactivă: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import Settings, get_settings
from .db import create_db_engine, init_db
from .routers import health, vocabulary


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = create_db_engine(settings.database_file)
        init_db(app.state.engine)
        yield
        app.state.engine.dispose()

    app = FastAPI(
        title="HobbyShop API",
        description="Sistem de recomandare bazat pe profilul utilizatorului. Toate datele sunt de test.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(vocabulary.router)
    return app


app = create_app()
