"""Recomandările finale: profilul combinat, excluderile, rezerva pe popularitate și explicațiile.

    profil(u) = normalizează(α × profil_declarat(u) + (1 − α) × profil_comportament(u))

Dacă una dintre cele două părți lipsește, profilul este cealaltă. Dacă lipsesc amândouă
(setări necompletate și niciun istoric), recomandăm cele mai cumpărate produse și spunem asta.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

import numpy as np

from ..vocabulary import LABELS, Activity, EventType, Level, Season, Style
from .behavior import History
from .engine import ContentRecommender
from .features import DeclaredProfileLike, declared_choices, split_feature

# Ponderea datelor declarate în profilul combinat; restul vine din comportament.
ALPHA = 0.5

PERSONALIZED = "personalized"
POPULAR = "popular"
NO_PROFILE_REASON = "Completează setările de profil pentru recomandări personalizate."
NO_MATCH_REASON = "Niciun produs disponibil nu se potrivește profilului și bugetului tău."

# Grupul de caracteristici → grupul din GET /vocabulary (categoria și utilizările sunt amândouă activități).
VOCABULARY_GROUPS = {
    "category": ("activities", Activity),
    "usage": ("activities", Activity),
    "style": ("styles", Style),
    "level": ("levels", Level),
    "season": ("seasons", Season),
}

HISTORY_SOURCES = {
    EventType.PURCHASE: "din cumpărăturile tale",
    EventType.FAVORITE: "din favoritele tale",
    EventType.VIEW: "dintre produsele pe care le-ai văzut",
}


@dataclass(frozen=True)
class Match:
    """O preferință care a contribuit la scor, de exemplu („activities”, „running”)."""

    group: str
    value: str

    @property
    def label(self) -> str:
        enum = next(e for g, e in VOCABULARY_GROUPS.values() if g == self.group)
        return LABELS[enum][self.value]


@dataclass(frozen=True)
class Explanation:
    text: str
    matched: list[Match]
    because_of: list[int]


@dataclass(frozen=True)
class Recommendation:
    product_id: int
    score: float
    explanation: Explanation


@dataclass(frozen=True)
class RecommendationList:
    strategy: str
    fallback_reason: str | None
    items: list[Recommendation]


def combine_profiles(
    declared: np.ndarray | None, behavior: np.ndarray | None, alpha: float = ALPHA
) -> np.ndarray | None:
    if declared is None:
        return behavior
    if behavior is None:
        return declared
    vector = alpha * declared + (1 - alpha) * behavior
    norm = np.linalg.norm(vector)
    return vector / norm if norm > 0 else None


def recommend(
    rec: ContentRecommender,
    profile: DeclaredProfileLike | None,
    history: History,
    purchase_counts: Mapping[int, int],
    k: int = 10,
    exclude: Iterable[int] = (),
    alpha: float = ALPHA,
) -> RecommendationList:
    """Recomandările pentru un utilizator. Produsele cumpărate nu se recomandă niciodată."""
    excluded = set(exclude) | history.purchased
    max_price = profile.max_budget if profile is not None else None
    declared = rec.declared_profile(profile) if profile is not None else None
    weights = history.product_weights()
    vector = combine_profiles(declared, rec.behavior_profile(weights), alpha)
    if vector is None:
        return popular(rec, purchase_counts, k, excluded, max_price, NO_PROFILE_REASON)

    ranked = rec.rank(vector, k, excluded, max_price)
    if not ranked:
        return popular(rec, purchase_counts, k, excluded, max_price, NO_MATCH_REASON)
    choices = declared_choices(profile) if declared is not None else set()
    items = [
        Recommendation(item.product_id, item.score, _explain(rec, declared, choices, weights, history, item.product_id))
        for item in ranked
    ]
    return RecommendationList(PERSONALIZED, None, items)


def popular(
    rec: ContentRecommender,
    purchase_counts: Mapping[int, int],
    k: int = 10,
    exclude: Iterable[int] = (),
    max_price: float | None = None,
    reason: str | None = NO_PROFILE_REASON,
) -> RecommendationList:
    """Rezerva: produsele disponibile cu cei mai mulți cumpărători distincți."""
    excluded = set(exclude)
    candidates = [
        p for p in rec.products
        if p.available and p.id not in excluded and (max_price is None or p.price <= max_price)
    ]
    candidates.sort(key=lambda p: (-purchase_counts.get(p.id, 0), p.id))
    items = [
        Recommendation(p.id, float(purchase_counts.get(p.id, 0)), Explanation(_popular_text(purchase_counts.get(p.id, 0)), [], []))
        for p in candidates[:k]
    ]
    return RecommendationList(POPULAR, reason, items)


def similar(rec: ContentRecommender, product_id: int, k: int = 4, exclude: Iterable[int] = ()) -> list[Recommendation]:
    """Produsele cele mai asemănătoare cu `product_id` (fără el însuși și fără cele excluse)."""
    vector = rec.product_vector(product_id)
    ranked = rec.rank(vector, k, set(exclude) | {product_id})
    items = []
    for item in ranked:
        common = _matched(rec, vector, rec.product_vector(item.product_id))
        text = "Caracteristici comune: " + _join(common) + "." if common else "Descriere asemănătoare."
        items.append(Recommendation(item.product_id, item.score, Explanation(text, common, [product_id])))
    return items


def _matched(
    rec: ContentRecommender,
    reference: np.ndarray,
    product: np.ndarray,
    allowed: set[str] | None = None,
    top: int = 3,
) -> list[Match]:
    """Preferințele prezente atât în `reference`, cât și în produs, ordonate după contribuția la scor.

    Cu `allowed`, doar caracteristicile din acea mulțime (de exemplu, cele alese explicit în setări).
    """
    n = rec.n_preference_features
    contributions = reference[:n] * product[:n]
    if allowed is not None:
        contributions = contributions * np.array([name in allowed for name in rec.feature_names[:n]])
    matches: list[Match] = []
    for index in np.argsort(-contributions, kind="stable"):
        if contributions[index] <= 0 or len(matches) == top:
            break
        group, value = split_feature(rec.feature_names[index])
        match = Match(VOCABULARY_GROUPS[group][0], value)
        if match not in matches:
            matches.append(match)
    return matches


def _explain(
    rec: ContentRecommender,
    declared: np.ndarray | None,
    choices: set[str],
    weights: Mapping[int, float],
    history: History,
    product_id: int,
) -> Explanation:
    product = rec.product_vector(product_id)
    # „Ai ales” se referă doar la ce a ales utilizatorul în setări și se regăsește în produs.
    matched = _matched(rec, declared, product, choices) if declared is not None else []
    influences = sorted(
        ((w * rec.similarity(product_id, pid), pid) for pid, w in weights.items() if pid != product_id and pid in rec.row),
        key=lambda item: (-item[0], item[1]),
    )
    because_of = [pid for score, pid in influences if score > 0][:2]

    parts = []
    if product_id in history.favorites:
        parts.append("este în favoritele tale")
    if matched:
        parts.append("pentru că ai ales " + _join(matched))
    if because_of:
        first = because_of[0]
        parts.append(f"seamănă cu „{rec.by_id[first].name}”, {HISTORY_SOURCES[history.strongest_event(first)]}")
    text = "; ".join(parts) + "." if parts else "se potrivește cu profilul tău."
    return Explanation(text[0].upper() + text[1:], matched, because_of)


def _join(matches: list[Match]) -> str:
    labels = [m.label[0].lower() + m.label[1:] for m in matches]
    return labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " și " + labels[-1]


def _popular_text(count: int) -> str:
    if count == 0:
        return "Produs disponibil în catalog."
    # „1 client”, „5 clienți”, „20 de clienți”
    noun = "client" if count == 1 else ("de clienți" if count % 100 == 0 or count % 100 >= 20 else "clienți")
    return f"Printre cele mai cumpărate: {count} {noun}."


@dataclass(frozen=True)
class ProfileSummary:
    """Pe ce date se bazează recomandările unui utilizator (pagina „Profilul meu de recomandare”)."""

    declared_share: float
    behavior_share: float
    # (preferință, pondere); ponderile tuturor preferințelor din profil însumează 1
    interests: list[tuple[Match, float]]
    # (id produs, pondere în profilul din comportament, tipurile de evenimente)
    top_products: list[tuple[int, float, list[str]]]


def profile_summary(
    rec: ContentRecommender,
    profile: DeclaredProfileLike | None,
    history: History,
    alpha: float = ALPHA,
    top_interests: int = 8,
    top_products: int = 5,
) -> ProfileSummary:
    declared = rec.declared_profile(profile) if profile is not None else None
    weights = history.product_weights()
    behavior = rec.behavior_profile(weights)
    if declared is not None and behavior is not None:
        shares = (alpha, 1 - alpha)
    else:
        shares = (float(declared is not None), float(behavior is not None))

    interests: list[tuple[Match, float]] = []
    vector = combine_profiles(declared, behavior, alpha)
    if vector is not None:
        totals: dict[Match, float] = {}
        for index in np.flatnonzero(vector[: rec.n_preference_features] > 0):
            group, value = split_feature(rec.feature_names[index])
            match = Match(VOCABULARY_GROUPS[group][0], value)
            totals[match] = totals.get(match, 0.0) + float(vector[index])
        total = sum(totals.values())
        ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0].group, item[0].value))
        interests = [(match, weight / total) for match, weight in ranked[:top_interests]]

    products = sorted(weights.items(), key=lambda item: (-item[1], item[0]))[:top_products]
    events = {
        EventType.PURCHASE: history.purchases,
        EventType.FAVORITE: history.favorites,
        EventType.VIEW: history.views,
    }
    summary_products = [
        (pid, weight, [event.value for event, products_with_event in events.items() if pid in products_with_event])
        for pid, weight in products
    ]
    return ProfileSummary(shares[0], shares[1], interests, summary_products)
