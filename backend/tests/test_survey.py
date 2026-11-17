import pytest
from sqlmodel import Session, select

from app.models import SurveyParticipant, SurveyResponse, User
from app.survey import QUESTIONS

from .helpers import register_headers

ANSWERS = {"q1": 4, "q2": 5, "q3": 3, "q4": 4, "q5": 5, "q6": "  Mi-au plăcut explicațiile.  "}


def submit(client, headers, answers=ANSWERS):
    return client.post("/survey", headers=headers, json={"answers": answers})


def test_questions_are_public(client):
    body = client.get("/survey").json()
    assert [q["id"] for q in body["questions"]] == [q.id for q in QUESTIONS]
    assert body["questions"][0]["kind"] == "scale" and body["questions"][0]["low"]
    assert body["questions"][-1]["kind"] == "open"
    assert body["answered"] is None and body["responses"] == 0


def test_submit_once_and_answers_are_anonymous(client):
    headers = register_headers(client)
    assert client.get("/survey", headers=headers).json()["answered"] is False

    response = submit(client, headers)
    assert response.status_code == 201

    body = client.get("/survey", headers=headers).json()
    assert body["answered"] is True and body["responses"] == 1

    with Session(client.app.state.engine) as session:
        saved = session.exec(select(SurveyResponse)).one()
        assert saved.answers == {**ANSWERS, "q6": "Mi-au plăcut explicațiile."}
        # Răspunsul nu are nicio coloană care să-l lege de cont.
        assert set(SurveyResponse.model_fields) == {"id", "answers", "created_at", "is_test_data"}
        assert saved.is_test_data is False
        user = session.exec(select(User)).one()
        assert session.get(SurveyParticipant, user.id) is not None


def test_second_submission_is_409(client):
    headers = register_headers(client)
    submit(client, headers)
    response = submit(client, headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "Ai completat deja chestionarul. Mulțumim!"


def test_open_question_is_optional(client):
    headers = register_headers(client)
    answers = {k: v for k, v in ANSWERS.items() if k != "q6"}
    assert submit(client, headers, answers).status_code == 201


@pytest.mark.parametrize(
    ("change", "question"),
    [
        ({"q1": None}, "q1"),
        ({"q2": 0}, "q2"),
        ({"q3": 6}, "q3"),
        ({"q4": "4"}, "q4"),
        ({"q6": "x" * 1001}, "q6"),
        ({"q9": 3}, "q9"),
    ],
)
def test_invalid_answers_are_422_on_the_question(client, change, question):
    headers = register_headers(client)
    response = submit(client, headers, {**ANSWERS, **change})
    assert response.status_code == 422
    assert question in [e["loc"][-1] for e in response.json()["detail"]]
    assert client.get("/survey", headers=headers).json()["answered"] is False


def test_missing_answer_is_422(client):
    headers = register_headers(client)
    answers = {k: v for k, v in ANSWERS.items() if k != "q5"}
    response = submit(client, headers, answers)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "Alege un răspuns."


def test_submitting_requires_an_account(client):
    assert client.post("/survey", json={"answers": ANSWERS}).status_code == 401
