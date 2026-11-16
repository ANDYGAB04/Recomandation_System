import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import create_db_engine, init_db
from app.main import create_app
from app.models import Product
from app.seed import seed_all
from tests.helpers import auth_header, register_headers

MARIA = ("maria@example.com", "maria2026")
RADU = ("radu@example.com", "radu2026")


@pytest.fixture
def seeded(settings):
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        seed_all(session, customers=30)
    engine.dispose()
    return settings


@pytest.fixture
def api(seeded):
    with TestClient(create_app(seeded)) as client:
        yield client


def login(client, account):
    email, password = account
    return auth_header(client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"])


def recommendations(client, headers, **params):
    response = client.get("/recommendations", headers=headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()


def ids(result):
    return [item["product"]["id"] for item in result["items"]]


def event(client, headers, product_id, event_type):
    body = {"event_id": str(uuid.uuid4()), "product_id": product_id, "type": event_type}
    assert client.post("/interactions", json=body, headers=headers).status_code == 201


# ---- GET /recommendations ----

def test_recommendations_require_authentication(api):
    assert api.get("/recommendations").status_code == 401
    assert api.get("/recommendations/profile").status_code == 401


def test_demo_accounts_get_disjoint_personalized_lists(api):
    maria = recommendations(api, login(api, MARIA))
    radu = recommendations(api, login(api, RADU))
    assert maria["strategy"] == radu["strategy"] == "personalized"
    assert maria["fallback_reason"] is None
    assert len(maria["items"]) == len(radu["items"]) == 10
    assert set(ids(maria)).isdisjoint(ids(radu))
    assert all(item["product"]["price"] <= 300 for item in maria["items"])


def test_response_follows_the_contract(api):
    item = recommendations(api, login(api, MARIA), k=1)["items"][0]
    assert set(item) == {"product", "score", "explanation"}
    assert set(item["explanation"]) == {"text", "matched", "because_of"}
    assert {"group": "activities", "value": "running", "label": "Alergare"} in item["explanation"]["matched"]
    assert all(set(ref) == {"id", "name"} for ref in item["explanation"]["because_of"])
    assert 0 < item["score"] <= 1


def test_new_profile_settings_are_reflected_immediately(api):
    headers = login(api, MARIA)
    before = recommendations(api, headers)
    settings = {"activities": {"cycling": "high"}, "level": "advanced", "styles": ["performance"], "season": "all_year"}
    assert api.put("/profile", json=settings, headers=headers).status_code == 200
    after = recommendations(api, headers)
    assert ids(after) != ids(before)
    # Istoricul de alergare al Mariei contează în continuare (α = 0,5), dar majoritatea listei e acum ciclism.
    cycling = [item for item in after["items"] if item["product"]["category"] == "cycling"]
    assert not any(item["product"]["category"] == "cycling" for item in before["items"])
    assert len(cycling) >= 5
    assert all("ciclism" in item["explanation"]["text"] for item in cycling)


def test_new_account_with_settings_and_no_history_gets_personalized_recommendations(api):
    headers = register_headers(api, email="nou@example.com")
    settings = {"activities": {"hiking": "high"}, "level": "beginner", "styles": ["budget"], "max_budget": 400}
    assert api.put("/profile", json=settings, headers=headers).status_code == 200
    result = recommendations(api, headers)
    assert result["strategy"] == "personalized"
    assert all(item["product"]["price"] <= 400 for item in result["items"])
    assert result["items"][0]["product"]["category"] == "hiking"


def test_new_account_without_settings_gets_the_marked_fallback(api):
    result = recommendations(api, register_headers(api, email="gol@example.com"), k=5)
    assert result["strategy"] == "popular"
    assert result["fallback_reason"] == "Completează setările de profil pentru recomandări personalizate."
    scores = [item["score"] for item in result["items"]]
    assert scores == sorted(scores, reverse=True) and scores[0] > 0
    assert result["items"][0]["explanation"]["text"].startswith("Printre cele mai cumpărate")


def test_exclude_and_purchases_remove_products(api):
    headers = login(api, MARIA)
    first = ids(recommendations(api, headers))[0]
    assert first not in ids(recommendations(api, headers, exclude=first))
    event(api, headers, first, "purchase")
    assert first not in ids(recommendations(api, headers, k=50))


def test_a_new_favorite_changes_the_order(api):
    headers = register_headers(api, email="fav@example.com")
    api.put("/profile", json={"activities": {"running": "high"}, "level": "beginner"}, headers=headers)
    before = recommendations(api, headers)
    pro = api.get("/products", params={"category": "running", "q": "Pro", "available_only": True}).json()["items"][0]
    event(api, headers, pro["id"], "favorite")
    assert ids(recommendations(api, headers)) != ids(before)


def test_k_is_validated(api):
    headers = login(api, MARIA)
    assert api.get("/recommendations", headers=headers, params={"k": 0}).status_code == 422
    assert api.get("/recommendations", headers=headers, params={"k": 51}).status_code == 422


# ---- GET /recommendations/profile ----

def test_recommendation_profile_shows_sources_interests_and_products(api):
    data = api.get("/recommendations/profile", headers=login(api, MARIA)).json()
    assert data["sources"] == {"declared": 0.5, "behavior": 0.5}
    assert data["interests"][0]["label"] == "Alergare"
    assert sum(i["weight"] for i in data["interests"]) <= 1.0001
    top = data["top_products"][0]
    assert top["product"]["name"] == "Pantofi de alergare pe șosea Ritm Start"
    assert top["events"] == ["purchase", "view"] and top["weight"] == 12.0


def test_recommendation_profile_of_maria_and_radu_differ(api):
    maria = {i["value"] for i in api.get("/recommendations/profile", headers=login(api, MARIA)).json()["interests"][:4]}
    radu = {i["value"] for i in api.get("/recommendations/profile", headers=login(api, RADU)).json()["interests"][:4]}
    assert maria.isdisjoint(radu)


def test_empty_account_has_an_empty_recommendation_profile(api):
    data = api.get("/recommendations/profile", headers=register_headers(api, email="gol2@example.com")).json()
    assert data == {"sources": {"declared": 0.0, "behavior": 0.0}, "interests": [], "top_products": []}


# ---- GET /products/{id}/similar ----

def test_similar_products_work_without_login(api):
    items = api.get("/products/1/similar", params={"k": 3}).json()["items"]
    assert len(items) == 3 and 1 not in [i["product"]["id"] for i in items]
    assert items[0]["explanation"]["text"].startswith("Caracteristici comune")
    assert items[0]["explanation"]["because_of"][0]["id"] == 1


def test_similar_products_exclude_the_users_purchases(api):
    headers = login(api, MARIA)
    shoes = next(p for p in api.get("/me/history", headers=headers).json()["purchases"])["product"]["id"]
    neighbour = api.get(f"/products/{shoes}/similar", params={"k": 1}).json()["items"][0]["product"]["id"]
    event(api, headers, neighbour, "purchase")
    assert neighbour not in [i["product"]["id"] for i in api.get(f"/products/{shoes}/similar", headers=headers).json()["items"]]


def test_similar_errors(api):
    assert api.get("/products/9999/similar").status_code == 404
    assert api.get("/products/1/similar", headers={"Authorization": "Bearer invalid"}).status_code == 401


# ---- Catalogul ----

def test_vectors_are_rebuilt_when_the_catalog_changes(api, seeded):
    headers = login(api, MARIA)
    first = ids(recommendations(api, headers))[0]
    engine = create_db_engine(seeded.database_file)
    with Session(engine) as session:
        product = session.get(Product, first)
        product.available = False
        session.add(product)
        session.commit()
    engine.dispose()
    assert first not in ids(recommendations(api, headers, k=50))


def test_empty_catalog_gives_a_clear_error(client):
    headers = register_headers(client, email="catalog@example.com")
    response = client.get("/recommendations", headers=headers)
    assert response.status_code == 503
    assert "python -m app.seed" in response.json()["detail"]
