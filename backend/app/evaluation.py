
import time
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, select

from .models import Interaction, Product, User, UserProfile
from .recommender import ALPHA, EVENT_WEIGHTS, ContentRecommender, History, popular, recommend
from .seed.simulation import is_simulated_email
from .seed.timeline import SIMULATION_DAYS, SIMULATION_START
from .vocabulary import EventType

K = 5
VALIDATION_START_DAY = 60
TEST_START_DAY = 75
NOTE = "Date sintetice: rezultatele descriu comportamentul simulatorului, nu preferințe reale."

WEIGHT_PRESETS: dict[str, Mapping[str, float]] = {
    "curs 1/5/10": EVENT_WEIGHTS,
    "egale 1/1/1": {EventType.VIEW: 1.0, EventType.FAVORITE: 1.0, EventType.PURCHASE: 1.0},
}
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)


@dataclass(frozen=True)
class Config:
    name: str
    strategy: str  
    alpha: float = ALPHA
    weights: str = "curs 1/5/10"


POPULARITY = Config("popularitate", "popular")
APP_CONFIG = Config(f"profil: α = {ALPHA}, curs 1/5/10 (folosită de aplicație)", "personalized", ALPHA)
INITIAL_CONFIG = Config("profil: α = 0.5, curs 1/5/10 (ponderile inițiale)", "personalized", 0.5)


def _config_name(alpha: float, weights: str) -> str:
    if alpha == 1.0:
        return "profil: doar setări (α = 1)"
    if alpha == 0.0:
        return f"profil: doar comportament (α = 0, {weights})"
    return f"profil: α = {alpha}, {weights}"


GRID = [Config(_config_name(a, w), "personalized", a, w) for a in ALPHAS for w in WEIGHT_PRESETS if not (a == 1.0 and w != "curs 1/5/10")]


@dataclass
class Window:

    start: datetime
    end: datetime
    users_total: int = 0
    histories: dict[int, History] = field(default_factory=dict)
    relevant: dict[int, set[int]] = field(default_factory=dict)
    purchase_counts: dict[int, int] = field(default_factory=dict)


def _utc(moment: datetime) -> datetime:
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment


def build_window(
    products: Sequence, events: Sequence[tuple[int, int, str, datetime]], start: datetime, end: datetime
) -> Window:
    window = Window(start, end)
    past: dict[int, list[tuple[int, str]]] = defaultdict(list)
    future: dict[int, set[int]] = defaultdict(set)
    buyers: dict[int, set[int]] = defaultdict(set)
    users = set()
    for user_id, product_id, event_type, moment in events:
        users.add(user_id)
        if moment < start:
            past[user_id].append((product_id, event_type))
            if event_type == EventType.PURCHASE:
                buyers[product_id].add(user_id)
        elif moment < end and event_type == EventType.PURCHASE:
            future[user_id].add(product_id)

    available = {p.id for p in products if p.available}
    window.users_total = len(users)
    window.purchase_counts = {pid: len(u) for pid, u in buyers.items()}
    for user_id in sorted(users):
        history = History.from_events(past.get(user_id, []))
        relevant = (future.get(user_id, set()) & available) - history.purchased
        if relevant:
            window.histories[user_id] = history
            window.relevant[user_id] = relevant
    return window


def _summary(rows: list[tuple[int, int]], k: int) -> tuple[float | None, float | None]:
    if not rows:
        return None, None
    precision = sum(hits for hits, _ in rows) / (k * len(rows))
    recall = sum(hits / total for hits, total in rows) / len(rows)
    return round(precision, 4), round(recall, 4)


def evaluate_config(
    window: Window, rec: ContentRecommender, profiles: Mapping[int, UserProfile], config: Config, k: int = K
) -> dict:
    with_history, without_history, latencies = [], [], []
    recommended: set[int] = set()
    weights = WEIGHT_PRESETS[config.weights]
    for user_id, relevant in window.relevant.items():
        history = window.histories[user_id]
        started = time.perf_counter()
        if config.strategy == "popular":
            result = popular(rec, window.purchase_counts, k, history.purchased)
        else:
            result = recommend(rec, profiles.get(user_id), history, window.purchase_counts, k,
                               alpha=config.alpha, event_weights=weights, explain=False)
        latencies.append((time.perf_counter() - started) * 1000)
        ids = [item.product_id for item in result.items]
        recommended.update(ids)
        row = (len(set(ids) & relevant), len(relevant))
        (without_history if history.is_empty() else with_history).append(row)

    precision, recall = _summary(with_history, k)
    cold_precision, cold_recall = _summary(without_history, k)
    available = sum(1 for p in rec.products if p.available)
    return {
        "config": config.name,
        "strategy": config.strategy,
        "alpha": config.alpha if config.strategy == "personalized" else None,
        "event_weights": config.weights if config.strategy == "personalized" else None,
        "precision_at_k": precision,
        "recall_at_k": recall,
        "coverage": round(len(recommended) / available, 4) if available else 0.0,
        "latency_ms": round(sum(latencies) / len(latencies), 3) if latencies else None,
        "users": len(with_history),
        "users_without_history": len(without_history),
        "without_history": {"precision_at_k": cold_precision, "recall_at_k": cold_recall},
    }


def _window_info(window: Window, rows: list[dict]) -> dict:
    return {
        "start": window.start.isoformat().replace("+00:00", "Z"),
        "end": window.end.isoformat().replace("+00:00", "Z"),
        "users_total": window.users_total,
        "users_evaluated": len(window.relevant),
        "users_without_relevant": window.users_total - len(window.relevant),
        "users_without_history": sum(1 for h in window.histories.values() if h.is_empty()),
        "results": rows,
    }


def run(products: Sequence, profiles: Mapping[int, UserProfile], events: Sequence[tuple], k: int = K) -> dict:
    rec = ContentRecommender(products)
    day = lambda n: SIMULATION_START + timedelta(days=n)  
    validation = build_window(products, events, day(VALIDATION_START_DAY), day(TEST_START_DAY))
    test = build_window(products, events, day(TEST_START_DAY), day(SIMULATION_DAYS + 1))

    validation_rows = [evaluate_config(validation, rec, profiles, POPULARITY, k)]
    validation_rows += [evaluate_config(validation, rec, profiles, config, k) for config in GRID]
    scored = list(zip(GRID, validation_rows[1:]))
    best = max(scored, key=lambda pair: (pair[1]["recall_at_k"] or 0, pair[1]["precision_at_k"] or 0))[0]

    test_configs = [POPULARITY, APP_CONFIG]
    seen = {(APP_CONFIG.alpha, APP_CONFIG.weights)}
    if (best.alpha, best.weights) not in seen:
        test_configs.append(Config(f"{best.name} (aleasă pe validare)", "personalized", best.alpha, best.weights))
        seen.add((best.alpha, best.weights))
    if (INITIAL_CONFIG.alpha, INITIAL_CONFIG.weights) not in seen:
        test_configs.append(INITIAL_CONFIG)
    test_rows = [evaluate_config(test, rec, profiles, config, k) for config in test_configs]
    return {
        "k": k,
        "note": NOTE,
        "selected_config": best.name,
        "validation": _window_info(validation, validation_rows),
        "test": _window_info(test, test_rows),
    }


def load_and_run(session: Session, k: int = K) -> dict:
    products = list(session.exec(select(Product).order_by(Product.id)))
    simulated = {u.id for u in session.exec(select(User)) if is_simulated_email(u.email)}
    profiles = {p.user_id: p for p in session.exec(select(UserProfile)) if p.user_id in simulated}
    events = [
        (i.user_id, i.product_id, i.type, _utc(i.created_at))
        for i in session.exec(select(Interaction).order_by(Interaction.created_at, Interaction.id))
        if i.user_id in simulated
    ]
    if not products or not events:
        raise ValueError("Nu există date de evaluat. Rulează `python -m app.seed` în directorul backend/.")
    return run(products, profiles, events, k)


def _format(value: float | None, kind: str) -> str:
    if value is None:
        return "–".rjust(7)
    return f"{value:7.1%}" if kind == "percent" else f"{value:7.3f}"


def print_report(report: dict) -> None:
    for key, title in (("validation", "VALIDARE (alegerea ponderilor)"), ("test", "TEST (rezultatul final)")):
        part = report[key]
        print(f"\n{title}: {part['start'][:10]} → {part['end'][:10]}")
        print(f"  {part['users_evaluated']} clienți cu cumpărări în interval; {part['users_without_relevant']} fără "
              f"(excluși); {part['users_without_history']} fără istoric înainte (raportați separat)")
        print(f"  {'configurație':58} {'P@' + str(report['k']):>7} {'R@' + str(report['k']):>7} {'acop.':>7} {'ms':>7}")
        for row in part["results"]:
            print(f"  {row['config']:58} {_format(row['precision_at_k'], 'num')} {_format(row['recall_at_k'], 'num')}"
                  f" {_format(row['coverage'], 'percent')} {_format(row['latency_ms'], 'num')}")
    print(f"\nAleasă pe validare: {report['selected_config']}")
    print(report["note"])


def main() -> None:
    from .config import get_settings
    from .db import create_db_engine, init_db

    engine = create_db_engine(get_settings().database_file)
    init_db(engine)
    with Session(engine) as session:
        try:
            report = load_and_run(session)
        except ValueError as error:
            raise SystemExit(str(error)) from None
    engine.dispose()
    print_report(report)


if __name__ == "__main__":
    main()
