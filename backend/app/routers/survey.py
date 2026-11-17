from fastapi import APIRouter, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from ..dependencies import CurrentUserDep, OptionalUserDep, SessionDep
from ..models import SurveyParticipant, SurveyResponse
from ..schemas import SurveyAnswersIn, SurveyOut, SurveyQuestionOut
from ..survey import OPEN_IDS, OPEN_MAX_LENGTH, QUESTIONS, SCALE_IDS, SCALE_MAX, SCALE_MIN

router = APIRouter(prefix="/survey", tags=["chestionar"])

ALREADY_ANSWERED = "Ai completat deja chestionarul. Mulțumim!"


def _error(question_id: str, message: str) -> dict:
    return {"type": "value_error", "loc": ("body", "answers", question_id), "msg": message, "input": None}


def validate_answers(answers: dict) -> dict:
    """Răspunsurile curățate; RequestValidationError (422) cu câte o eroare pe întrebare."""
    errors = []
    known = {q.id for q in QUESTIONS}
    errors += [_error(key, "Întrebare necunoscută.") for key in answers if key not in known]

    clean: dict = {}
    for qid in SCALE_IDS:
        value = answers.get(qid)
        if value is None:
            errors.append(_error(qid, "Alege un răspuns."))
        elif isinstance(value, bool) or not isinstance(value, int) or not SCALE_MIN <= value <= SCALE_MAX:
            errors.append(_error(qid, f"Răspunsul trebuie să fie între {SCALE_MIN} și {SCALE_MAX}."))
        else:
            clean[qid] = value
    for qid in OPEN_IDS:
        value = answers.get(qid)
        if value is None or (isinstance(value, str) and not value.strip()):
            clean[qid] = ""
        elif not isinstance(value, str):
            errors.append(_error(qid, "Răspunsul trebuie să fie text."))
        elif len(value.strip()) > OPEN_MAX_LENGTH:
            errors.append(_error(qid, f"Maximum {OPEN_MAX_LENGTH} de caractere."))
        else:
            clean[qid] = value.strip()
    if errors:
        raise RequestValidationError(errors)
    return clean


def _count(session) -> int:
    return session.exec(select(func.count()).select_from(SurveyResponse)).one()


@router.get("")
def get_survey(session: SessionDep, user: OptionalUserDep) -> SurveyOut:
    """Întrebările chestionarului și dacă utilizatorul autentificat a răspuns deja."""
    answered = None if user is None else session.get(SurveyParticipant, user.id) is not None
    return SurveyOut(
        questions=[SurveyQuestionOut(id=q.id, text=q.text, kind=q.kind, low=q.low, high=q.high) for q in QUESTIONS],
        answered=answered,
        responses=_count(session),
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_survey(data: SurveyAnswersIn, user: CurrentUserDep, session: SessionDep) -> dict[str, bool]:
    """Salvează răspunsurile, anonim: contul se notează separat, doar ca să nu răspundă de două ori."""
    answers = validate_answers(data.answers)
    if session.get(SurveyParticipant, user.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=ALREADY_ANSWERED)
    session.add(SurveyParticipant(user_id=user.id))
    session.add(SurveyResponse(answers=answers))
    try:
        session.commit()
    except IntegrityError:  # două trimiteri simultane din același cont
        session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail=ALREADY_ANSWERED) from None
    return {"saved": True}
