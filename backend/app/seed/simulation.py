"""Clienți simulați: setări de profil și istoric pe 90 de zile, generate cu seed fix.

Servesc pentru popularitate (rezerva motorului) și pentru evaluarea offline. Fiecare client
are preferințe ascunse (activități, stiluri, nivel, sezon, buget). Setările lui de profil sunt
apropiate de ele, iar produsele pe care le vede, le salvează și le cumpără depind de cât de
bine se potrivesc cu ele, plus o popularitate de bază a fiecărui produs.

Rezultatele obținute pe aceste date descriu comportamentul simulatorului, nu preferințe reale.
"""

import secrets
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import timedelta

import numpy as np
from sqlmodel import Session, select

from ..models import Favorite, Interaction, Product, User, UserProfile
from ..security import hash_password
from ..vocabulary import Activity, EventType, Intensity, Level, Season, Style
from .timeline import SIMULATION_DAYS, SIMULATION_START, final_favorites

SIMULATION_SEED = 20261116
SIMULATED_CUSTOMERS = 300
# Clienții simulați se recunosc după domeniul e-mailului (de exemplu la evaluare).
SIMULATED_EMAIL_DOMAIN = "simulat.example.com"

ACTIVITIES = [a.value for a in Activity]
STYLES = [s.value for s in Style]
LEVELS = [lv.value for lv in Level]
SEASONS = [s.value for s in Season]
BUDGETS = [300.0, 600.0, 1200.0, None]


def simulated_email(number: int) -> str:
    return f"client{number:03d}@{SIMULATED_EMAIL_DOMAIN}"


def is_simulated_email(email: str) -> bool:
    return email.endswith("@" + SIMULATED_EMAIL_DOMAIN)


@dataclass
class Taste:
    primary: str
    secondary: str | None
    styles: list[str]
    level: str
    season: str
    budget: float | None


@dataclass
class SimulatedCustomer:
    number: int
    taste: Taste
    profile: dict
    # (moment, id produs, tip eveniment), în ordine cronologică
    events: list[tuple]


def _random_taste(rng: np.random.Generator) -> Taste:
    primary = str(rng.choice(ACTIVITIES))
    secondary = str(rng.choice([a for a in ACTIVITIES if a != primary])) if rng.random() < 0.4 else None
    styles = [str(s) for s in rng.choice(STYLES, size=int(rng.integers(1, 3)), replace=False)]
    level = str(rng.choice(LEVELS, p=[0.4, 0.4, 0.2]))
    season = str(rng.choice(SEASONS, p=[0.45, 0.25, 0.30]))
    budget = BUDGETS[int(rng.choice(len(BUDGETS), p=[0.25, 0.35, 0.25, 0.15]))]
    return Taste(primary, secondary, styles, level, season, budget)


def _declared_profile(taste: Taste, rng: np.random.Generator) -> dict:
    """Setările pe care clientul le-ar completa: apropiate de preferințele ascunse, uneori incomplete."""
    if rng.random() < 0.1:  # unii clienți nu își completează deloc profilul
        return {"activities": {}, "level": None, "styles": [], "season": None, "max_budget": None}
    activities = {taste.primary: Intensity.HIGH.value}
    if taste.secondary:
        activities[taste.secondary] = Intensity.LOW.value
    return {
        "activities": activities,
        "level": taste.level if rng.random() < 0.8 else None,
        "styles": taste.styles if rng.random() < 0.8 else [],
        "season": taste.season if rng.random() < 0.7 else None,
        "max_budget": taste.budget if rng.random() < 0.7 else None,
    }


def _affinity(taste: Taste, products: Sequence[Product], base_popularity: np.ndarray) -> np.ndarray:
    level_index = LEVELS.index(taste.level)
    values = []
    for product, base in zip(products, base_popularity):
        score = 0.0
        if taste.primary in product.usages:
            score += 2.0 + (0.5 if product.category == taste.primary else 0.0)
        if taste.secondary and taste.secondary in product.usages:
            score += 1.0
        score += 0.8 * len(set(taste.styles) & set(product.styles))
        if product.levels:
            distance = min(abs(LEVELS.index(lv) - level_index) for lv in product.levels)
            score += {0: 0.6, 1: 0.3}.get(distance, -0.3)
        if taste.season in product.seasons or Season.ALL_YEAR.value in product.seasons:
            score += 0.6
        if taste.budget is not None and product.price > taste.budget:
            score -= 1.5
        values.append(score + base)
    return np.array(values)


def simulate_customers(
    products: Sequence[Product], count: int = SIMULATED_CUSTOMERS, seed: int = SIMULATION_SEED
) -> list[SimulatedCustomer]:
    """Generează clienții; aceleași produse și același seed dau mereu aceleași date."""
    rng = np.random.default_rng(seed)
    base_popularity = rng.normal(0.0, 0.5, len(products))
    available = np.array([p.available for p in products])
    customers = []
    for number in range(1, count + 1):
        taste = _random_taste(rng)
        profile = _declared_profile(taste, rng)
        affinity = _affinity(taste, products, base_popularity)
        p_view = np.exp(affinity / 0.7)
        p_view /= p_view.sum()
        p_action = 1.0 / (1.0 + np.exp(-(affinity - 3.0)))

        events: list[tuple] = []
        favorites: set[int] = set()
        bought: set[int] = set()
        for day in np.sort(rng.uniform(0, SIMULATION_DAYS, 1 + rng.poisson(4))):
            moment = SIMULATION_START + timedelta(days=float(day))
            for index in rng.choice(len(products), size=1 + rng.poisson(2), p=p_view):
                product_id = products[index].id
                moment += timedelta(seconds=int(rng.integers(20, 300)))
                events.append((moment, product_id, EventType.VIEW.value))
                if available[index] and product_id not in bought and rng.random() < 0.45 * p_action[index]:
                    bought.add(product_id)
                    moment += timedelta(seconds=30)
                    events.append((moment, product_id, EventType.PURCHASE.value))
                elif product_id not in favorites and rng.random() < 0.35 * p_action[index]:
                    favorites.add(product_id)
                    moment += timedelta(seconds=10)
                    events.append((moment, product_id, EventType.FAVORITE.value))
            if favorites and rng.random() < 0.1:
                product_id = sorted(favorites)[int(rng.integers(len(favorites)))]
                favorites.discard(product_id)
                moment += timedelta(seconds=15)
                events.append((moment, product_id, EventType.UNFAVORITE.value))
        customers.append(SimulatedCustomer(number, taste, profile, events))
    return customers


def seed_simulated_customers(
    session: Session, count: int = SIMULATED_CUSTOMERS, seed: int = SIMULATION_SEED
) -> int:
    """Adaugă clienții simulați dacă nu există deja niciunul. Întoarce câți au fost creați."""
    existing = session.exec(select(User).where(User.email.like(f"%@{SIMULATED_EMAIL_DOMAIN}"))).first()
    if existing is not None:
        return 0
    products = list(session.exec(select(Product).order_by(Product.id)))
    # Clienții simulați nu se autentifică: toți primesc hash-ul unei parole aleatoare, necunoscute.
    unusable_hash = hash_password(secrets.token_urlsafe(32))
    for customer in simulate_customers(products, count, seed):
        user = User(
            email=simulated_email(customer.number),
            password_hash=unusable_hash,
            display_name=f"Client simulat {customer.number:03d}",
            created_at=SIMULATION_START,
        )
        session.add(user)
        session.flush()
        session.add(UserProfile(user_id=user.id, updated_at=SIMULATION_START, **customer.profile))
        interactions = [
            Interaction(event_id=f"seed-sim-{customer.number:03d}-{n:04d}", user_id=user.id,
                        product_id=product_id, type=event_type, created_at=moment)
            for n, (moment, product_id, event_type) in enumerate(customer.events)
        ]
        session.add_all(interactions)
        session.add_all(
            Favorite(user_id=user.id, product_id=pid, created_at=at) for pid, at in final_favorites(interactions).items()
        )
    session.commit()
    return count
