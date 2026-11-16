"""Scriptul de inițializare a datelor de test.

    python -m app.seed            # din directorul backend/: completează ce lipsește
    python -m app.seed --reset    # șterge toate datele și le recreează (de exemplu înainte de prezentare)

Încarcă catalogul, cele două conturi demonstrative (Maria și Radu) și clienții simulați.
"""

from dataclasses import dataclass

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, select

from ..db import init_db
from ..models import Product
from .catalog import CATALOG_SEED, build_catalog
from .demo import DEMO_ACCOUNTS, seed_demo_accounts
from .simulation import SIMULATED_CUSTOMERS, SIMULATION_SEED, is_simulated_email, seed_simulated_customers

__all__ = [
    "DEMO_ACCOUNTS",
    "SeedSummary",
    "is_simulated_email",
    "reset_database",
    "seed_all",
    "seed_catalog",
]


def seed_catalog(session: Session, seed: int = CATALOG_SEED) -> tuple[int, int]:
    """Încarcă sau actualizează catalogul (după nume). Întoarce (produse noi, produse actualizate).

    Rulat de mai multe ori, lasă aceleași date: produsele existente se suprascriu cu
    aceleași valori, iar id-urile lor nu se schimbă.
    """
    existing = {p.name: p for p in session.exec(select(Product))}
    created = updated = 0
    for data in build_catalog(seed):
        product = existing.get(data["name"])
        if product is None:
            session.add(Product(**data))
            created += 1
        else:
            for key, value in data.items():
                setattr(product, key, value)
            updated += 1
    session.commit()
    return created, updated


@dataclass(frozen=True)
class SeedSummary:
    products_created: int
    products_updated: int
    demo_accounts_created: int
    simulated_customers_created: int


def seed_all(
    session: Session, customers: int = SIMULATED_CUSTOMERS, simulation_seed: int = SIMULATION_SEED
) -> SeedSummary:
    """Completează datele de test care lipsesc; nu atinge conturile create de utilizatori."""
    created, updated = seed_catalog(session)
    demo = seed_demo_accounts(session)
    simulated = seed_simulated_customers(session, customers, simulation_seed)
    return SeedSummary(created, updated, demo, simulated)


def reset_database(engine: Engine) -> None:
    """Șterge toate tabelele (și datele) și le recreează goale."""
    from .. import models  # noqa: F401  (înregistrează modelele în SQLModel.metadata)

    SQLModel.metadata.drop_all(engine)
    init_db(engine)
