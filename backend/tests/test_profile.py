import pytest
from sqlmodel import Session

from app.models import UserProfile

from .helpers import register, register_headers

FULL = {
    "activities": {"running": "high", "cycling": "low"},
    "level": "beginner",
    "styles": ["budget", "comfort"],
    "season": "summer",
    "max_budget": 300,
}


def test_new_account_has_empty_profile(client):
    response = client.get("/profile", headers=register_headers(client))
    assert response.status_code == 200
    body = response.json()
    assert body["activities"] == {} and body["styles"] == []
    assert body["level"] is None and body["season"] is None and body["max_budget"] is None
    assert body["is_complete"] is False
    assert body["updated_at"].endswith("Z")


def test_saved_profile_reads_back_identically(client):
    headers = register_headers(client)
    saved = client.put("/profile", json=FULL, headers=headers)
    assert saved.status_code == 200
    read = client.get("/profile", headers=headers).json()
    assert read == saved.json()
    assert {k: read[k] for k in FULL} == FULL
    assert read["is_complete"] is True


def test_put_replaces_all_settings(client):
    headers = register_headers(client)
    client.put("/profile", json=FULL, headers=headers)
    body = client.put("/profile", json={"activities": {"camping": "high"}}, headers=headers).json()
    assert body["activities"] == {"camping": "high"}
    assert body["level"] is None and body["styles"] == [] and body["season"] is None and body["max_budget"] is None


def test_profile_without_activities_is_incomplete(client):
    headers = register_headers(client)
    body = client.put("/profile", json={"level": "advanced", "styles": ["durable"]}, headers=headers).json()
    assert body["is_complete"] is False


@pytest.mark.parametrize(
    "change",
    [
        {"activities": {"swimming": "high"}},
        {"activities": {"running": "very"}},
        {"level": "expert"},
        {"styles": ["fancy"]},
        {"styles": ["budget", "budget"]},
        {"season": "spring"},
        {"max_budget": 0},
        {"max_budget": -10},
        {"unknown_field": 1},
    ],
)
def test_unknown_or_invalid_values_are_422(client, change):
    headers = register_headers(client)
    assert client.put("/profile", json={**FULL, **change}, headers=headers).status_code == 422
    # Profilul nu s-a schimbat.
    assert client.get("/profile", headers=headers).json()["activities"] == {}


def test_profile_requires_authentication(client):
    assert client.get("/profile").status_code == 401
    assert client.put("/profile", json=FULL).status_code == 401


def test_users_only_see_and_change_their_own_profile(client):
    ana = register_headers(client, "ana@exemplu.ro")
    radu = register_headers(client, "radu@exemplu.ro")
    client.put("/profile", json=FULL, headers=ana)
    client.put("/profile", json={"activities": {"camping": "high"}, "season": "winter"}, headers=radu)

    assert client.get("/profile", headers=ana).json()["activities"] == FULL["activities"]
    assert client.get("/profile", headers=radu).json()["activities"] == {"camping": "high"}


def test_missing_profile_row_is_recreated(client):
    body = register(client)
    with Session(client.app.state.engine) as session:
        session.delete(session.get(UserProfile, body["user"]["id"]))
        session.commit()
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    assert client.get("/profile", headers=headers).json()["is_complete"] is False
