import itertools

import pytest
from sqlmodel import Session, func, select

from app.models import Favorite, Interaction, Product

from .helpers import register_headers

_ids = itertools.count(1)


@pytest.fixture
def products(client):
    with Session(client.app.state.engine) as session:
        items = [
            Product(name="Cort 2P", category="camping", usages=["camping"], price=800),
            Product(name="Pantofi Trail", category="running", usages=["running"], price=450),
            Product(name="Cască Veche", category="cycling", usages=["cycling"], price=200, available=False),
        ]
        session.add_all(items)
        session.commit()
        return {p.name: p.id for p in items}


@pytest.fixture
def ana(client):
    return register_headers(client, "ana@exemplu.ro")


def send(client, headers, product_id, type_, event_id=None):
    event_id = event_id or f"ev-{next(_ids)}"
    return client.post("/interactions", json={"event_id": event_id, "product_id": product_id, "type": type_},
                       headers=headers)


def count(client, model, **where):
    with Session(client.app.state.engine) as session:
        query = select(func.count()).select_from(model)
        for key, value in where.items():
            query = query.where(getattr(model, key) == value)
        return session.exec(query).one()


@pytest.mark.parametrize("type_", ["view", "favorite", "unfavorite", "purchase"])
def test_each_event_type_is_recorded(client, ana, products, type_):
    response = send(client, ana, products["Cort 2P"], type_, event_id="e-1")
    assert response.status_code == 201
    assert response.json() == {"event_id": "e-1", "recorded": True}
    assert count(client, Interaction, type=type_) == 1


def test_resending_the_same_event_does_not_duplicate_it(client, ana, products):
    first = send(client, ana, products["Cort 2P"], "view", event_id="same")
    again = send(client, ana, products["Cort 2P"], "view", event_id="same")
    assert first.status_code == 201
    assert again.status_code == 200
    assert again.json() == {"event_id": "same", "recorded": False}
    assert count(client, Interaction) == 1


def test_resent_purchase_is_not_rejected_as_repeat(client, ana, products):
    send(client, ana, products["Cort 2P"], "purchase", event_id="buy")
    assert send(client, ana, products["Cort 2P"], "purchase", event_id="buy").status_code == 200


def test_missing_product_is_404(client, ana, products):
    response = send(client, ana, 999, "view")
    assert response.status_code == 404
    assert response.json()["detail"] == "Produsul nu există."


def test_buying_unavailable_product_is_409(client, ana, products):
    response = send(client, ana, products["Cască Veche"], "purchase")
    assert response.status_code == 409
    assert response.json()["detail"] == "Produsul nu este disponibil."
    assert count(client, Interaction) == 0


def test_unavailable_product_can_still_be_viewed(client, ana, products):
    assert send(client, ana, products["Cască Veche"], "view").status_code == 201


def test_buying_twice_is_409(client, ana, products):
    assert send(client, ana, products["Cort 2P"], "purchase").status_code == 201
    response = send(client, ana, products["Cort 2P"], "purchase")
    assert response.status_code == 409
    assert response.json()["detail"] == "Ai cumpărat deja acest produs."


def test_favorites_reflect_the_last_action(client, ana, products):
    cort = products["Cort 2P"]
    send(client, ana, cort, "favorite")
    assert count(client, Favorite, product_id=cort) == 1
    send(client, ana, cort, "favorite")  
    assert count(client, Favorite, product_id=cort) == 1
    send(client, ana, cort, "unfavorite")
    assert count(client, Favorite, product_id=cort) == 0
    send(client, ana, cort, "unfavorite")  
    assert count(client, Favorite, product_id=cort) == 0
    send(client, ana, cort, "favorite")
    assert count(client, Favorite, product_id=cort) == 1
    assert count(client, Interaction) == 5


@pytest.mark.parametrize(
    "payload",
    [
        {"event_id": "x", "product_id": 1, "type": "like"},
        {"event_id": "", "product_id": 1, "type": "view"},
        {"event_id": "x" * 65, "product_id": 1, "type": "view"},
        {"product_id": 1, "type": "view"},
    ],
)
def test_invalid_payload_is_422(client, ana, products, payload):
    assert client.post("/interactions", json=payload, headers=ana).status_code == 422


def test_interactions_and_history_require_authentication(client, products):
    assert client.post("/interactions", json={"event_id": "x", "product_id": 1, "type": "view"}).status_code == 401
    assert client.get("/me/history").status_code == 401


def test_history(client, ana, products):
    cort, pantofi = products["Cort 2P"], products["Pantofi Trail"]
    send(client, ana, cort, "view", "h1")
    send(client, ana, cort, "favorite", "h2")
    send(client, ana, pantofi, "favorite", "h3")
    send(client, ana, pantofi, "purchase", "h4")
    send(client, ana, cort, "unfavorite", "h5")

    body = client.get("/me/history", headers=ana).json()
    assert [p["name"] for p in body["favorites"]] == ["Pantofi Trail"]
    assert [p["product"]["name"] for p in body["purchases"]] == ["Pantofi Trail"]
    assert body["purchases"][0]["purchased_at"].endswith("Z")
    assert [e["event_id"] for e in body["events"]] == ["h5", "h4", "h3", "h2", "h1"]
    assert body["events"][0] == {
        "event_id": "h5", "type": "unfavorite", "product": {"id": cort, "name": "Cort 2P"},
        "created_at": body["events"][0]["created_at"],
    }


def test_history_keeps_only_the_last_50_events(client, ana, products):
    for i in range(55):
        send(client, ana, products["Cort 2P"], "view", f"v{i:02d}")
    events = client.get("/me/history", headers=ana).json()["events"]
    assert len(events) == 50
    assert events[0]["event_id"] == "v54" and events[-1]["event_id"] == "v05"


def test_history_is_per_user(client, ana, products):
    radu = register_headers(client, "radu@exemplu.ro")
    send(client, ana, products["Cort 2P"], "favorite")
    send(client, radu, products["Pantofi Trail"], "purchase")

    ana_history = client.get("/me/history", headers=ana).json()
    radu_history = client.get("/me/history", headers=radu).json()
    assert [p["name"] for p in ana_history["favorites"]] == ["Cort 2P"] and ana_history["purchases"] == []
    assert radu_history["favorites"] == [] and len(radu_history["events"]) == 1


def test_another_user_can_buy_the_same_product(client, ana, products):
    radu = register_headers(client, "radu@exemplu.ro")
    assert send(client, ana, products["Cort 2P"], "purchase").status_code == 201
    assert send(client, radu, products["Cort 2P"], "purchase").status_code == 201
