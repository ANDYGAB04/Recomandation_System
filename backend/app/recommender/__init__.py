"""Motorul de recomandare HobbyShop, independent de baza de date și de API.

Primește produse și profiluri ca obiecte cu atributele din `features.ProductLike` și
`features.DeclaredProfileLike`; modelele SQLModel `Product` și `UserProfile` le au deja.
"""

from .engine import ContentRecommender, ScoredProduct
from .features import declared_profile_features, product_preference_features

__all__ = ["ContentRecommender", "ScoredProduct", "declared_profile_features", "product_preference_features"]
