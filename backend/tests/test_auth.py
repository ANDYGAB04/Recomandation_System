from datetime import UTC, datetime, timedelta

import pytest
from sqlmodel import Session, select

from app.models import User, UserProfile
from app.security import create_access_token

ANA = {"email": "Ana@Exemplu.ro", "password": "parola-secreta", "display_name": "Ana"}


def register(client, **overrides):
    return client.post("/auth/register", json={**ANA, **overrides})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def db_session(client):
    return Session(client.app.state.engine)


def test_register_creates_account_profile_and_token(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"] == {"id": body["user"]["id"], "email": "ana@exemplu.ro", "display_name": "Ana"}

    with db_session(client) as session:
        profile = session.get(UserProfile, body["user"]["id"])
        assert profile is not None
        assert profile.activities == {} and profile.styles == [] and profile.level is None


def test_register_then_login_and_me(client):
    register(client)
    response = client.post("/auth/login", json={"email": "ANA@exemplu.ro", "password": ANA["password"]})
    assert response.status_code == 200
    token = response.json()["access_token"]

    me = client.get("/auth/me", headers=auth_header(token))
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == "ana@exemplu.ro"
    assert body["display_name"] == "Ana"
    assert body["created_at"].endswith("Z")


def test_register_token_works_directly(client):
    token = register(client).json()["access_token"]
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 200


def test_duplicate_email_is_409_regardless_of_case(client):
    assert register(client).status_code == 201
    response = register(client, email="ANA@EXEMPLU.RO")
    assert response.status_code == 409
    assert response.json()["detail"] == "Există deja un cont cu acest e-mail."


def test_wrong_password_and_unknown_email_give_same_401(client):
    register(client)
    wrong = client.post("/auth/login", json={"email": ANA["email"], "password": "alta-parola"})
    unknown = client.post("/auth/login", json={"email": "nimeni@exemplu.ro", "password": "alta-parola"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"] == "E-mail sau parolă greșită."


@pytest.mark.parametrize(
    "overrides",
    [{"email": "nu-e-email"}, {"password": "scurta"}, {"display_name": "   "}, {"display_name": "x" * 101}],
)
def test_register_rejects_invalid_data(client, overrides):
    assert register(client, **overrides).status_code == 422


def test_password_is_stored_only_as_hash(client):
    register(client)
    with db_session(client) as session:
        user = session.exec(select(User)).one()
    assert ANA["password"] not in user.password_hash
    assert user.password_hash.startswith("$2")  


def test_long_passwords_differ_after_72_bytes(client):
    base = "a" * 80
    register(client, password=base + "1")
    response = client.post("/auth/login", json={"email": ANA["email"], "password": base + "2"})
    assert response.status_code == 401


def test_me_without_token_is_401(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("token", ["nu-e-un-token", create_access_token(1, "alta-cheie")])
def test_me_with_invalid_token_is_401(client, token):
    register(client)
    assert client.get("/auth/me", headers=auth_header(token)).status_code == 401


def test_me_with_expired_token_is_401(client, settings):
    user_id = register(client).json()["user"]["id"]
    expired = create_access_token(user_id, settings.secret_key, now=datetime.now(UTC) - timedelta(days=8))
    assert client.get("/auth/me", headers=auth_header(expired)).status_code == 401


def test_me_for_deleted_user_is_401(client):
    body = register(client).json()
    with db_session(client) as session:
        session.delete(session.get(User, body["user"]["id"]))
        session.commit()
    assert client.get("/auth/me", headers=auth_header(body["access_token"])).status_code == 401
