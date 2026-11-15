import unicodedata
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from ..dependencies import SessionDep
from ..models import Product
from ..schemas import ProductOut, ProductPage
from ..vocabulary import Activity

router = APIRouter(prefix="/products", tags=["catalog"])

PRODUCT_NOT_FOUND = "Produsul nu există."


def normalize(text: str) -> str:
    """Litere mici, fără diacritice: „Ușor” și „usor” se potrivesc."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def matches(product: Product, terms: list[str]) -> bool:
    haystack = normalize(" ".join([product.name, product.description, *product.tags]))
    return all(term in haystack for term in terms)


@router.get("")
def list_products(
    session: SessionDep,
    category: Activity | None = None,
    q: Annotated[str | None, Query(max_length=100, description="Caută în nume, descriere și etichete")] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    available_only: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 24,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProductPage:
    """Catalogul, ordonat după id. Filtrele se pot combina."""
    query = select(Product).order_by(Product.id)
    if category is not None:
        query = query.where(Product.category == category.value)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    if available_only:
        query = query.where(Product.available)
    products = list(session.exec(query))

    # Căutarea text se face în Python: SQLite nu ignoră diacriticele, iar etichetele sunt JSON.
    # Catalogul are ~130 de produse, deci costul e neglijabil.
    terms = normalize(q).split() if q else []
    if terms:
        products = [p for p in products if matches(p, terms)]

    page = products[offset : offset + limit]
    return ProductPage(
        items=[ProductOut.model_validate(p, from_attributes=True) for p in page],
        total=len(products),
        limit=limit,
        offset=offset,
    )


@router.get("/{product_id}")
def get_product(product_id: int, session: SessionDep) -> ProductOut:
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=PRODUCT_NOT_FOUND)
    return ProductOut.model_validate(product, from_attributes=True)
