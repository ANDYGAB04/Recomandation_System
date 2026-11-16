import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import create_db_engine, init_db
from app.main import create_app
from app.seed import seed_catalog
from app.seed.demo import seed_demo_accounts
from tests.helpers import auth_header, register_headers


@pytest.fixture
def api(settings):
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        seed_catalog(session)
        seed_demo_accounts(session)
    engine.dispose()
    with TestClient(create_app(settings)) as client:
        yield client


def vote(client, headers, product_id, useful, strategy="personalized"):
    return client.post("/recommendations/feedback", headers=headers,
                       json={"product_id": product_id, "useful": useful, "strategy": strategy})


def test_feedback_requires_authentication(api):
    assert api.post("/recommendations/feedback", json={"product_id": 1, "useful": True}).status_code == 401
    assert api.get("/recommendations/feedback").status_code == 401


def test_a_new_vote_replaces_the_old_one(api):
    headers = register_headers(api, email="vot@example.com")
    first = vote(api, headers, 1, True)
    assert first.status_code == 200 and first.json()["useful"] is True
    second = vote(api, headers, 1, False)
    assert second.json()["useful"] is False
    votes = api.get("/recommendations/feedback", headers=headers).json()
    assert [(v["product_id"], v["useful"]) for v in votes] == [(1, False)]


def test_votes_are_private_to_each_user(api):
    ana, ion = register_headers(api, email="ana@example.com"), register_headers(api, email="ion@example.com")
    vote(api, ana, 1, True)
    vote(api, ion, 2, False)
    assert [v["product_id"] for v in api.get("/recommendations/feedback", headers=ana).json()] == [1]


def test_invalid_feedback_is_rejected(api):
    headers = register_headers(api, email="rau@example.com")
    assert vote(api, headers, 99999, True).status_code == 404
    assert vote(api, headers, 1, True, strategy="random").status_code == 422


def test_summary_counts_votes_per_strategy(api):
    assert api.get("/evaluation/feedback").json() == {
        "votes": 0, "useful": 0, "useful_share": None, "users": 0,
        "personalized": {"votes": 0, "useful": 0, "useful_share": None},
        "popular": {"votes": 0, "useful": 0, "useful_share": None},
    }
    ana, ion = register_headers(api, email="ana2@example.com"), register_headers(api, email="ion2@example.com")
    vote(api, ana, 1, True)
    vote(api, ana, 2, False)
    vote(api, ion, 1, True)
    vote(api, ion, 3, True, strategy="popular")
    summary = api.get("/evaluation/feedback").json()
    assert (summary["votes"], summary["useful"], summary["useful_share"], summary["users"]) == (4, 3, 0.75, 2)
    assert summary["personalized"] == {"votes": 3, "useful": 2, "useful_share": 0.6667}
    assert summary["popular"] == {"votes": 1, "useful": 1, "useful_share": 1.0}


def test_summary_ignores_demo_accounts(api):
    token = api.post("/auth/login", json={"email": "maria@example.com", "password": "maria2026"}).json()["access_token"]
    vote(api, auth_header(token), 1, True)
    assert api.get("/evaluation/feedback").json()["votes"] == 0
