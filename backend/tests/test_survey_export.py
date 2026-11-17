import csv
from datetime import UTC, datetime

from sqlmodel import Session

from app.db import create_db_engine, init_db
from app.models import SurveyResponse
from app.survey_export import COLUMNS, averages, rows, write_csv


def test_export_has_no_personal_data_and_correct_averages(tmp_path):
    engine = create_db_engine(tmp_path / "export.db")
    init_db(engine)
    with Session(engine) as session:
        session.add(SurveyResponse(answers={"q1": 4, "q2": 5, "q3": 3, "q4": 4, "q5": 5, "q6": "Bun, ușor"},
                                   created_at=datetime(2026, 11, 18, 14, 37, 12, tzinfo=UTC)))
        session.add(SurveyResponse(answers={"q1": 2, "q2": 3, "q3": 4, "q4": 2, "q5": 4, "q6": ""}))
        session.commit()
        data = rows(session)
    engine.dispose()

    assert [row["raspuns"] for row in data] == [1, 2]
    assert data[0]["data"] == "2026-11-18"  # doar ziua, fără oră
    assert averages(data) == {"q1": 3.0, "q2": 4.0, "q3": 3.5, "q4": 3.0, "q5": 4.5}

    out = tmp_path / "raspunsuri.csv"
    write_csv(data, out)
    with out.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        assert reader.fieldnames == COLUMNS
        lines = list(reader)
    assert lines[0]["q6"] == "Bun, ușor" and lines[1]["q1"] == "2"
    assert not {"email", "user_id", "display_name"} & set(COLUMNS)


def test_export_without_responses(tmp_path):
    engine = create_db_engine(tmp_path / "empty.db")
    init_db(engine)
    with Session(engine) as session:
        assert rows(session) == []
    assert averages([]) == {f"q{i}": None for i in range(1, 6)}
