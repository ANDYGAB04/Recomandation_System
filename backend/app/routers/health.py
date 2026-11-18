from fastapi import APIRouter
from sqlalchemy import text

from ..dependencies import SessionDep

router = APIRouter(tags=["sistem"])


@router.get("/health")
def health(session: SessionDep) -> dict[str, str]:
    session.exec(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
