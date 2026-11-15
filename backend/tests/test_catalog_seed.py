from sqlmodel import Session, select

from app.db import create_db_engine, init_db
from app.models import Product
from app.seed import seed_catalog
from app.seed.catalog import build_catalog
from app.vocabulary import Activity, Level, Season, Style


def rows(session):
    return [p.model_dump() for p in session.exec(select(Product).order_by(Product.id))]


def test_build_catalog_is_deterministic():
    assert build_catalog() == build_catalog()
    assert build_catalog(seed=1) != build_catalog(seed=2)


def test_catalog_size_and_values():
    catalog = build_catalog()
    assert 100 <= len(catalog) <= 150
    assert len({p["name"] for p in catalog}) == len(catalog)
    activities = {a.value for a in Activity}
    assert {p["category"] for p in catalog} == activities
    for p in catalog:
        assert p["category"] in p["usages"]
        assert set(p["usages"]) <= activities
        assert set(p["levels"]) <= {lv.value for lv in Level}
        assert set(p["styles"]) <= {s.value for s in Style}
        assert set(p["seasons"]) <= {s.value for s in Season}
        assert p["price"] > 0
        assert p["is_test_data"] is True


def test_catalog_covers_both_demo_profiles():
    catalog = build_catalog()
    # Maria: alergare, începătoare, vară, buget redus.
    assert any(
        "running" in p["usages"] and "beginner" in p["levels"] and "budget" in p["styles"] and "summer" in p["seasons"]
        for p in catalog
    )
    # Radu: camping și drumeție de iarnă, avansat, rezistență.
    assert any(
        {"camping", "hiking"} & set(p["usages"]) and "advanced" in p["levels"] and "durable" in p["styles"]
        and "winter" in p["seasons"]
        for p in catalog
    )


def test_two_seed_runs_give_the_same_data(tmp_path):
    engine = create_db_engine(tmp_path / "seed.db")
    init_db(engine)
    with Session(engine) as session:
        assert seed_catalog(session) == (len(build_catalog()), 0)
        first = rows(session)
        assert seed_catalog(session) == (0, len(build_catalog()))
        assert rows(session) == first


def test_seeding_two_databases_gives_identical_rows(tmp_path):
    results = []
    for name in ("a.db", "b.db"):
        engine = create_db_engine(tmp_path / name)
        init_db(engine)
        with Session(engine) as session:
            seed_catalog(session)
            results.append(rows(session))
        engine.dispose()
    assert results[0] == results[1]
