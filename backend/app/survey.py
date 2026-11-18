
from dataclasses import dataclass

SCALE_MIN, SCALE_MAX = 1, 5
OPEN_MAX_LENGTH = 1000


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    kind: str  
    low: str = ""  
    high: str = ""  


QUESTIONS: tuple[Question, ...] = (
    Question("q1", "Cât de potrivite au fost recomandările cu setările pe care le-ai ales?", "scale", "Deloc potrivite", "Foarte potrivite"),
    Question("q2", "Cât de clare au fost explicațiile de sub recomandări („Pentru că ai ales…”)?", "scale", "Deloc clare", "Foarte clare"),
    Question("q3", "După ce ți-ai schimbat setările, cât de bine s-a adaptat lista de recomandări?", "scale", "Deloc", "Foarte bine"),
    Question("q4", "Dacă magazinul ar fi real, cât de probabil ar fi să cumperi un produs recomandat?", "scale", "Deloc probabil", "Foarte probabil"),
    Question("q5", "Cât de ușor ți-a fost să folosești aplicația (cont, setări, recomandări)?", "scale", "Foarte greu", "Foarte ușor"),
    Question("q6", "Ce ți-a plăcut, ce ți-a lipsit sau ce ai schimba?", "open"),
)

SCALE_IDS = tuple(q.id for q in QUESTIONS if q.kind == "scale")
OPEN_IDS = tuple(q.id for q in QUESTIONS if q.kind == "open")
