
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlmodel import Session, select

from ..models import Favorite, Interaction, Product, User, UserProfile
from ..security import hash_password
from ..vocabulary import EventType
from .timeline import SIMULATION_END, final_favorites

E = EventType


@dataclass(frozen=True)
class DemoAccount:
    email: str
    password: str
    display_name: str
    activities: dict[str, str]
    level: str
    styles: list[str]
    season: str
    max_budget: float | None
    history: list[tuple[int, str, str]] = field(default_factory=list)


DEMO_ACCOUNTS = (
    DemoAccount(
        email="maria@example.com",
        password="maria2026",
        display_name="Maria",
        activities={"running": "high"},
        level="beginner",
        styles=["budget"],
        season="summer",
        max_budget=300,
        history=[
            (6, "Pantofi de alergare pe șosea Ritm Start", E.VIEW),
            (6, "Pantofi de alergare pe șosea Ritm Start", E.VIEW),
            (5, "Pantofi de alergare pe șosea Ritm Start", E.PURCHASE),
            (4, "Tricou tehnic de alergare Ritm Start", E.VIEW),
            (4, "Tricou tehnic de alergare Ritm Start", E.FAVORITE),
            (2, "Centură de alergare Ritm Start", E.VIEW),
        ],
    ),
    DemoAccount(
        email="radu@example.com",
        password="radu2026",
        display_name="Radu",
        activities={"camping": "high", "hiking": "high"},
        level="advanced",
        styles=["durable"],
        season="winter",
        max_budget=5000,
        history=[
            (7, "Cort 4 anotimpuri Bivuac Pro", E.VIEW),
            (6, "Cort 4 anotimpuri Bivuac Pro", E.PURCHASE),
            (5, "Sac de dormit de iarnă Bivuac Pro", E.VIEW),
            (5, "Sac de dormit de iarnă Bivuac Pro", E.FAVORITE),
            (3, "Bocanci de iarnă Carpatia Pro", E.VIEW),
            (1, "Colțari de drumeție Carpatia Pro", E.VIEW),
        ],
    ),
)

DEMO_CREATED_AT = SIMULATION_END - timedelta(days=30)


def seed_demo_accounts(session: Session) -> int:
    products = {p.name: p for p in session.exec(select(Product))}
    created = 0
    for account in DEMO_ACCOUNTS:
        if session.exec(select(User).where(User.email == account.email)).first():
            continue
        user = User(
            email=account.email,
            password_hash=hash_password(account.password),
            display_name=account.display_name,
            created_at=DEMO_CREATED_AT,
        )
        session.add(user)
        session.flush()
        session.add(UserProfile(
            user_id=user.id,
            activities=account.activities,
            level=account.level,
            styles=account.styles,
            season=account.season,
            max_budget=account.max_budget,
            updated_at=DEMO_CREATED_AT,
        ))
        events = []
        for n, (days_before_end, product_name, event_type) in enumerate(account.history):
            moment: datetime = SIMULATION_END - timedelta(days=days_before_end) + timedelta(minutes=n)
            events.append(Interaction(
                event_id=f"seed-demo-{user.id}-{n}",
                user_id=user.id,
                product_id=products[product_name].id,
                type=event_type,
                created_at=moment,
            ))
        session.add_all(events)
        session.add_all(Favorite(user_id=user.id, product_id=pid, created_at=at) for pid, at in final_favorites(events).items())
        created += 1
    session.commit()
    return created
