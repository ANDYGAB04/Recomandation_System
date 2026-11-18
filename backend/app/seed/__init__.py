
from dataclasses import dataclass

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, select

from ..db import init_db
from ..models import Product
from .catalog import CATALOG_SEED, build_catalog
from .demo import DEMO_ACCOUNTS, seed_demo_accounts
from .feedback_test_data import seed_feedback_test_data
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
    test_survey_responses_created: int = 0
    test_votes_created: int = 0


def seed_all(
    session: Session, customers: int = SIMULATED_CUSTOMERS, simulation_seed: int = SIMULATION_SEED
) -> SeedSummary:
    created, updated = seed_catalog(session)
    demo = seed_demo_accounts(session)
    simulated = seed_simulated_customers(session, customers, simulation_seed)
    survey_responses, votes = seed_feedback_test_data(session)
    return SeedSummary(created, updated, demo, simulated, survey_responses, votes)


def reset_database(engine: Engine) -> None:
    from .. import models  

    SQLModel.metadata.drop_all(engine)
    init_db(engine)
