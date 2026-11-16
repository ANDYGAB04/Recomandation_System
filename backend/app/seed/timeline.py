"""Perioada simulată și utilitare comune pentru datele de test."""

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from ..models import Interaction
from ..vocabulary import EventType

# Istoricul de test acoperă 90 de zile fixe, ca datele să fie aceleași la fiecare rulare.
SIMULATION_START = datetime(2026, 8, 1, tzinfo=UTC)
SIMULATION_DAYS = 90
SIMULATION_END = SIMULATION_START + timedelta(days=SIMULATION_DAYS)


def final_favorites(events: Iterable[Interaction]) -> dict[int, datetime]:
    """Favoritele rămase după evenimente (în ordine cronologică): produs → momentul adăugării."""
    favorites: dict[int, datetime] = {}
    for event in events:
        if event.type == EventType.FAVORITE:
            favorites.setdefault(event.product_id, event.created_at)
        elif event.type == EventType.UNFAVORITE:
            favorites.pop(event.product_id, None)
    return favorites
