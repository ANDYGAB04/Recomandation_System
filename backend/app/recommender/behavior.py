
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Protocol

from ..vocabulary import EventType

EVENT_WEIGHTS: Mapping[str, float] = {EventType.VIEW: 1.0, EventType.FAVORITE: 5.0, EventType.PURCHASE: 10.0}
VIEW_CAP = 3


class InteractionLike(Protocol):
    product_id: int
    type: str


@dataclass
class History:
    views: Counter = field(default_factory=Counter)
    favorites: set[int] = field(default_factory=set)
    purchases: Counter = field(default_factory=Counter)

    @classmethod
    def from_events(cls, events: Iterable[tuple[int, str]]) -> "History":
        history = cls()
        for product_id, event_type in events:
            if event_type == EventType.VIEW:
                history.views[product_id] += 1
            elif event_type == EventType.FAVORITE:
                history.favorites.add(product_id)
            elif event_type == EventType.UNFAVORITE:
                history.favorites.discard(product_id)
            elif event_type == EventType.PURCHASE:
                history.purchases[product_id] += 1
        return history

    @classmethod
    def from_interactions(cls, interactions: Iterable[InteractionLike]) -> "History":
        return cls.from_events((i.product_id, i.type) for i in interactions)

    @property
    def purchased(self) -> set[int]:
        return set(self.purchases)

    def is_empty(self) -> bool:
        return not (self.views or self.favorites or self.purchases)

    def product_weights(
        self, event_weights: Mapping[str, float] = EVENT_WEIGHTS, view_cap: int = VIEW_CAP
    ) -> dict[int, float]:
        weights: Counter = Counter()
        for product_id, count in self.views.items():
            weights[product_id] += event_weights[EventType.VIEW] * min(count, view_cap)
        for product_id in self.favorites:
            weights[product_id] += event_weights[EventType.FAVORITE]
        for product_id, count in self.purchases.items():
            weights[product_id] += event_weights[EventType.PURCHASE] * count
        return {product_id: w for product_id, w in weights.items() if w > 0}

    def weights_by_event(
        self, event_weights: Mapping[str, float] = EVENT_WEIGHTS, view_cap: int = VIEW_CAP
    ) -> dict[str, float]:
        return {
            EventType.PURCHASE.value: event_weights[EventType.PURCHASE] * sum(self.purchases.values()),
            EventType.FAVORITE.value: event_weights[EventType.FAVORITE] * len(self.favorites),
            EventType.VIEW.value: event_weights[EventType.VIEW] * sum(min(n, view_cap) for n in self.views.values()),
        }

    def strongest_event(self, product_id: int) -> str | None:
        if product_id in self.purchases:
            return EventType.PURCHASE
        if product_id in self.favorites:
            return EventType.FAVORITE
        if product_id in self.views:
            return EventType.VIEW
        return None
