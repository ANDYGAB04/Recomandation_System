
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from ..models import Interaction
from ..vocabulary import EventType

SIMULATION_START = datetime(2026, 8, 1, tzinfo=UTC)
SIMULATION_DAYS = 90
SIMULATION_END = SIMULATION_START + timedelta(days=SIMULATION_DAYS)


def final_favorites(events: Iterable[Interaction]) -> dict[int, datetime]:
    favorites: dict[int, datetime] = {}
    for event in events:
        if event.type == EventType.FAVORITE:
            favorites.setdefault(event.product_id, event.created_at)
        elif event.type == EventType.UNFAVORITE:
            favorites.pop(event.product_id, None)
    return favorites
