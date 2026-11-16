from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..dependencies import CurrentUserDep, SessionDep
from ..models import Favorite, Interaction, Product
from ..schemas import (
    EventOut,
    HistoryOut,
    InteractionIn,
    InteractionRecorded,
    ProductOut,
    ProductRef,
    PurchaseOut,
)
from ..vocabulary import EventType
from .products import PRODUCT_NOT_FOUND

router = APIRouter(tags=["interacțiuni"])

NOT_AVAILABLE = "Produsul nu este disponibil."
ALREADY_PURCHASED = "Ai cumpărat deja acest produs."
HISTORY_EVENTS_LIMIT = 50


def _already_recorded(session: Session, event_id: str) -> bool:
    return session.exec(select(Interaction.id).where(Interaction.event_id == event_id)).first() is not None


def _has_purchased(session: Session, user_id: int, product_id: int) -> bool:
    query = select(Interaction.id).where(
        Interaction.user_id == user_id,
        Interaction.product_id == product_id,
        Interaction.type == EventType.PURCHASE.value,
    )
    return session.exec(query).first() is not None


@router.post("/interactions", status_code=status.HTTP_201_CREATED)
def record_interaction(
    data: InteractionIn, user: CurrentUserDep, session: SessionDep, response: Response
) -> InteractionRecorded:
    """Salvează o vizualizare, un favorit, o scoatere din favorite sau o cumpărare simulată.

    Retrimiterea aceluiași `event_id` răspunde cu 200 și `recorded: false`, fără să-l salveze din nou.
    """
    duplicate = InteractionRecorded(event_id=data.event_id, recorded=False)
    # Verificăm duplicatul primul: o retrimitere trebuie să reușească chiar dacă produsul s-a schimbat între timp.
    if _already_recorded(session, data.event_id):
        response.status_code = status.HTTP_200_OK
        return duplicate

    product = session.get(Product, data.product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=PRODUCT_NOT_FOUND)
    if data.type == EventType.PURCHASE:
        if not product.available:
            raise HTTPException(status.HTTP_409_CONFLICT, detail=NOT_AVAILABLE)
        if _has_purchased(session, user.id, product.id):
            raise HTTPException(status.HTTP_409_CONFLICT, detail=ALREADY_PURCHASED)

    # Evenimentul și lista de favorite se schimbă în aceeași tranzacție.
    session.add(Interaction(event_id=data.event_id, user_id=user.id, product_id=product.id, type=data.type.value))
    favorite = session.get(Favorite, (user.id, product.id))
    if data.type == EventType.FAVORITE and favorite is None:
        session.add(Favorite(user_id=user.id, product_id=product.id))
    elif data.type == EventType.UNFAVORITE and favorite is not None:
        session.delete(favorite)
    try:
        session.commit()
    except IntegrityError:  # același event_id salvat între timp de o cerere paralelă
        session.rollback()
        if not _already_recorded(session, data.event_id):
            raise
        response.status_code = status.HTTP_200_OK
        return duplicate
    return InteractionRecorded(event_id=data.event_id, recorded=True)


@router.get("/me/history")
def get_history(user: CurrentUserDep, session: SessionDep) -> HistoryOut:
    """Favoritele, cumpărăturile și ultimele evenimente ale utilizatorului autentificat, cele mai noi primele."""
    favorites = session.exec(
        select(Product)
        .join(Favorite, Favorite.product_id == Product.id)
        .where(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc(), Product.id.desc())
    ).all()

    purchases = session.exec(
        select(Interaction, Product)
        .join(Product, Interaction.product_id == Product.id)
        .where(Interaction.user_id == user.id, Interaction.type == EventType.PURCHASE.value)
        .order_by(Interaction.created_at.desc(), Interaction.id.desc())
    ).all()

    events = session.exec(
        select(Interaction, Product)
        .join(Product, Interaction.product_id == Product.id)
        .where(Interaction.user_id == user.id)
        .order_by(Interaction.created_at.desc(), Interaction.id.desc())
        .limit(HISTORY_EVENTS_LIMIT)
    ).all()

    return HistoryOut(
        favorites=[ProductOut.model_validate(p, from_attributes=True) for p in favorites],
        purchases=[
            PurchaseOut(product=ProductOut.model_validate(p, from_attributes=True), purchased_at=i.created_at)
            for i, p in purchases
        ],
        events=[
            EventOut(event_id=i.event_id, type=i.type, product=ProductRef(id=p.id, name=p.name), created_at=i.created_at)
            for i, p in events
        ],
    )
