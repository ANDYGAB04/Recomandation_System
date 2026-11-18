
from enum import StrEnum


class Activity(StrEnum):
    HIKING = "hiking"
    CAMPING = "camping"
    RUNNING = "running"
    CYCLING = "cycling"


class Intensity(StrEnum):
    LOW = "low"
    HIGH = "high"


class Level(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Style(StrEnum):
    ULTRALIGHT = "ultralight"
    COMFORT = "comfort"
    DURABLE = "durable"
    PERFORMANCE = "performance"
    BUDGET = "budget"


class Season(StrEnum):
    SUMMER = "summer"
    WINTER = "winter"
    ALL_YEAR = "all_year"


class EventType(StrEnum):
    VIEW = "view"
    FAVORITE = "favorite"
    UNFAVORITE = "unfavorite"
    PURCHASE = "purchase"


LABELS: dict[type[StrEnum], dict[str, str]] = {
    Activity: {"hiking": "Drumeție", "camping": "Camping", "running": "Alergare", "cycling": "Ciclism"},
    Intensity: {"low": "Puțin", "high": "Mult"},
    Level: {"beginner": "Începător", "intermediate": "Intermediar", "advanced": "Avansat"},
    Style: {
        "ultralight": "Ultraușor",
        "comfort": "Confort",
        "durable": "Rezistență",
        "performance": "Performanță",
        "budget": "Buget redus",
    },
    Season: {"summer": "Vară", "winter": "Iarnă", "all_year": "Tot anul"},
    EventType: {
        "view": "Vizualizare",
        "favorite": "Adăugat la favorite",
        "unfavorite": "Scos din favorite",
        "purchase": "Cumpărare",
    },
}

VOCABULARY_KEYS: dict[str, type[StrEnum]] = {
    "activities": Activity,
    "intensities": Intensity,
    "levels": Level,
    "styles": Style,
    "seasons": Season,
    "event_types": EventType,
}


def options(enum: type[StrEnum]) -> list[dict[str, str]]:
    return [{"value": member.value, "label": LABELS[enum][member.value]} for member in enum]
