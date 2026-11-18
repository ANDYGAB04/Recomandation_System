
from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field, PlainSerializer, StringConstraints, field_validator

from .vocabulary import Activity, EventType, Intensity, Level, Season, Style


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


UtcDatetime = Annotated[
    datetime,
    AfterValidator(_as_utc),
    PlainSerializer(lambda v: _as_utc(v).isoformat(timespec="seconds").replace("+00:00", "Z"), return_type=str),
]

Email = Annotated[EmailStr, AfterValidator(str.lower)]




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




class ProfileIn(BaseModel):

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




class InteractionIn(BaseModel):
    event_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
    product_id: int
    type: EventType


class InteractionRecorded(BaseModel):
    event_id: str
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
    behavior_breakdown: dict[str, float]
    interests: list[InterestOut]
    top_products: list[ProfileProductOut]




class MetricsOut(BaseModel):
    precision_at_k: float | None
    recall_at_k: float | None


class EvaluationRow(MetricsOut):
    config: str
    strategy: str
    alpha: float | None
    event_weights: str | None
    coverage: float
    latency_ms: float | None
    users: int
    users_without_history: int
    without_history: MetricsOut


class EvaluationWindow(BaseModel):
    start: str
    end: str
    users_total: int
    users_evaluated: int
    users_without_relevant: int
    users_without_history: int
    results: list[EvaluationRow]


class EvaluationOut(BaseModel):
    k: int
    note: str
    selected_config: str
    validation: EvaluationWindow
    test: EvaluationWindow




class FeedbackIn(BaseModel):
    product_id: int
    useful: bool
    strategy: Literal["personalized", "popular"] = "personalized"


class FeedbackOut(BaseModel):
    product_id: int
    useful: bool
    strategy: str
    updated_at: UtcDatetime


class FeedbackCounts(BaseModel):
    votes: int
    useful: int
    useful_share: float | None


class FeedbackGroups(FeedbackCounts):
    users: int
    personalized: FeedbackCounts
    popular: FeedbackCounts


class FeedbackSummary(FeedbackGroups):

    test_data: FeedbackGroups




class SurveyQuestionOut(BaseModel):
    id: str
    text: str
    kind: str
    low: str
    high: str


class SurveyOut(BaseModel):
    questions: list[SurveyQuestionOut]
    answered: bool | None
    responses: int
    test_responses: int = 0


class SurveyAnswersIn(BaseModel):
    answers: dict[str, int | str | None]
