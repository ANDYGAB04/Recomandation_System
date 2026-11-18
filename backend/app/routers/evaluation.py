from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import func
from sqlmodel import select

from ..dependencies import SessionDep
from ..evaluation import load_and_run
from ..models import Interaction, Product, RecommendationFeedback, User
from ..schemas import EvaluationOut, FeedbackCounts, FeedbackGroups, FeedbackSummary
from ..seed import DEMO_ACCOUNTS, is_simulated_email

router = APIRouter(tags=["evaluare"])

NO_DATA = "Nu există date de evaluat. Rulează `python -m app.seed` în directorul backend/."


@router.get("/evaluation")
def get_evaluation(request: Request, session: SessionDep) -> EvaluationOut:
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


DEMO_EMAILS = {account.email for account in DEMO_ACCOUNTS}


def _counts(votes: list[bool]) -> FeedbackCounts:
    useful = sum(votes)
    return FeedbackCounts(votes=len(votes), useful=useful, useful_share=round(useful / len(votes), 4) if votes else None)


@router.get("/evaluation/feedback")
def get_feedback_summary(session: SessionDep) -> FeedbackSummary:
    rows = list(session.exec(select(RecommendationFeedback, User.email).join(User, User.id == RecommendationFeedback.user_id)))
    real = [f for f, email in rows if email not in DEMO_EMAILS and not is_simulated_email(email)]
    test = [f for f, email in rows if is_simulated_email(email)]
    return FeedbackSummary(**_groups(real).model_dump(), test_data=_groups(test))


def _groups(votes: list[RecommendationFeedback]) -> FeedbackGroups:
    return FeedbackGroups(
        **_counts([f.useful for f in votes]).model_dump(),
        users=len({f.user_id for f in votes}),
        personalized=_counts([f.useful for f in votes if f.strategy == "personalized"]),
        popular=_counts([f.useful for f in votes if f.strategy == "popular"]),
    )
