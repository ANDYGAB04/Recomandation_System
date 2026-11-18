
import argparse
import csv
from pathlib import Path

from sqlmodel import Session, select

from .config import BACKEND_DIR, get_settings
from .db import create_db_engine, init_db
from .models import SurveyResponse
from .survey import QUESTIONS, SCALE_IDS

DEFAULT_OUT = BACKEND_DIR.parent / "docs" / "chestionar-raspunsuri.csv"
COLUMNS = ["raspuns", "sursa", "data", *(q.id for q in QUESTIONS)]
REAL, TEST = "real", "date de test"


def rows(session: Session) -> list[dict]:
    responses = session.exec(select(SurveyResponse).order_by(SurveyResponse.id)).all()
    return [
        {
            "raspuns": number,
            "sursa": TEST if response.is_test_data else REAL,
            "data": response.created_at.date().isoformat(),
            **{q.id: response.answers.get(q.id, "") for q in QUESTIONS},
        }
        for number, response in enumerate(responses, start=1)
    ]


def write_csv(data: list[dict], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(data)


def averages(data: list[dict]) -> dict[str, float | None]:
    result = {}
    for qid in SCALE_IDS:
        values = [row[qid] for row in data if isinstance(row[qid], int)]
        result[qid] = round(sum(values) / len(values), 2) if values else None
    return result


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.survey_export", description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="fișierul CSV (implicit docs/chestionar-raspunsuri.csv)")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_db_engine(settings.database_file)
    init_db(engine)
    with Session(engine) as session:
        data = rows(session)
    engine.dispose()

    write_csv(data, args.out)
    real = [row for row in data if row["sursa"] == REAL]
    test = [row for row in data if row["sursa"] == TEST]
    print(f"{len(data)} răspunsuri exportate în {args.out}: {len(real)} reale, {len(test)} date de test")
    texts = {q.id: q.text for q in QUESTIONS}
    for label, group in (("REALE", real), ("DATE DE TEST (generate, nu de la participanți)", test)):
        if group:
            print(f"Medii — {label}:")
            for qid, average in averages(group).items():
                print(f"  {qid} (medie {'–' if average is None else average}): {texts[qid]}")


if __name__ == "__main__":
    main()
