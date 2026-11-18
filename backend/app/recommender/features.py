
from collections.abc import Iterable, Mapping
from typing import Protocol

from ..vocabulary import Intensity, Level, Season


class ProductLike(Protocol):
    id: int
    name: str
    category: str
    usages: list[str]
    levels: list[str]
    styles: list[str]
    seasons: list[str]
    tags: list[str]
    description: str
    price: float
    available: bool


class DeclaredProfileLike(Protocol):
    activities: Mapping[str, str]
    level: str | None
    styles: list[str]
    season: str | None
    max_budget: float | None


GROUP_WEIGHTS: dict[str, float] = {
    "category": 1.0,
    "usage": 1.0,
    "style": 0.8,
    "level": 0.6,
    "season": 0.6,
}

INTENSITY_WEIGHTS: dict[str, float] = {Intensity.HIGH: 1.0, Intensity.LOW: 0.5}

LEVEL_AFFINITY: dict[str, dict[str, float]] = {
    Level.BEGINNER: {Level.BEGINNER: 1.0, Level.INTERMEDIATE: 0.5},
    Level.INTERMEDIATE: {Level.BEGINNER: 0.5, Level.INTERMEDIATE: 1.0, Level.ADVANCED: 0.5},
    Level.ADVANCED: {Level.INTERMEDIATE: 0.5, Level.ADVANCED: 1.0},
}

SEASON_AFFINITY: dict[str, dict[str, float]] = {
    Season.SUMMER: {Season.SUMMER: 1.0, Season.ALL_YEAR: 0.5},
    Season.WINTER: {Season.WINTER: 1.0, Season.ALL_YEAR: 0.5},
    Season.ALL_YEAR: {Season.ALL_YEAR: 1.0, Season.SUMMER: 0.5, Season.WINTER: 0.5},
}


def feature(group: str, value: str) -> str:
    return f"{group}:{value}"


def split_feature(name: str) -> tuple[str, str]:
    group, _, value = name.partition(":")
    return group, value


def product_preference_features(product: ProductLike) -> dict[str, float]:
    features = {feature("category", product.category): 1.0}
    groups: Iterable[tuple[str, list[str]]] = (
        ("usage", product.usages),
        ("level", product.levels),
        ("style", product.styles),
        ("season", product.seasons),
    )
    for group, values in groups:
        features.update({feature(group, value): 1.0 for value in values})
    return features


def product_text(product: ProductLike) -> str:
    return " ".join([product.name, *product.tags, product.description])


def declared_choices(profile: DeclaredProfileLike) -> set[str]:
    choices = {feature(group, a) for a in profile.activities for group in ("category", "usage")}
    choices |= {feature("style", s) for s in profile.styles}
    if profile.level:
        choices.add(feature("level", profile.level))
    if profile.season:
        choices.add(feature("season", profile.season))
    return choices


def declared_profile_features(profile: DeclaredProfileLike) -> dict[str, float]:
    features: dict[str, float] = {}

    def add(group: str, value: str, weight: float) -> None:
        name = feature(group, value)
        features[name] = features.get(name, 0.0) + GROUP_WEIGHTS[group] * weight

    for activity, intensity in profile.activities.items():
        weight = INTENSITY_WEIGHTS.get(intensity, 0.0)
        add("category", activity, weight)
        add("usage", activity, weight)
    for style in profile.styles:
        add("style", style, 1.0)
    if profile.level:
        for level, weight in LEVEL_AFFINITY.get(profile.level, {}).items():
            add("level", level, weight)
    if profile.season:
        for season, weight in SEASON_AFFINITY.get(profile.season, {}).items():
            add("season", season, weight)
    return {name: weight for name, weight in features.items() if weight > 0}
