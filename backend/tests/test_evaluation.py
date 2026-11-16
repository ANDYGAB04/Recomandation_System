from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import create_db_engine, init_db
from app.evaluation import POPULARITY, Config, build_window, evaluate_config, load_and_run
from app.main import create_app
from app.recommender import ContentRecommender
from app.seed import seed_all

T0 = datetime(2026, 8, 1, tzinfo=UTC)
CUT = datetime(2026, 9, 1, tzinfo=UTC)
END = datetime(2026, 10, 1, tzinfo=UTC)


def product(pid, activity, available=True, price=100.0):
    return SimpleNamespace(id=pid, name=f"P{pid}", category=activity, usages=[activity], levels=[], styles=[],
                           seasons=[], tags=[], description="", price=price, available=available)


PRODUCTS = [product(1, "camping"), product(2, "camping"), product(3, "running"), product(4, "running"),
            product(5, "camping", available=False)]

EVENTS = [
    (10, 1, "purchase", T0),   # 10: camping în trecut
    (10, 2, "purchase", CUT),  # relevant (camping)
    (10, 5, "purchase", CUT),  # indisponibil acum: nu e relevant
    (11, 3, "purchase", T0),
    (11, 3, "purchase", CUT),  # cumpărat și înainte: nu e relevant
    (12, 4, "purchase", CUT),  # 12: fără istoric înainte de prag
    (13, 4, "purchase", END),  # după interval: ignorat
]


def test_window_uses_only_the_past_for_history_and_popularity():
    window = build_window(PRODUCTS, EVENTS, CUT, END)
    assert window.relevant == {10: {2}, 12: {4}}
    assert window.purchase_counts == {1: 1, 3: 1}
    assert window.histories[10].purchased == {1}
    assert window.histories[12].is_empty()
    assert window.users_total == 4


def test_metrics_on_a_small_example_computed_by_hand():
    window = build_window(PRODUCTS, EVENTS, CUT, END)
    rec = ContentRecommender(PRODUCTS)
    behavior = evaluate_config(window, rec, {}, Config("comportament", "personalized", alpha=0.0), k=2)
    # Utilizatorul 10 are istoric de camping: produsul 2 e singurul camping disponibil necumpărat → găsit.
    # P@2 = 1 găsit / 2 recomandate = 0,5; R@2 = 1 / 1 relevant = 1.
    assert (behavior["users"], behavior["users_without_history"]) == (1, 1)
    assert (behavior["precision_at_k"], behavior["recall_at_k"]) == (0.5, 1.0)

    popular = evaluate_config(window, rec, {}, POPULARITY, k=2)
    # Popularitatea din trecut recomandă 3 (cumpărat o dată), apoi 2 (după id): pentru 10, produsul 2 e găsit.
    assert (popular["precision_at_k"], popular["recall_at_k"]) == (0.5, 1.0)
    # Utilizatorul 12 (fără istoric) primește 1 și 3 (câte un cumpărător fiecare); produsul 4 nu e printre ele.
    assert popular["without_history"] == {"precision_at_k": 0.0, "recall_at_k": 0.0}


@pytest.fixture(scope="module")
def seeded_engine(tmp_path_factory):
    path = tmp_path_factory.mktemp("eval") / "eval.db"
    engine = create_db_engine(path)
    init_db(engine)
    with Session(engine) as session:
        seed_all(session)
    yield engine
    engine.dispose()


def without_latency(report):
    for part in ("validation", "test"):
        for row in report[part]["results"]:
            row.pop("latency_ms")
    return report


def test_results_are_reproducible(seeded_engine):
    with Session(seeded_engine) as session:
        assert without_latency(load_and_run(session)) == without_latency(load_and_run(session))


def test_report_states_the_data_is_synthetic_and_profile_beats_popularity(seeded_engine):
    with Session(seeded_engine) as session:
        report = load_and_run(session)
    assert "sintetice" in report["note"]
    test = {row["strategy"]: row for row in report["test"]["results"]}
    # Concluzia principală a evaluării, pe datele generate cu seed-ul implicit.
    assert test["personalized"]["recall_at_k"] > test["popular"]["recall_at_k"]
    assert test["personalized"]["coverage"] > test["popular"]["coverage"]
    assert report["selected_config"] in {row["config"] for row in report["validation"]["results"]}


def test_evaluation_endpoint(settings):
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        seed_all(session, customers=60)
    engine.dispose()
    with TestClient(create_app(settings)) as client:
        first = client.get("/evaluation")
        assert first.status_code == 200
        data = first.json()
        assert data["k"] == 5 and set(data) == {"k", "note", "selected_config", "validation", "test"}
        assert data["test"]["results"][0]["config"] == "popularitate"
        assert client.get("/evaluation").json() == data  # din memorie


def test_evaluation_without_data_gives_a_clear_error(client):
    response = client.get("/evaluation")
    assert response.status_code == 503
    assert "python -m app.seed" in response.json()["detail"]
