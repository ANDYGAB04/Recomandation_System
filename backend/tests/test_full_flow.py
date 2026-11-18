
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.config import Settings
from app.db import create_db_engine, init_db
from app.main import create_app
from app.seed import seed_all
from tests.helpers import auth_header

UI_PAGE_SIZE = 12  

CYCLIST = {"activities": {"cycling": "high"}, "level": "intermediate", "styles": ["ultralight"], "max_budget": 500}


@pytest.fixture(scope="module")
def api(tmp_path_factory):
    settings = Settings(database_path=tmp_path_factory.mktemp("flow") / "flow.db", secret_key="test")
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        seed_all(session, customers=60)
    engine.dispose()
    with TestClient(create_app(settings)) as client:
        yield client


def new_account(client):
    email = f"cont-{uuid.uuid4().hex[:8]}@exemplu.ro"
    response = client.post("/auth/register", json={"email": email, "password": "parola-noua", "display_name": "Nou"})
    assert response.status_code == 201
    return email, auth_header(response.json()["access_token"])


def login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return auth_header(response.json()["access_token"])


def recommend(client, headers, k=UI_PAGE_SIZE):
    response = client.get("/recommendations", headers=headers, params={"k": k})
    assert response.status_code == 200, response.text
    return response.json()


def ids(recommendations):
    return [item["product"]["id"] for item in recommendations["items"]]


def act(client, headers, product_id, type_):
    return client.post(
        "/interactions", headers=headers, json={"event_id": str(uuid.uuid4()), "product_id": product_id, "type": type_}
    )




def test_new_account_settings_then_recommendations(api):
    email, headers = new_account(api)

    assert api.get("/profile", headers=headers).json()["is_complete"] is False

    saved = api.put("/profile", headers=headers, json=CYCLIST)
    assert saved.status_code == 200 and saved.json()["is_complete"] is True

    recs = recommend(api, headers)
    assert recs["strategy"] == "personalized" and recs["fallback_reason"] is None
    assert len(recs["items"]) == UI_PAGE_SIZE
    for item in recs["items"]:
        product = item["product"]
        assert "cycling" in product["usages"]
        assert product["price"] <= CYCLIST["max_budget"]
        assert product["available"]
        assert item["explanation"]["text"]
        assert any(m["value"] == "cycling" for m in item["explanation"]["matched"])
    assert "ultralight" in recs["items"][0]["product"]["styles"]

    again = login(api, email, "parola-noua")
    assert {k: v for k, v in api.get("/profile", headers=again).json().items() if k in CYCLIST} == CYCLIST




def test_changing_settings_changes_the_list(api):
    _, headers = new_account(api)
    api.put("/profile", headers=headers, json=CYCLIST)
    cycling = recommend(api, headers)

    api.put("/profile", headers=headers, json={**CYCLIST, "activities": {"running": "high"}, "max_budget": 200})
    running = recommend(api, headers)

    assert set(ids(cycling)).isdisjoint(ids(running))
    assert all("running" in i["product"]["usages"] and i["product"]["price"] <= 200 for i in running["items"])




def test_views_and_a_favorite_adapt_the_list_and_purchases_disappear(api):
    _, headers = new_account(api)
    api.put("/profile", headers=headers, json=CYCLIST)
    before = recommend(api, headers)

    target = before["items"][5]["product"]["id"]
    for _ in range(3):
        assert act(api, headers, target, "view").status_code == 201
    assert act(api, headers, target, "favorite").status_code == 201

    after = recommend(api, headers)
    assert ids(after) != ids(before)
    assert ids(after).index(target) < 5  
    assert any(item["explanation"]["because_of"] for item in after["items"])

    bought = after["items"][0]["product"]["id"]
    assert act(api, headers, bought, "purchase").status_code == 201
    assert bought not in ids(recommend(api, headers, k=50))
    similar = api.get(f"/products/{target}/similar", headers=headers).json()["items"]
    assert bought not in [item["product"]["id"] for item in similar]




def test_demo_accounts_have_no_common_recommendation(api):
    maria = login(api, "maria@example.com", "maria2026")
    radu = login(api, "radu@example.com", "radu2026")
    maria_recs, radu_recs = recommend(api, maria), recommend(api, radu)

    assert maria_recs["strategy"] == radu_recs["strategy"] == "personalized"
    assert set(ids(maria_recs)).isdisjoint(ids(radu_recs))
    assert all("running" in i["product"]["usages"] for i in maria_recs["items"])
    assert all({"camping", "hiking"} & set(i["product"]["usages"]) for i in radu_recs["items"])
    assert all(i["product"]["price"] <= 300 for i in maria_recs["items"])




def test_account_without_settings_or_history_gets_the_marked_fallback(api):
    _, headers = new_account(api)
    recs = recommend(api, headers)
    assert recs["strategy"] == "popular"
    assert recs["fallback_reason"] == "Completează setările de profil pentru recomandări personalizate."
    assert recs["items"]


def test_duplicate_email_and_wrong_password(api):
    email, _ = new_account(api)
    duplicate = api.post("/auth/register", json={"email": email.upper(), "password": "parola-noua", "display_name": "X"})
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Există deja un cont cu acest e-mail."

    wrong = api.post("/auth/login", json={"email": email, "password": "alta-parola"})
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == "E-mail sau parolă greșită."


def test_buying_an_unavailable_product_is_rejected(api):
    _, headers = new_account(api)
    products = api.get("/products", params={"limit": 100}).json()["items"]
    products += api.get("/products", params={"limit": 100, "offset": 100}).json()["items"]
    unavailable = next(p for p in products if not p["available"])

    response = act(api, headers, unavailable["id"], "purchase")
    assert response.status_code == 409
    assert response.json()["detail"] == "Produsul nu este disponibil."
    assert act(api, headers, 999_999, "purchase").status_code == 404


def test_budget_below_every_price_gives_an_empty_fallback_with_reason(api):
    _, headers = new_account(api)
    api.put("/profile", headers=headers, json={"activities": {"camping": "high"}, "max_budget": 10})
    recs = recommend(api, headers)
    assert recs["strategy"] == "popular"
    assert recs["fallback_reason"] == "Niciun produs disponibil nu se potrivește profilului și bugetului tău."
    assert recs["items"] == []


def test_resent_event_is_saved_once(api):
    _, headers = new_account(api)
    product_id = api.get("/products", params={"limit": 1}).json()["items"][0]["id"]
    payload = {"event_id": str(uuid.uuid4()), "product_id": product_id, "type": "favorite"}
    assert api.post("/interactions", headers=headers, json=payload).status_code == 201
    assert api.post("/interactions", headers=headers, json=payload).json()["recorded"] is False
    assert len(api.get("/me/history", headers=headers).json()["events"]) == 1
