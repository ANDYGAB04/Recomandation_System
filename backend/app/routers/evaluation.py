from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func
from sqlmodel import select

from ..dependencies import SessionDep
from ..evaluation import load_and_run
from ..models import Interaction, Product
from ..schemas import EvaluationOut

router = APIRouter(tags=["evaluare"])

NO_DATA = "Nu există date de evaluat. Rulează `python -m app.seed` în directorul backend/."


@router.get("/evaluation")
def get_evaluation(request: Request, session: SessionDep) -> EvaluationOut:
    """Popularitate vs. recomandarea bazată pe profil, pe istoricul clienților simulați (date sintetice).

    Rezultatul se calculează o dată și se refolosește cât timp produsele și interacțiunile nu se schimbă.
    """
    key = (
        session.exec(select(func.count(Interaction.id), func.max(Interaction.id))).one(),
        session.exec(select(func.count(Product.id), func.sum(Product.price), func.sum(Product.available))).one(),
    )
    state = request.app.state
    if getattr(state, "evaluation_key", None) != key:
        try:
            state.evaluation = EvaluationOut.model_validate(load_and_run(session))
        except ValueError:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=NO_DATA) from None
        state.evaluation_key = key
    return state.evaluation
