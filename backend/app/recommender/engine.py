"""Recomandare bazată pe conținut: vectorii produselor și scorul față de profilul declarat.

    vector(produs)       = normalizează([ preferințe × W_PREFERINȚE , text × W_TEXT ])
    profil_declarat(u)   = normalizează(preferințele din setări, ponderate)
    scor(u, produs)      = cosinus(profil_declarat(u), vector(produs))

Ambele blocuri ale vectorului de produs sunt normalizate separat. Profilul declarat are doar
partea de preferințe, așa că blocul de text nu schimbă ordinea produselor pentru el. Textul
(nume, etichete, descriere) contează la produsele similare și la profilul din comportament.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
from scipy import sparse
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from .features import (
    DeclaredProfileLike,
    ProductLike,
    declared_profile_features,
    product_preference_features,
    product_text,
)

PREFERENCE_WEIGHT = 1.0
TEXT_WEIGHT = 0.5

ROMANIAN_STOP_WORDS = [
    "a", "ai", "al", "ale", "cu", "care", "ce", "cei", "cel", "cele", "de", "din", "după", "fără",
    "in", "în", "la", "le", "mai", "pe", "pentru", "prin", "se", "și", "sau", "un", "una", "unei",
]


@dataclass(frozen=True)
class ScoredProduct:
    product_id: int
    score: float


class ContentRecommender:
    """Vectorii produselor din catalog; se construiesc o dată, la pornirea API-ului."""

    def __init__(self, products: Iterable[ProductLike]):
        self.products: list[ProductLike] = list(products)
        if not self.products:
            raise ValueError("Catalogul este gol: nu există produse pentru recomandări.")
        self.by_id = {p.id: p for p in self.products}
        self.row = {p.id: i for i, p in enumerate(self.products)}

        self.preference_vectorizer = DictVectorizer()
        preferences = normalize(
            self.preference_vectorizer.fit_transform([product_preference_features(p) for p in self.products])
        )
        self.text_vectorizer = TfidfVectorizer(stop_words=ROMANIAN_STOP_WORDS, token_pattern=r"(?u)\b\w\w+\b")
        text = self.text_vectorizer.fit_transform([product_text(p) for p in self.products])

        self.matrix = normalize(
            sparse.hstack([preferences * PREFERENCE_WEIGHT, text * TEXT_WEIGHT]).tocsr()
        )
        self.n_preference_features = preferences.shape[1]
        self.feature_names: list[str] = [
            *self.preference_vectorizer.get_feature_names_out(),
            *(f"text:{word}" for word in self.text_vectorizer.get_feature_names_out()),
        ]

    def declared_profile(self, profile: DeclaredProfileLike) -> np.ndarray | None:
        """Vectorul normalizat al preferințelor din setări; None dacă profilul nu are nicio preferință cunoscută."""
        features = declared_profile_features(profile)
        if not features:
            return None
        preferences = self.preference_vectorizer.transform([features]).toarray().ravel()
        vector = np.concatenate([preferences, np.zeros(self.matrix.shape[1] - self.n_preference_features)])
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else None

    def behavior_profile(self, weights: Mapping[int, float]) -> np.ndarray | None:
        """Suma ponderată a vectorilor produselor din istoric, normalizată; None fără istoric."""
        rows = [(self.row[pid], w) for pid, w in weights.items() if pid in self.row and w > 0]
        if not rows:
            return None
        indices, row_weights = zip(*rows)
        vector = np.asarray(self.matrix[list(indices)].T @ np.array(row_weights, dtype=float)).ravel()
        norm = np.linalg.norm(vector)
        return vector / norm if norm > 0 else None

    def product_vector(self, product_id: int) -> np.ndarray:
        return self.matrix[self.row[product_id]].toarray().ravel()

    def similarity(self, product_a: int, product_b: int) -> float:
        """Similaritatea cosinus dintre două produse."""
        return float(self.matrix[self.row[product_a]].multiply(self.matrix[self.row[product_b]]).sum())

    def scores(self, profile_vector: np.ndarray) -> np.ndarray:
        """Similaritatea cosinus dintre profil și fiecare produs (vectorii sunt deja normalizați)."""
        return np.asarray(self.matrix @ profile_vector).ravel()

    def rank(
        self,
        profile_vector: np.ndarray,
        k: int = 10,
        exclude: Iterable[int] = (),
        max_price: float | None = None,
    ) -> list[ScoredProduct]:
        """Primele k produse cu scor pozitiv, disponibile, sub buget și neexcluse."""
        excluded = set(exclude)
        ranked = [
            ScoredProduct(p.id, float(score))
            for p, score in zip(self.products, self.scores(profile_vector))
            if score > 1e-9
            and p.available
            and p.id not in excluded
            and (max_price is None or p.price <= max_price)
        ]
        ranked.sort(key=lambda item: (-item.score, item.product_id))
        return ranked[:k]

    def recommend_declared(
        self, profile: DeclaredProfileLike, k: int = 10, exclude: Sequence[int] = ()
    ) -> list[ScoredProduct]:
        """Recomandări doar din datele declarate; listă goală dacă profilul nu are preferințe."""
        vector = self.declared_profile(profile)
        if vector is None:
            return []
        return self.rank(vector, k, exclude, profile.max_budget)
