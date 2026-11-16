"""Formatul JSON al cererilor și răspunsurilor API (vezi docs/api.md)."""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, StringConstraints, field_validator

from .vocabulary import Activity, EventType, Intensity, Level, Season, Style


def _as_utc(value: datetime) -> datetime:
    # SQLite nu păstrează fusul orar; momentele salvate sunt mereu în UTC.
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


# Moment în UTC, scris ca "2026-11-15T14:30:00Z".
UtcDatetime = Annotated[
    datetime,
    AfterValidator(_as_utc),
    PlainSerializer(lambda v: _as_utc(v).isoformat(timespec="seconds").replace("+00:00", "Z"), return_type=str),
]

Email = Annotated[EmailStr, AfterValidator(str.lower)]


# ---------- Conturi ----------


class RegisterRequest(BaseModel):
    email: Email
    password: str = Field(min_length=8, max_length=256)
    display_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1, max_length=256)


class UserPublic(BaseModel):
    id: int
    email: str
    display_name: str


class UserMe(UserPublic):
    created_at: UtcDatetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


# ---------- Catalog ----------


class ProductOut(BaseModel):
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
    is_test_data: bool


class ProductPage(BaseModel):
    items: list[ProductOut]
    total: int
    limit: int
    offset: int


# ---------- Profil ----------


class ProfileIn(BaseModel):
    """Setările de profil. Un câmp lipsă înseamnă „necompletat”; valorile sunt cele din GET /vocabulary."""

    model_config = ConfigDict(extra="forbid")

    activities: dict[Activity, Intensity] = Field(default_factory=dict)
    level: Level | None = None
    styles: list[Style] = Field(default_factory=list)
    season: Season | None = None
    max_budget: float | None = Field(default=None, gt=0)

    @field_validator("styles")
    @classmethod
    def no_duplicate_styles(cls, styles: list[Style]) -> list[Style]:
        if len(set(styles)) != len(styles):
            raise ValueError("Stilurile nu se pot repeta.")
        return styles


class ProfileOut(BaseModel):
    activities: dict[str, str]
    level: str | None
    styles: list[str]
    season: str | None
    max_budget: float | None
    is_complete: bool
    updated_at: UtcDatetime


# ---------- Interacțiuni ----------


class InteractionIn(BaseModel):
    event_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    product_id: int
    type: EventType


class InteractionRecorded(BaseModel):
    event_id: str
    # false dacă evenimentul cu același event_id fusese deja salvat
    recorded: bool


class ProductRef(BaseModel):
    id: int
    name: str


class PurchaseOut(BaseModel):
    product: ProductOut
    purchased_at: UtcDatetime


class EventOut(BaseModel):
    event_id: str
    type: str
    product: ProductRef
    created_at: UtcDatetime


class HistoryOut(BaseModel):
    favorites: list[ProductOut]
    purchases: list[PurchaseOut]
    events: list[EventOut]


# ---------- Recomandări ----------


class MatchOut(BaseModel):
    group: str
    value: str
    label: str


class ExplanationOut(BaseModel):
    text: str
    matched: list[MatchOut]
    because_of: list[ProductRef]


class RecommendationOut(BaseModel):
    product: ProductOut
    score: float
    explanation: ExplanationOut


class RecommendationsOut(BaseModel):
    # "personalized" (din profil) sau "popular" (rezervă)
    strategy: str
    fallback_reason: str | None
    items: list[RecommendationOut]


class SimilarOut(BaseModel):
    items: list[RecommendationOut]


class ProfileSources(BaseModel):
    declared: float
    behavior: float


class InterestOut(MatchOut):
    weight: float


class ProfileProductOut(BaseModel):
    product: ProductRef
    weight: float
    events: list[str]


class RecommendationProfileOut(BaseModel):
    sources: ProfileSources
    # "purchase" / "favorite" / "view" → partea din profilul din comportament; {} fără istoric
    behavior_breakdown: dict[str, float]
    interests: list[InterestOut]
    top_products: list[ProfileProductOut]
