"""Motorul de recomandare HobbyShop, independent de baza de date și de API.

Primește produse și profiluri ca obiecte cu atributele din `features.ProductLike` și
`features.DeclaredProfileLike`; modelele SQLModel `Product` și `UserProfile` le au deja.
Istoricul se construiește cu `History.from_interactions(...)` din modelele `Interaction`.
"""

from .behavior import EVENT_WEIGHTS, VIEW_CAP, History
from .engine import ContentRecommender, ScoredProduct
from .features import declared_profile_features, product_preference_features
from .recommend import (
    ALPHA,
    POPULAR,
    PERSONALIZED,
    Explanation,
    Match,
    Recommendation,
    RecommendationList,
    popular,
    recommend,
    similar,
)

__all__ = [
    "ALPHA",
    "EVENT_WEIGHTS",
    "PERSONALIZED",
    "POPULAR",
    "VIEW_CAP",
    "ContentRecommender",
    "Explanation",
    "History",
    "Match",
    "Recommendation",
    "RecommendationList",
    "ScoredProduct",
    "declared_profile_features",
    "popular",
    "product_preference_features",
    "recommend",
    "similar",
]
