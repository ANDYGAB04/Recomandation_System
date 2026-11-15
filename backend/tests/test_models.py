import pytest
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import create_db_engine, init_db
from app.models import Favorite, Interaction, Product, User, UserProfile


@pytest.fixture
def session(tmp_path):
    engine = create_db_engine(tmp_path / "models.db")
    init_db(engine)
    with Session(engine) as s:
        yield s


def make_user(session, email="ana@test.ro"):
    user = User(email=email, password_hash="hash", display_name="Ana")
    session.add(user)
    session.commit()
    return user


def make_product(session, name="Cort Ultralight", **kwargs):
    product = Product(name=name, category="camping", usages=["camping", "hiking"], styles=["ultralight"],
                      seasons=["summer"], levels=["intermediate"], tags=["cort"], price=899.99, **kwargs)
    session.add(product)
    session.commit()
    return product


def test_json_columns_round_trip(session):
    user = make_user(session)
    session.add(UserProfile(user_id=user.id, activities={"running": "high"}, styles=["budget"], max_budget=300))
    product = make_product(session)
    session.commit()
    session.expire_all()
    assert session.get(UserProfile, user.id).activities == {"running": "high"}
    assert session.get(Product, product.id).usages == ["camping", "hiking"]


def test_email_is_unique(session):
    make_user(session)
    with pytest.raises(IntegrityError):
        make_user(session)


def test_event_id_is_unique(session):
    user, product = make_user(session), make_product(session)
    session.add(Interaction(event_id="e1", user_id=user.id, product_id=product.id, type="view"))
    session.commit()
    session.add(Interaction(event_id="e1", user_id=user.id, product_id=product.id, type="view"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_interaction_needs_existing_product(session):
    user = make_user(session)
    session.add(Interaction(event_id="e2", user_id=user.id, product_id=999, type="view"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_unknown_event_type_is_rejected(session):
    user, product = make_user(session), make_product(session)
    session.add(Interaction(event_id="e3", user_id=user.id, product_id=product.id, type="like"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_negative_price_is_rejected(session):
    session.add(Product(name="Gratis", category="camping", price=-1))
    with pytest.raises(IntegrityError):
        session.commit()


def test_deleting_a_user_removes_profile_interactions_and_favorites(session):
    user, product = make_user(session), make_product(session)
    session.add_all([
        UserProfile(user_id=user.id),
        Interaction(event_id="e4", user_id=user.id, product_id=product.id, type="favorite"),
        Favorite(user_id=user.id, product_id=product.id),
    ])
    session.commit()
    session.delete(user)
    session.commit()
    assert session.exec(select(UserProfile)).all() == []
    assert session.exec(select(Interaction)).all() == []
    assert session.exec(select(Favorite)).all() == []
    assert session.get(Product, product.id) is not None
