"""Datele de test pentru evaluarea cu utilizatori: generate de seed, marcate și separate de cele reale."""

import csv

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, select

from app.db import create_db_engine, init_db
from app.main import create_app
from app.models import SurveyResponse
from app.seed import seed_all
from app.seed.feedback_test_data import TEST_PARTICIPANTS, VOTES_PER_PARTICIPANT
from app.survey_export import REAL, TEST, rows, write_csv
from tests.helpers import register_headers

SCALE = {"q1": 4, "q2": 5, "q3": 4, "q4": 3, "q5": 5}


@pytest.fixture
def seeded(settings):
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        summary = seed_all(session, customers=30)
    yield engine, summary
    engine.dispose()


@pytest.fixture
def api(settings, seeded):
    with TestClient(create_app(settings)) as client:
        yield client


def test_seed_creates_labeled_test_data_once(seeded):
    engine, summary = seeded
    assert summary.test_survey_responses_created == TEST_PARTICIPANTS
    assert summary.test_votes_created == TEST_PARTICIPANTS * VOTES_PER_PARTICIPANT
    with Session(engine) as session:
        responses = session.exec(select(SurveyResponse)).all()
        assert responses and all(r.is_test_data for r in responses)
        again = seed_all(session, customers=30)
    assert (again.test_survey_responses_created, again.test_votes_created) == (0, 0)


def test_test_data_is_counted_separately_from_real_data(api):
    survey = api.get("/survey").json()
    assert (survey["responses"], survey["test_responses"]) == (0, TEST_PARTICIPANTS)
    summary = api.get("/evaluation/feedback").json()
    assert summary["votes"] == 0 and summary["users"] == 0
    assert summary["test_data"]["votes"] == TEST_PARTICIPANTS * VOTES_PER_PARTICIPANT
    assert summary["test_data"]["users"] == TEST_PARTICIPANTS

    headers = register_headers(api, email="participant@example.com")
    assert api.post("/survey", headers=headers, json={"answers": {**SCALE, "q6": ""}}).status_code == 201
    vote = {"product_id": 1, "useful": True, "strategy": "personalized"}
    assert api.post("/recommendations/feedback", headers=headers, json=vote).status_code == 200
    survey = api.get("/survey").json()
    assert (survey["responses"], survey["test_responses"]) == (1, TEST_PARTICIPANTS)
    summary = api.get("/evaluation/feedback").json()
    assert (summary["votes"], summary["users"]) == (1, 1)
    assert summary["test_data"]["votes"] == TEST_PARTICIPANTS * VOTES_PER_PARTICIPANT


def test_export_labels_each_response(seeded, tmp_path, api):
    engine, _ = seeded
    headers = register_headers(api, email="real@example.com")
    api.post("/survey", headers=headers, json={"answers": {**SCALE, "q6": "Bun."}})
    with Session(engine) as session:
        data = rows(session)
    out = tmp_path / "raspunsuri.csv"
    write_csv(data, out)
    with out.open(encoding="utf-8-sig") as file:
        sources = [row["sursa"] for row in csv.DictReader(file)]
    assert sources.count(TEST) == TEST_PARTICIPANTS and sources.count(REAL) == 1


def test_old_database_gets_the_new_column_without_losing_data(tmp_path):
    engine = create_db_engine(tmp_path / "old.db")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE survey_responses (id INTEGER PRIMARY KEY, answers JSON NOT NULL, created_at DATETIME NOT NULL)"))
        connection.execute(text("""INSERT INTO survey_responses (answers, created_at) VALUES ('{"q1": 5}', '2026-11-17 10:00:00')"""))
    init_db(engine)
    with Session(engine) as session:
        response = session.exec(select(SurveyResponse)).one()
    assert response.answers == {"q1": 5} and response.is_test_data is False
    engine.dispose()
