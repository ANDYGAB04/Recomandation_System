import pytest
from sqlmodel import Session

from app.models import Product
from app.seed import seed_catalog
from app.seed.catalog import build_catalog

PRODUCTS = [
    dict(name="Cort Ușor 2P", category="camping", usages=["camping", "hiking"], styles=["ultralight"],
         seasons=["summer"], levels=["advanced"], tags=["cort", "2 persoane"], description="Cort de vară.", price=900),
    dict(name="Pantofi Trail", category="running", usages=["running", "hiking"], styles=["performance"],
         seasons=["all_year"], levels=["intermediate"], tags=["pantofi"], description="Pentru poteci.", price=450),
    dict(name="Pantofi Șosea Start", category="running", usages=["running"], styles=["budget"],
         seasons=["summer"], levels=["beginner"], tags=["pantofi"], description="Pentru asfalt.", price=199.99),
    dict(name="Pantofi Șosea Vechi", category="running", usages=["running"], styles=["budget"],
         seasons=["summer"], levels=["beginner"], tags=["pantofi"], description="Stoc epuizat.", price=150,
         available=False),
    dict(name="Cască Oraș", category="cycling", usages=["cycling"], styles=["comfort"],
         seasons=["all_year"], levels=["beginner"], tags=["cască", "siguranță"], description="Cască urbană.", price=250),
]


@pytest.fixture
def catalog(client):
    with Session(client.app.state.engine) as session:
        for data in PRODUCTS:
            session.add(Product(**data))
        session.commit()
    return client


def names(response):
    assert response.status_code == 200, response.text
    return [p["name"] for p in response.json()["items"]]


def test_list_all_ordered_by_id_with_page_info(catalog):
    response = catalog.get("/products")
    assert names(response) == [p["name"] for p in PRODUCTS]
    body = response.json()
    assert (body["total"], body["limit"], body["offset"]) == (5, 24, 0)
    first = body["items"][0]
    assert first["id"] == 1
    assert first["usages"] == ["camping", "hiking"]
    assert first["available"] is True and first["is_test_data"] is True


def test_filter_by_category(catalog):
    assert names(catalog.get("/products", params={"category": "running"})) == [
        "Pantofi Trail", "Pantofi Șosea Start", "Pantofi Șosea Vechi"]


def test_unknown_category_is_422(catalog):
    assert catalog.get("/products", params={"category": "inot"}).status_code == 422


def test_filter_by_max_price_is_inclusive(catalog):
    assert names(catalog.get("/products", params={"max_price": 250})) == [
        "Pantofi Șosea Start", "Pantofi Șosea Vechi", "Cască Oraș"]


def test_filter_available_only(catalog):
    assert "Pantofi Șosea Vechi" not in names(catalog.get("/products", params={"available_only": True}))


@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("cort", ["Cort Ușor 2P"]),             
        ("POTECI", ["Pantofi Trail"]),          
        ("siguranță", ["Cască Oraș"]),          
        ("siguranta", ["Cască Oraș"]),          
        ("pantofi sosea", ["Pantofi Șosea Start", "Pantofi Șosea Vechi"]),  
        ("inexistent", []),
    ],
)
def test_text_search(catalog, q, expected):
    assert names(catalog.get("/products", params={"q": q})) == expected


def test_filters_combine(catalog):
    params = {"category": "running", "q": "pantofi", "max_price": 300, "available_only": True}
    response = catalog.get("/products", params=params)
    assert names(response) == ["Pantofi Șosea Start"]
    assert response.json()["total"] == 1


def test_pagination(catalog):
    response = catalog.get("/products", params={"limit": 2, "offset": 2})
    assert names(response) == ["Pantofi Șosea Start", "Pantofi Șosea Vechi"]
    assert response.json()["total"] == 5


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"max_price": -5}])
def test_invalid_paging_or_price_is_422(catalog, params):
    assert catalog.get("/products", params=params).status_code == 422


def test_get_product(catalog):
    response = catalog.get("/products/2")
    assert response.status_code == 200
    assert response.json()["name"] == "Pantofi Trail"


def test_missing_product_is_404(catalog):
    response = catalog.get("/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produsul nu există."


def test_seeded_catalog_through_api(client):
    with Session(client.app.state.engine) as session:
        seed_catalog(session)
    body = client.get("/products", params={"category": "camping", "available_only": True, "limit": 100}).json()
    assert body["total"] > 0
    assert all(p["category"] == "camping" and p["available"] for p in body["items"])
    assert client.get("/products", params={"limit": 1}).json()["total"] == len(build_catalog())
