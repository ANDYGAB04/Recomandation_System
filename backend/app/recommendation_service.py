
import hashlib
import json
from types import SimpleNamespace

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select

from .models import Interaction, Product, UserProfile
from .recommender import ContentRecommender, History
from .vocabulary import EventType

EMPTY_CATALOG = "Catalogul este gol. Rulează `python -m app.seed` în directorul backend/."


def _catalog_key(products: list[Product]) -> str:
    data = json.dumps([p.model_dump() for p in products], sort_keys=True, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def get_recommender(session: Session, state) -> ContentRecommender:
    products = list(session.exec(select(Product).order_by(Product.id)))
    if not products:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=EMPTY_CATALOG)
    key = _catalog_key(products)
    if getattr(state, "recommender_key", None) != key:
        snapshot = [SimpleNamespace(**p.model_dump()) for p in products]
        state.recommender = ContentRecommender(snapshot)
        state.recommender_key = key
    return state.recommender


def purchase_counts(session: Session) -> dict[int, int]:
    query = (
        select(Interaction.product_id, func.count(func.distinct(Interaction.user_id)))
        .where(Interaction.type == EventType.PURCHASE.value)
        .group_by(Interaction.product_id)
    )
    return {product_id: count for product_id, count in session.exec(query)}


def load_history(session: Session, user_id: int) -> History:
    query = (
        select(Interaction)
        .where(Interaction.user_id == user_id)
        .order_by(Interaction.created_at, Interaction.id)
    )
    return History.from_interactions(session.exec(query))


def load_profile(session: Session, user_id: int) -> UserProfile | None:
    return session.get(UserProfile, user_id)
