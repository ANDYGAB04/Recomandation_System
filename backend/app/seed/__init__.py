"""Scriptul de inițializare a datelor de test.

    python -m app.seed          # din directorul backend/

Pasul 08 încarcă doar catalogul; conturile demonstrative și clienții simulați vin la pasul 12.
"""

from sqlmodel import Session, select

from ..models import Product
from .catalog import CATALOG_SEED, build_catalog


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
