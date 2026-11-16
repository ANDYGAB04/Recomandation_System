from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status

from ..dependencies import CurrentUserDep, OptionalUserDep, SessionDep
from ..recommendation_service import get_recommender, load_history, load_profile, purchase_counts
from ..recommender import ContentRecommender, Recommendation, profile_summary, recommend, similar
from ..schemas import (
    ExplanationOut,
    InterestOut,
    MatchOut,
    ProductOut,
    ProductRef,
    ProfileProductOut,
    ProfileSources,
    RecommendationOut,
    RecommendationProfileOut,
    RecommendationsOut,
    SimilarOut,
)
from .products import PRODUCT_NOT_FOUND

router = APIRouter(tags=["recomandări"])


def _product_ref(rec: ContentRecommender, product_id: int) -> ProductRef:
    return ProductRef(id=product_id, name=rec.by_id[product_id].name)


def _to_out(rec: ContentRecommender, item: Recommendation) -> RecommendationOut:
    explanation = item.explanation
    return RecommendationOut(
        product=ProductOut.model_validate(rec.by_id[item.product_id], from_attributes=True),
        score=round(item.score, 4),
        explanation=ExplanationOut(
            text=explanation.text,
            matched=[MatchOut(group=m.group, value=m.value, label=m.label) for m in explanation.matched],
            because_of=[_product_ref(rec, pid) for pid in explanation.because_of],
        ),
    )


@router.get("/recommendations")
def get_recommendations(
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
    k: Annotated[int, Query(ge=1, le=50, description="Câte recomandări")] = 10,
    exclude: Annotated[list[int] | None, Query(description="Produse de exclus, de exemplu cel deschis în pagină")] = None,
) -> RecommendationsOut:
    """Recomandările personalizate, cu explicații; fără setări și fără istoric, cele mai cumpărate produse."""
    rec = get_recommender(session, request.app.state)
    result = recommend(
        rec,
        load_profile(session, user.id),
        load_history(session, user.id),
        purchase_counts(session),
        k=k,
        exclude=exclude or (),
    )
    return RecommendationsOut(
        strategy=result.strategy,
        fallback_reason=result.fallback_reason,
        items=[_to_out(rec, item) for item in result.items],
    )


@router.get("/recommendations/profile")
def get_recommendation_profile(request: Request, session: SessionDep, user: CurrentUserDep) -> RecommendationProfileOut:
    """Pe ce date se bazează recomandările: ponderea surselor, interesele dominante, produsele din istoric."""
    rec = get_recommender(session, request.app.state)
    summary = profile_summary(rec, load_profile(session, user.id), load_history(session, user.id))
    return RecommendationProfileOut(
        sources=ProfileSources(declared=summary.declared_share, behavior=summary.behavior_share),
        interests=[
            InterestOut(group=m.group, value=m.value, label=m.label, weight=round(weight, 4))
            for m, weight in summary.interests
        ],
        top_products=[
            ProfileProductOut(product=_product_ref(rec, pid), weight=weight, events=events)
            for pid, weight, events in summary.top_products
            if pid in rec.by_id
        ],
    )


@router.get("/products/{product_id}/similar", tags=["catalog"])
def get_similar_products(
    product_id: int,
    request: Request,
    session: SessionDep,
    user: OptionalUserDep,
    k: Annotated[int, Query(ge=1, le=20, description="Câte produse similare")] = 4,
) -> SimilarOut:
    """Produsele cele mai asemănătoare. Cu token, fără cele cumpărate deja de utilizator."""
    rec = get_recommender(session, request.app.state)
    if product_id not in rec.by_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=PRODUCT_NOT_FOUND)
    purchased = load_history(session, user.id).purchased if user is not None else set()
    return SimilarOut(items=[_to_out(rec, item) for item in similar(rec, product_id, k, purchased)])
