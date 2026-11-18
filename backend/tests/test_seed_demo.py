import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.config import Settings
from app.db import create_db_engine, init_db
from app.main import create_app
from app.models import Favorite, Interaction, Product, User, UserProfile
from app.recommender import PERSONALIZED, ContentRecommender, History, recommend
from app.seed import DEMO_ACCOUNTS, is_simulated_email, reset_database, seed_all
from app.seed.timeline import SIMULATION_END, SIMULATION_START, final_favorites
from app.vocabulary import EventType

CUSTOMERS = 40


@pytest.fixture
def settings(tmp_path):
    return Settings(database_path=tmp_path / "seed.db", secret_key="test")


@pytest.fixture
def engine(settings):
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        seed_all(session, customers=CUSTOMERS)
    yield engine
    engine.dispose()


def dump(engine):
    with Session(engine) as s:
        return (
            [(u.id, u.email, u.display_name, u.created_at) for u in s.exec(select(User).order_by(User.id))],
            [p.model_dump() for p in s.exec(select(UserProfile).order_by(UserProfile.user_id))],
            [i.model_dump() for i in s.exec(select(Interaction).order_by(Interaction.id))],
            [f.model_dump() for f in s.exec(select(Favorite).order_by(Favorite.user_id, Favorite.product_id))],
        )


def demo_user(session, email):
    return session.exec(select(User).where(User.email == email)).one()


def test_seed_creates_catalog_demo_accounts_and_customers(engine):
    with Session(engine) as s:
        users = s.exec(select(User)).all()
        assert len(s.exec(select(Product)).all()) > 100
        assert sorted(u.email for u in users if not is_simulated_email(u.email)) == sorted(a.email for a in DEMO_ACCOUNTS)
        assert sum(is_simulated_email(u.email) for u in users) == CUSTOMERS
        assert len(s.exec(select(UserProfile)).all()) == len(users)


def test_demo_accounts_can_log_in_and_simulated_customers_cannot(engine, settings):
    with TestClient(create_app(settings)) as client:
        for account in DEMO_ACCOUNTS:
            response = client.post("/auth/login", json={"email": account.email, "password": account.password})
            assert response.status_code == 200
            assert response.json()["user"]["display_name"] == account.display_name
        response = client.post("/auth/login", json={"email": "client001@simulat.example.com", "password": "orice-parola"})
        assert response.status_code == 401


def test_two_runs_produce_the_same_data(tmp_path, engine):
    other = create_db_engine(tmp_path / "other.db")
    init_db(other)
    with Session(other) as session:
        seed_all(session, customers=CUSTOMERS)
    assert dump(other) == dump(engine)
    other.dispose()


def test_running_the_seed_again_adds_nothing(engine):
    before = dump(engine)
    with Session(engine) as session:
        summary = seed_all(session, customers=CUSTOMERS)
    assert (summary.products_created, summary.demo_accounts_created, summary.simulated_customers_created) == (0, 0, 0)
    assert dump(engine) == before


def test_reset_removes_accounts_created_in_the_app(engine):
    with Session(engine) as s:
        s.add(User(email="nou@example.com", password_hash="x", display_name="Nou"))
        s.commit()
    reset_database(engine)
    with Session(engine) as s:
        assert s.exec(select(User)).all() == []
        seed_all(s, customers=CUSTOMERS)
        assert s.exec(select(User).where(User.email == "nou@example.com")).first() is None


def test_demo_accounts_have_nothing_in_common(engine):
    maria_account, radu_account = DEMO_ACCOUNTS
    with Session(engine) as s:
        maria = s.get(UserProfile, demo_user(s, maria_account.email).id)
        radu = s.get(UserProfile, demo_user(s, radu_account.email).id)
        assert set(maria.activities).isdisjoint(radu.activities)
        assert set(maria.styles).isdisjoint(radu.styles)
        assert maria.season != radu.season and maria.level != radu.level

        for account, profile in ((maria_account, maria), (radu_account, radu)):
            user = demo_user(s, account.email)
            for event in s.exec(select(Interaction).where(Interaction.user_id == user.id)):
                assert set(s.get(Product, event.product_id).usages) <= set(profile.activities)


def test_demo_recommendations_have_no_common_product(engine):
    with Session(engine) as s:
        rec = ContentRecommender(s.exec(select(Product).order_by(Product.id)).all())
        top = []
        for account in DEMO_ACCOUNTS:
            user = demo_user(s, account.email)
            events = s.exec(select(Interaction).where(Interaction.user_id == user.id)
                            .order_by(Interaction.created_at, Interaction.id)).all()
            history = History.from_interactions(events)
            result = recommend(rec, s.get(UserProfile, user.id), history, {}, k=10)
            assert result.strategy == PERSONALIZED and len(result.items) == 10
            ids = {item.product_id for item in result.items}
            assert ids.isdisjoint(history.purchased)
            top.append(ids)
        assert top[0].isdisjoint(top[1])


def test_history_is_consistent(engine):
    with Session(engine) as s:
        for user in s.exec(select(User)):
            events = s.exec(select(Interaction).where(Interaction.user_id == user.id)
                            .order_by(Interaction.created_at, Interaction.id)).all()
            assert all(SIMULATION_START <= e.created_at.replace(tzinfo=SIMULATION_START.tzinfo) <= SIMULATION_END for e in events)
            assert all(e.type in set(EventType) for e in events)
            favorites = {f.product_id for f in s.exec(select(Favorite).where(Favorite.user_id == user.id))}
            assert favorites == set(final_favorites(events))
            purchases = [e.product_id for e in events if e.type == EventType.PURCHASE]
            assert len(purchases) == len(set(purchases))
